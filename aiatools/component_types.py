# -*- mode: python; coding: utf-8 -*-
# Copyright © 2017 Massachusetts Institute of Technology, All rights reserved.

"""
The :py:mod:`aiatools.component_types` module defines the components for App Inventor. Component types are
programmatically constructed during module compilation from the simple_components.json used to populate App Inventor's
online development environment.
"""

import json
import xml.etree.ElementTree as ETree

import pkg_resources

from aiatools.selectors import Selector, NamedCollection, Selectors
from .common import *

__author__ = 'Evan W. Patton <ewpatton@mit.edu>'


# noinspection PyShadowingBuiltins
class ComponentContainer(Component, Selectors):
    """
    :py:class:`ComponentContainer` models the App Inventor ComponentContainer class.

    Parameters:
        parent (ComponentContainer, optional): The parent of the container. May be None for :py:class:`.Screen`.
        uuid (basestring): The UUID for the component container.
        type (str): The type of the component container.
        name (basestring): The name of the component container.
        version (str): The version number of the component container's type at the time the project was last saved.
        properties (dict[basestring, T], optional): The properties of the component as a dictionary. The values are
                                                    dependent on the key (property).
        components (list[Component], optional): A list of components contained by the container.
    """
    def __init__(self, parent, uuid, type, name, version, properties=None, components=None):
        super(ComponentContainer, self).__init__(parent, uuid, type, name, version, properties)
        self._children = [] if components is None else list(components)

    def __iter__(self):
        """
        Iterate over the children of the container.

        :return: An iterator over the container's children.
        :rtype: collections.Iterable[Component]
        """
        return iter(self._children)

    def itervalues(self):
        """
        Iterate over the values of this container. For :py:class:`ComponentContainer`, the values are the children
        of the container.

        :return: Iterator over the container's children.
        :rtype: collections.Iterable[Component]
        """
        return iter(self)

    def children(self):
        """
        Iterate over the child components in the container

        :return: An iterator over the components in the container.
        :rtype: collections.Iterable[Component]

        .. versionadded:: 0.1
        """
        return self._children

    def _components(self, *args, **kwargs):
        items = {item.id: item for item in RecursiveIterator(self)}
        items[self.id] = self
        return Selector(NamedCollection(items)).components(*args, **kwargs)

    @classmethod
    def from_json(cls, parent, json_repr):
        """
        Constructs a :py:class:`ComponentContainer`

        :param parent: The parent container of the new container.
        :type parent: ComponentContainer
        :param json_repr: The JSON representation of the component from the Screen definition.
        :type json_repr: dict[str, T]
        :return: A newly constructed ComponentContainer from the JSON representation.
        :rtype: ComponentContainer
        """
        typename = json_repr['$Type']
        if typename in globals():
            type = globals()[typename]
        else:
            type = Extension(typename)
        properties = {k: v for k, v in json_repr.items() if k not in Component._DISALLOWED_KEYS}
        container = cls(parent, json_repr['Uuid'], type, json_repr['$Name'], json_repr['$Version'], properties)
        for component_description in json_repr['$Components']:
            if '$Components' in component_description:
                child = ComponentContainer.from_json(container, component_description)
            else:
                child = Component.from_json(container, component_description)
            container._children.append(child)
        return container

    components = property(_components, doc="""
    Returns a :py:class:`~aiatools.selectors.Selector` over the components in the container.
    
    :type: Selector[Component]
    """)


class DesignerRoot(ComponentContainer):
    """
    The :py:class:`Screen` class provides a Python representation of an App Inventor Screen.

    The Screen object encapsulates both its descendant components and the blocks code prescribing the behavior of the
    Screen's contents.

    Parameters
    ----------
    name : basestring, optional
        The name of the screen.
    components : list[Component], optional
        A list of immediate components that are the children of the screen.
    design : string | file, optional
        A pathname, string, or file-like that contains a Screen's Scheme (.scm) file.
    blocks : string | file, optional
        A pathname, string, or file-like that contains a Screen's Blocks (.bky) file.
    """
    def __init__(self, name=None, components=None, design=None, blocks=None, project=None, root_type=None):
        self.uuid = 0
        self.name = name
        self.path = name
        self._children = components
        self._blocks = NamedCollection()
        self.ya_version = None
        self.blocks_version = None
        self.project = project
        if design is not None:
            form_json = None
            if isinstance(design, str):
                form_json = json.loads(design)
            else:
                form_contents = [line.decode('utf-8') if hasattr(line, 'decode') else line for line in design.readlines()]
                if len(form_contents) > 2:
                    if form_contents[1] != '$JSON\n' and form_contents[1] != b'$JSON\n':
                        raise RuntimeError('Unknown Screen format: %s' % form_contents[1])
                    form_json = json.loads(form_contents[2])
                elif len(form_contents) == 1:  # Alexa support
                    form_json = json.loads(form_contents[0])

            self.name = name or (form_json is not None and form_json['Properties']['$Name'])
            super(DesignerRoot, self).__init__(parent=None,
                                               uuid=('0' if form_json is None else form_json['Properties']['Uuid']),
                                               type=root_type,
                                               name=self.name,
                                               version=(None if form_json is None else form_json['Properties']['$Version']),
                                               components=components)
            if form_json:
                self._process_components_json(form_json['Properties']['$Components']
                                              if '$Components' in form_json['Properties'] else [])
                self.properties = {
                    key: value for key, value in form_json.items() if key not in Component._DISALLOWED_KEYS
                }
                self.ya_version = int(form_json['AlexaVersion'] if 'AlexaVersion' in form_json else form_json['YaVersion'])
            else:
                self.properties = {}
                self.ya_version = None
        else:
            super(DesignerRoot, self).__init__(None, '0', root_type, name or 'Screen1', '20', components=components)
        self.id = self.name
        if isinstance(blocks, str):
            blocks_content = blocks
        else:
            blocks_content = None if blocks is None else blocks.read()
        blocks_content = blocks_content if blocks_content and len(blocks_content) > 0 else None
        xml_root = None if blocks_content is None else ETree.fromstring(blocks_content)
        if xml_root is not None:
            for child in xml_root:
                if child.tag.endswith('yacodeblocks'):
                    self.blocks_version = int(child.attrib['language-version'])
                    self.ya_version = max(self.ya_version, int(child.attrib['ya-version']))
                else:
                    block = Block.from_xml(self, child, self.blocks_version)
                    self._blocks[block.id] = block
        self.blocks = Selector(self._blocks)

    def _process_components_json(self, components):
        self._children = []
        for component_description in components:
            if '$Components' in component_description:  # component container
                component = ComponentContainer.from_json(self, component_description)
            else:
                component = Component.from_json(self, component_description)
            self._children.append(component)

    def __iter__(self):
        for child in RecursiveIterator(self):
            yield child
        for child in self._blocks.values():
            yield child

    def __str__(self):
        return self.name


class Screen(DesignerRoot):
    def __init__(self, name=None, components=None, design=None, blocks=None, project=None):
        super(Screen, self).__init__(name, components, design, blocks, project, Form)

    def __repr__(self):
        return "Screen(%s)" % repr(self.name)


class Skill(DesignerRoot):
    def __init__(self, name=None, components=None, design=None, blocks=None, project=None):
        super(Skill, self).__init__(name, components, design, blocks, project, Alexa)

    def __repr__(self):
        return "Skill(%s)" % repr(self.name)


def list_to_dict(iterable, key='name'):
    return {i[key]: i for i in iterable}


container_types = {
    'Canvas',
    'Chart',
    'FeatureCollection',
    'Form',
    'Map',
    'HorizontalArrangement',
    'HorizontalScrollArrangement',
    'TableArrangement'
    'VerticalArrangement',
    'VerticalScrollArrangement'
}


def component_from_descriptor(descriptor: dict) -> ComponentType:
    methods = list_to_dict(descriptor['methods'])
    events = list_to_dict(descriptor['events'])
    properties = list_to_dict(descriptor['properties'])
    for prop in descriptor['blockProperties']:
        if prop['name'] in properties:
            properties[prop['name']].update(prop)
        else:
            properties[prop['name']] = prop
            prop['editorType'] = None
            prop['defaultValue'] = None
    external = descriptor['external'] == 'true'
    cls = Extension if external else ComponentType
    component = cls(descriptor['name'], methods, events, properties)
    component.type = descriptor['type']
    component.external = external
    component.version = int(descriptor['version'])
    component.category_string = descriptor['categoryString']
    component.help_string = descriptor['helpString']
    component.show_on_palette = bool(descriptor['showOnPalette'])
    component.visible = not bool(descriptor['nonVisible'])
    component.icon_name = descriptor['iconName']
    return component


def _load_component_types(filename, use_type=False):
    """
    Loads the descriptions of App Inventor components from simple_components.json and populates the module with
    instances of ComponentType for each known type.
    """
    with open(pkg_resources.resource_filename('aiatools', filename)) as _f:
        _component_descriptors = json.load(_f)
        for _descriptor in _component_descriptors:
            _component = component_from_descriptor(_descriptor)
            name = _component.type if use_type else _component.name
            globals()[name] = _component
            Component.TYPES[name] = _component


_load_component_types('simple_components.json')
_load_component_types('alexa-devices.json', use_type=True)
