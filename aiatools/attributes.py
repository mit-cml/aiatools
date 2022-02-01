# -*- mode: python; coding: utf-8; -*-
# Copyright © 2017 Massachusetts Institute of Technology, All rights reserved.

"""
The :py:mod:`aiatools.attributes` module provides :py:class:`~aiatools.algebra.Functor` for querying App Inventor
projects.

.. testsetup::

    from aiatools.aia import AIAFile
    from aiatools.attributes import *
    from aiatools.block_types import *
    from aiatools.component_types import *
    project = AIAFile('test_aias/LondonCholeraMap.aia')
"""

from aiatools.algebra import ComputedAttribute
from .algebra import Functor, NotExpression
from .common import Block, BlockKind
from .selectors import select
try:
    from collections.abc import Callable
except ImportError:
    from collections import Callable


__author__ = 'Evan W. Patton <ewpatton@mit.edu>'


class NamedAttribute(Functor):
    """
    The :py:class:`NamedAttribute` is a :py:class:`Functor` that retrieves the value of a specific field on entities in
    an App Inventor project.

    Example
    _______
    Retrieve any Form entities in the project:

        >>> project.components(NamedAttribute('type') == Form)
        [Screen('Screen1')]

    Parameters
    __________
    name : basestring
        The name of the attribute to be retrieved.
    """

    # noinspection PyShadowingNames
    def __init__(self, name):
        self.name = name

    def __call__(self, obj, *args, **kwargs):
        if hasattr(obj, self.name):
            return getattr(obj, self.name)
        return None

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        if isinstance(other, NamedAttribute):
            return self.name == other.name
        else:
            return super(NamedAttribute, self).__eq__(other)

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, repr(self.name))


class NamedAttributeTuple(Functor):
    """
    The :py:class:`NamedAttributeTuple` is a :py:class:`Functor` that retrieves the value of a field on entities in an
    App Inventor project. Unlike :py:class:`NamedAttribute`, it can take more than one name as a tuple. The given field
    names are searched in order until one is found. This is useful for presenting a single :py:class:`Functor` over
    synonyms, for example, ``'name'`` gives the name of a :py:class:`Component` whereas ``'component_name'`` gives the
    name of a block's component (if any).

    Parameters
    ----------
    names : (str, unicode)
        The name(s) of the attribute(s) to be retrieved. Giving a 1-tuple is less efficient than defining and using the
        equivalent :py:class:`NamedAttribute` instance.
    """
    def __init__(self, names):
        super(NamedAttributeTuple, self).__init__()
        self.names = names

    def __call__(self, obj, *args, **kwargs):
        for _name in self.names:
            if hasattr(obj, _name):
                return getattr(obj, _name)
        return None

    def __hash__(self):
        return hash(self.names)

    def __eq__(self, other):
        if isinstance(other, NamedAttributeTuple):
            return self.names == other.names
        else:
            return super(NamedAttributeTuple, self).__eq__(other)

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.names)


def has_ancestor(target=None):
    """
    Constructs a new ComputedAttribute that accepts an entity if and only if the entity has an ancestor that matches the
    given ``target`` clause.

    Example
    -------
    Count the number of :py:data:`~.block_type.text` blocks with an ancestor that is a
    :py:data:`~.block_type.logic_compare` block.

        >>> project.blocks((type == text) & has_ancestor(type == logic_compare)).count()
        1

    Parameters
    ----------
    target : Expression
        An :py:class:`Expression` to use for testing ancestors.

    Returns
    -------
    ComputedAttribute
        A new ComputedAttribute that will walk the entity graph using the ``parent`` field and test whether any
        ``parent`` matches ``target``.
    """
    def checkAncestor(b):
        if b is None:
            return False
        b = b.parent  # Skip b
        while b is not None:
            if target is None:
                return True
            elif isinstance(target, Callable) and target(b):
                return True
            elif b is target:
                return True
            b = b.parent
        return False
    return ComputedAttribute(checkAncestor)


def has_descendant(target=None):
    """
    Constructs a new ComputedAttribute that accepts an entity if and only if the entity has a descendant that matches
    the given ``target`` clause.

    Example
    -------
    Count the number of top-level blocks that have control_if blocks as descendants.

        >>> project.blocks(top_level & has_descendant(type == controls_if)).count()
        1

    Parameters
    ----------
    target : Expression
        An :py:class:`Expression` to use for testing descendants.

    Returns
    -------
    ComputedAttribute
        A new ComputedAttribute that will walk the entity graph using the ``children`` field and test whether any
        descendant in the subgraph matches ``target``.
    """
    def checkDescendant(b):
        if b is None:
            return False
        if not hasattr(b, 'children'):
            return False
        for child in b.children():
            if target is None:
                return True
            elif isinstance(target, Callable) and target(child):
                return True
            elif child is target:
                return True
            elif checkDescendant(child):
                return True
        return False
    return ComputedAttribute(checkDescendant)


def _root_block(block):
    """
    Looks up the root of the stack of blocks containing the given ``block``.

    Example
    -------

    Parameters
    ----------
    block : Block
        The block of interest for which the root block will be obtained.

    Returns
    -------
    Block
        The block at the root of the block stack containing ``block``.
    """
    if not block:
        return block
    while block.logical_parent:
        block = block.logical_parent
    return block


root_block = ComputedAttribute(_root_block)


class HeightAttribute(Functor):
    """
    :py:class:`HeightAttribute` class is used to memoize the heights of the forest representing an App Inventor
    project. Use :py:data:`aiatools.attributes.height` to benefit from the memoization feature.

    Example
    -------
    Get the heights of the block stacks in the project.

        >>> project.blocks(top_level).map(height)
        [2, 6]
    """
    def __init__(self):
        self.precomputed = {}

    # noinspection PyShadowingNames
    def __call__(self, *args, **kwargs):
        block_or_component = args[0]
        if block_or_component in self.precomputed:
            return self.precomputed[block_or_component]
        else:
            try:
                height = max(self(x) for x in block_or_component.children()) + 1
            except ValueError:
                height = 0
            self.precomputed[block_or_component] = height
            return height


class DepthAttribute(Functor):
    """
    :py:class:`DepthAttribute` class is used to memoize the depths of entities in the forest representing an App
    Inventor project. Use :py:data:`aiatools.attributes.depth` to benefit from the memoization feature.

    Example
    -------
    Get the depth of all leaves in the project.

        >>> project.blocks(leaf).map(depth)
        [2, 2, 4, 4, 4, 6, 5, 5, 5, 5, 5]
    """
    def __init__(self):
        self.precomputed = {}

    @staticmethod
    def _get_parent(block_or_component):
        if hasattr(block_or_component, 'logical_parent'):
            return block_or_component.logical_parent
        else:
            return block_or_component.parent

    # noinspection PyShadowingNames
    def __call__(self, *args, **kwargs):
        block_or_component = DepthAttribute._get_parent(args[0])
        depth = 0
        while block_or_component is not None:
            depth += 1
            block_or_component = DepthAttribute._get_parent(block_or_component)
        return depth


class _MutationHelper(Functor):
    """
    :py:class:`_MutatorHelper` is a helper class used for generating new :py:class:`Functor` for retrieving mutation
    fields on a block. :py:class:`_MutationHelper` interns the instances so that the returned items are the same
    instance, that is:

        >>> mutation.component_type is mutation.component_type
        True

    :py:class:`_MutationHelper` is accessed through the :py:data:`mutation` instance.
    """
    _interned = {}

    def __init__(self, child=None):
        self.child = child

    def __call__(self, *args, **kwargs):
        if hasattr(args[0], 'mutation'):
            _mutation = args[0].mutation
            if _mutation is not None:
                if self.child is None:
                    return _mutation
                elif self.child in _mutation:
                    return _mutation[self.child]
        return None

    def __getattr__(self, item):
        if item not in _MutationHelper._interned:
            _MutationHelper._interned[item] = _MutationHelper(item)
        return _MutationHelper._interned[item]

    def __repr__(self):
        return


class _FieldHelper(Functor):
    """
    :py:class:`_FieldHelper` is a helper class used for generating new :py:class:`Functor` for retrieving fields of
    blocks. :py:class:`_FieldHelper` interns the instances so that the returned items are the same instace, that is:

        >>> fields.OP is fields.OP
        True

    :py:class:`_FieldHelper` is accessed through the :py:data:`field` instance.
    """
    _interned = {}

    def __init__(self, child=None):
        self.child = child

    def __call__(self, *args, **kwargs):
        if hasattr(args[0], 'fields'):
            _fields = args[0].fields
            if _fields is not None:
                if self.child is None:
                    return _fields
                elif self.child in _fields:
                    return _fields[self.child]
        return None

    def __getattr__(self, item):
        if item not in _FieldHelper._interned:
            _FieldHelper._interned[item] = _FieldHelper(item)
        return _FieldHelper._interned[item]


type = NamedAttributeTuple(('type', 'component_type'))
"""Returns the type of the entity."""

name = NamedAttributeTuple(('name', 'instance_name'))
"""Returns the name of the entity."""


def _kind(block):
    try:
        return block.kind
    except AttributeError:
        return None


kind = NamedAttribute("kind")
"""Returns the kind of the entity."""

external = NamedAttribute('external')
"""Returns true if the component is an extension."""

version = NamedAttribute('version')
"""Returns the version number for the entity."""

category = NamedAttributeTuple(('category', 'category_string'))
"""Returns the category for the entity."""

help_string = NamedAttribute('help_string')
"""Returns the help string for the entity."""

show_on_palette = NamedAttribute('show_on_palette')
"""Returns true if the entity is shown in the palette."""

visible = NamedAttribute('visible')
"""Returns true if the entity is visible."""

non_visible = NotExpression(visible)
"""Returns true if the entity is nonvisible."""

icon_name = NamedAttribute('iconName')
"""Returns the icon for the component."""

return_type = NamedAttribute('return_type')
"""Gets the return type of the block."""

generic = NamedAttribute('generic')
"""Tests whether the block is a generic component block."""

disabled = NamedAttribute('disabled')
"""Tests whether the entity is disabled."""

logically_disabled = NamedAttribute('logically_disabled')
"""Tests whether the block is logically disabled, either because it is explicitly disabled or is contained within a
disabled subtree."""

logically_enabled = ~logically_disabled
"""Tests whether the block is logically enabled."""

enabled = NamedAttribute('Enabled') | ~disabled
"""Tests whether the entity is enabled."""

top_level = ComputedAttribute(lambda b: isinstance(b, Block) and b.parent is None)
"""Tests whether the block is at the top level."""

parent = NamedAttribute('parent')
"""Gets the parent of the entity."""

mutation = _MutationHelper()
"""
Tests whether a block has a mutation specified. One can also use :py:data:`mutation` to obtain accessors for specific
mutation fields, for example:

.. doctest::

    >>> project.blocks(mutation.component_type == Button)
    [...]

will retrieve all blocks that have a mutation where the component_type key is the Button type.
"""

fields = _FieldHelper()
"""
:py:data:`fields` is a generator for :py:class:`Functor` to retrieve the values of fields in a block. For example:

.. doctest::

    >>> project.blocks(logic_compare).map(fields.OP)
    ['EQ']
"""

depth = DepthAttribute()
"""
Computes the depth of the entity with its tree. For components, this will be the number of containers from the Screen.
For blocks, this will be the number of logical ancestors to the top-most block of the block stack.

.. doctest::

    >>> project.components(type == Marker).avg(depth)
    2.0
"""

height = HeightAttribute()
"""
Computes the height of the tree from the given entity. This will be the longest path from the node to one of its
children. For leaf nodes, the height is 0.

.. doctest::

    >>> project.blocks(top_level).avg(height)
    4.0
"""

is_procedure = (type == 'procedures_defreturn') | (type == 'procedures_defnoreturn')
"""
Returns True if the type of a block is a procedure definition block, either :py:data:`procedures_defreturn` or
:py:data:`procedures_defnoreturn`

.. doctest::

    >>> with AIAFile('test_aias/ProcedureTest.aia') as proc_project:
    ...    proc_project.blocks(is_procedure).count()
    7
"""

is_called = ComputedAttribute(lambda x: not select(x).callers().empty())
"""
Returns True if the entity in question is called by some other block in the code.

.. todo::

    Add a mechanism for describing the call graph internal to components so that, for example,
    ``project.blocks(mutation.event_name == 'GotText').callers()`` should be non-empty for any ``Get`` method call
    blocks in the screen for the same ``instance_name``.
"""

leaf = ComputedAttribute(lambda x: len(x.children()) == 0)
"""
Returns True if the entity is a leaf in the tree (i.e., it has no children).

.. doctest::

    >>> project.blocks(leaf).count(group_by=type)
    {'text': 3, 'lexical_variable_get': 6, 'color_blue': 2}
"""

declaration = (type == 'component_event') | (type == 'global_declaration') | is_procedure
"""
"""

statement = kind == BlockKind.STATEMENT
"""
"""

value = kind == BlockKind.VALUE

"""
.. testcleanup::

    project.close()
"""
