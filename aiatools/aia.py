# -*- mode: python; coding: utf-8; -*-
# Copyright © 2017 Massachusetts Institute of Technology, All rights reserved.

"""

.. testsetup ::

    from aiatools.aia import AIAFile

The :py:mod:`aiatools.aia` package provides the :py:class:`AIAFile` class for reading App Inventor (.aia) projects.
"""

import logging
import os
from io import StringIO
from os.path import isdir, join
from zipfile import ZipFile

import jprops

from .component_types import Screen
from .selectors import Selector, NamedCollection, UnionSelector

__author__ = 'Evan W. Patton <ewpatton@mit.edu>'

log = logging.getLogger(__name__)


class AIAAsset(object):
    """
    :py:class:`AIAAsset` provides an interface for reading the contents of assets from an App Inventor project.
    """

    def __init__(self, zipfile, name):
        """
        Constructs a new reference to an asset within an AIA file.

        :param zipfile: The zipped project file that is the source of the asset.
        :param name: The path of the asset within the project file hierarchy.
        """
        self.zipfile = zipfile
        self.name = name

    def open(self, mode='r'):
        """
        Opens the asset. ``mode`` is an optional file access mode.

        :param mode: The access mode to use when accessing the asset. Must be one of 'r', 'rU', or 'U'.
        :type mode: basestring
        :return: A file-like for accessing the contents of the asset.
        :rtype: zipfile.ZipExtFile
        """
        return self.zipfile.open(self.name, mode)


class AIAFile(object):
    """
    :py:class:`AIAFile` encapsulates an App Inventor project (AIA) file.

    Opens an App Inventor project (AIA) with the given filename. ``filename`` can be any file-like object that is
    acceptable to :py:class:`ZipFile`'s constructor, or a path to a directory containing an unzipped project.

    Parameters
    ----------
    filename : basestring | file
        A string or file-like containing the contents of an App Inventor project.
    strict : bool, optional
        Process the AIAFile in strict mode, i.e., if a blocks file is missing then it is an error. Default: false
    """

    def __init__(self, filename, strict=False):
        if filename is None:
            self.zipfile = None
        elif not isinstance(filename, str) or (not isdir(filename) and filename[-4:] == '.aia'):
            self.zipfile = ZipFile(filename)
        else:
            self.zipfile = None

        self.assets = []
        """
        A list of assets contained in the project.

        :type: list[aiatools.aia.AIAAsset]
        """

        self.filename = filename
        """
        The filename or file-like that is the source of the project.

        :type: basestring or file
        """

        self.properties = {}
        """
        The contents of the project.properties file.

        :type: Properties
        """

        self._screens = NamedCollection()
        self.screens = Selector(self._screens)
        """
        A :py:class:`~aiatools.selectors.Selector` over the components of type
        :py:class:`~aiatools.component_types.Screen` in the project.

        For example, if you want to know how many screens are in a project run:

        .. doctest::

            >>> with AIAFile('test_aias/LondonCholeraMap.aia') as aia:
            ...     len(aia.screens)
            1

        :type: aiatools.selectors.Selector[aiatools.component_types.Screen]
        """

        self.components = UnionSelector(self._screens, 'components')
        """
        A :py:class:`~aiatools.selectors.Selector` over the component instances of all screens defined in the project.

        For example, if you want to know how many component instances are in a project run:

        .. doctest::

            >>> with AIAFile('test_aias/LondonCholeraMap.aia') as aia:
            ...     len(aia.components())  # Form, Map, Marker, Button
            4

        :type: aiatools.selectors.Selector[aiatools.common.Component]
        """

        self.blocks = UnionSelector(self._screens, 'blocks')
        """
        A :py:class:`~aiatoools.selectors.Selector` over the blocks of all screen defined in the project.

        For example, if you want to know how many blocks are in a project run:

        .. doctest::

            >>> with AIAFile('test_aias/LondonCholeraMap.aia') as aia:
            ...     len(aia.blocks())
            23

        :type: aiatools.selectors.Selector[aiatools.common.Block]
        """

        if self.zipfile:
            self._process_zip(strict)
        elif filename is not None:
            self._process_dir(strict)

    def close(self):
        if self.zipfile:
            self.zipfile.close()
        self.zipfile = None

    def __enter__(self):
        if self.zipfile:
            self.zipfile.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.zipfile:
            self.zipfile.__exit__(exc_type, exc_val, exc_tb)

    def _listfiles(self):
        names = []
        for dirname, dirs, files in os.walk(self.filename):
            names.extend([join(dirname, f) for f in files])

        return names

    def _process_zip(self, strict):
        """
        Processes the contents of an AIA file into Python objects for further operation.
        """
        self.assets = []
        for name in self.zipfile.namelist():
            if name.startswith('assets/'):
                self.assets.append(AIAAsset(self, name))
                # TODO(ewpatton): Need to load extension JSON to extend language model
            elif name.startswith('src/'):
                if name.endswith('.scm'):
                    name = name[:-4]
                    form = self.zipfile.open('%s.scm' % name, 'r')
                    try:
                        blocks = self.zipfile.open('%s.bky' % name, 'r')
                    except KeyError as e:
                        if strict:
                            raise e
                        else:
                            blocks = None  # older aia without a bky file
                    screen = Screen(form=form, blocks=blocks)
                    self._screens[screen.name] = screen
            elif name.endswith('project.properties'):
                with self.zipfile.open(name) as prop_file:
                    self.properties = jprops.load_properties(prop_file)
            else:
                log.warning('Ignoring file in AIA: %s' % name)

    def _process_dir(self, strict):
        """
        Processes the contents of a directory as if it were an AIA file and converts the content into Python objects
        for further operation.
        """
        self.assets = []
        asset_path = join(self.filename, 'assets')
        src_path = join(self.filename, 'src')
        for name in self._listfiles():
            if name.startswith(asset_path):
                self.assets.append(AIAAsset(None, name))
                # TODO(ewpatton): Need to load extension JSON to extend language model
            elif name.startswith(src_path) or name.endswith('.scm') or name.endswith('.bky'):
                if name.endswith('.scm'):
                    name = name[:-4]
                    if strict and not os.path.exists('%s.bky' % name):
                        raise IOError('Did not find expected blocks file %s.bky' % name)
                    bky_handle = open('%s.bky' % name) if os.path.exists('%s.bky' % name) else StringIO('<xml/>')
                    with open('%s.scm' % name, 'r') as form, bky_handle as blocks:
                        screen = Screen(form=form, blocks=blocks)
                        self._screens[screen.name] = screen
            elif name.endswith('project.properties'):
                with open(name, 'r') as prop_file:
                    self.properties = jprops.load_properties(prop_file)
            else:
                log.warning('Ignoring file in directory: %s' % name)

