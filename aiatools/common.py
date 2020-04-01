# -*- mode: python; coding: utf-8; -*-
# Copyright © 2017 Massachusetts Institute of Technology, All rights reserved.

"""
.. testsetup::

    from aiatools import *
    project = AIAFile('test_aias/LondonCholeraMap.aia')

The :py:mod:`aiatools.common` module defines the core data model that is used throughout the aiatools project. In most
cases, users will not construct these objects directly but rather through use of the :py:class:`~aiatools.aia.AIAFile`
class.
"""

from .algebra import Atom
from functools import reduce
from enum import Enum


__author__ = 'Evan W. Patton <ewpatton@mit.edu>'


def _html(tag):
    """
    Prefixes the given ``tag`` with the XHTML prefix. Block files saved with newer versions of App Inventor will have
    this XML namespace prepended when read with the ETree framework.
    :param tag: An XML element tag
    :type tag: basestring
    :return: A new string prefixed with the XHTML prefix.
    :rtype: str or unicode
    """
    return '{http://www.w3.org/1999/xhtml}' + tag


# noinspection PyShadowingBuiltins
class Block(object):
    _CATEGORIES = {'color', 'component', 'controls', 'global', 'lexical', 'lists', 'local', 'logic', 'math',
                   'obfuscated', 'dictionaries', 'procedures', 'text'}
    _CATEGORY_MAP = {
        'color': 'Colors',
        'component': 'Components',
        'controls': 'Controls',
        'global': 'Variables',
        'lexical': 'Variables',
        'lists': 'Lists',
        'local': 'Variables',
        'logic': 'Logic',
        'math': 'Math',
        'obfuscated': 'Text',
        'obsfucated': 'Text',
        'dictionaries': 'Dictionaries',
        'procedures': 'Procedures',
        'text': 'Text'
    }
    _ID_COUNT = 0

    def __init__(self, id, type):
        self.id = id
        self.type = type
        parts = type.split('_')
        if parts[0] == 'text':
            self.category = 'Text'
        else:
            self.category = Block._CATEGORY_MAP[parts[0]]
        self.parent = None
        self.logical_parent = None
        self.output = None
        self.inputs = {}
        self.ordered_inputs = []
        self.fields = {}
        self.statements = {}
        self.values = {}
        self.next = None
        self.mutation = None
        self.x = None
        self.y = None
        self.inline = False
        self.comment = None
        self.disabled = False
        self.logically_disabled = False
        self.screen = None

    @classmethod
    def from_xml(cls, screen, xml, lang_ver, siblings=None, parent=None, connection_type=None):
        siblings = siblings if siblings is not None else []
        attributes = xml.attrib
        type = attributes['type']
        id = attributes['id'] if 'id' in attributes else None
        if id is None:
            id = Block._ID_COUNT
            Block._ID_COUNT += 1
        type_parts = type.split('_')
        if type_parts[0] not in Block._CATEGORIES and lang_ver < 17:
            # likely old-format blocks code with component names in block types
            if type_parts[0] in screen.components:
                if type_parts[1] == 'setproperty':
                    # Old-style property setter
                    type = 'component_set_get'
                elif type_parts[1] == 'getproperty':
                    # Old-style property getter
                    type = 'component_set_get'
                elif len(xml) >= 2 and xml[1].tag == 'statement' and 'name' in xml[1].attrib and \
                        xml[1].attrib['name'] == 'DO':
                    # Old-style event handler
                    type = 'component_event'
                else:
                    # Old-style method call
                    type = 'component_method'
            else:
                raise RuntimeError('Unknown block type: %s' % type_parts[0])
        block = Block(id, type)
        screen._blocks[id] = block
        block.screen = screen
        block.parent = parent
        block.logical_parent = parent
        siblings.append(block)
        if 'x' in attributes and 'y' in attributes:  # Top level block
            block.x, block.y = attributes['x'], attributes['y']
        if 'inline' in attributes:
            block.inline = attributes['inline'] == 'true'
        if 'disabled' in attributes and attributes['disabled'] == 'true':
            block.disabled = True
            block.logically_disabled = True
        if connection_type == 'value' or connection_type == 'statement':
            block.logically_disabled = block.disabled or parent.logically_disabled
        for child in xml:
            if child.tag == 'mutation' or child.tag == _html('mutation'):
                block.mutation = dict(child.attrib)
                if type.startswith('component_') and ('is_generic' not in block.mutation or
                                                      block.mutation['is_generic'] == 'false'):
                    block.component = screen.components[block.mutation['instance_name']]
            elif child.tag == 'comment' or child.tag == _html('comment'):
                block.comment = child.text
            elif child.tag in {'field', 'title', _html('field'), _html('title')}:
                block.fields[child.attrib['name']] = child.text
            elif child.tag == 'value' or child.tag == _html('value'):
                block.inputs[child.attrib['name']] = block.values[child.attrib['name']] = []
                child_block = Block.from_xml(screen, child[0], lang_ver, block.values[child.attrib['name']],
                                             parent=block, connection_type='value')
                child_block.output = block
                block.ordered_inputs.append(child_block)
            elif child.tag == 'statement' or child.tag == _html('statement'):
                block.inputs[child.attrib['name']] = block.statements[child.attrib['name']] = []
                child_block = Block.from_xml(screen, child[0], lang_ver, block.statements[child.attrib['name']],
                                             parent=block, connection_type='statement')
                block.ordered_inputs.append(child_block)
                for child_block in block.statements[child.attrib['name']]:
                    child_block.logical_parent = block
            elif child.tag == 'next' or child.tag == _html('next'):
                child_block = Block.from_xml(screen, child[0], lang_ver, siblings=siblings, parent=block,
                                             connection_type='next')
                block.next = child_block
        return block

    @property
    def return_type(self):
        if self.type == 'component_method':
            from aiatools import component_types
            type = getattr(component_types, self.mutation['component_type'])
            assert(isinstance(type, ComponentType))
            return type.methods[self.mutation['method_name']].return_type
        return None

    @property
    def kind(self):
        from aiatools import block_types
        type = getattr(block_types, self.type)
        if type.kind == BlockKind.MUTATION:
            if self.type == 'component_set_get':
                return BlockKind.VALUE if self.mutation['set_or_get'] == 'get' else BlockKind.STATEMENT
            elif self.type == 'component_method':
                return BlockKind.VALUE if self.return_type is not None else BlockKind.STATEMENT
            else:
                raise ValueError('Unknown type ' + self.type)
        else:
            return type.kind

    def children(self):
        return reduce(list.__add__, iter(self.values.values()), []) + \
               reduce(list.__add__, iter(self.statements.values()), [])

    def __repr__(self):
        return '%s(%r, %r)' % (self.__class__.__name__, self.id, self.type)

    def __str__(self):
        description = {
            'id': self.id,
            'type': self.type,
            'disabled': self.disabled
        }
        if self.x is not None:
            description['x'] = self.x
            description['y'] = self.y
        if self.comment is not None:
            description['comment'] = self.comment
        if self.mutation is not None:
            description['mutation'] = self.mutation
        if len(self.fields) > 0:
            description['fields'] = self.fields
        if len(self.values) > 0:
            description['values'] = self.values
        if len(self.statements) > 0:
            description['statements'] = self.statements
        return str(description)

    def _get_is_generic(self):
        return self.mutation and 'is_generic' in self.mutation and self.mutation['is_generic'] == 'true'

    def __hash__(self):
        return hash(self.id) * 31 + hash(self.type)

    generic = property(_get_is_generic, doc="""
    True if the block is a generic component block (getter, setter, or method call), otherwise False.

    :type: bool
    """)
    # statements = property(_get_statements, doc="""
    # Access the statements of a block with continuation in an iterable fashion.
    #
    # :type: list[:class:`Block`]
    # """)


class BlockKind(Atom, Enum):
    DECLARATION = 1
    STATEMENT = 2
    VALUE = 3
    MUTATION = 4


class BlockType(Atom):
    def __init__(self, name, category, kind):
        """

        :param name:
        :type name: str
        :param category:
        :type category: BlockCategory
        :param kind:
        :type kind: BlockKind
        """
        self.name = name
        self.category = category
        self.kind = kind
        category.add_type(self)

    def __repr__(self):
        return 'BlockType(%r, %r, %r)' % (self.name, self.category, self.kind)

    def __call__(self, *args, **kwargs):
        return self.name


class BlockCategory(Atom):
    def __init__(self, name):
        self.name = name
        self.blocks = {}

    def __repr__(self):
        return 'aiatools.block_types.%s' % self.name

    def __call__(self, *args, **kwargs):
        return self.name

    def add_type(self, block_type):
        """

        :param block_type:
        :type block_type: BlockType
        """
        self.blocks[block_type.name] = block_type


class Method(Atom):
    # noinspection PyPep8Naming
    def __init__(self, name, description, deprecated, params, returnType=None):
        self.name = name
        self.description = description
        if isinstance(deprecated, str):
            self.deprecated = deprecated == 'true'
        else:
            self.deprecated = deprecated
        self.params = [param if isinstance(param, Parameter) else Parameter(**param) for param in params]
        self.return_type = returnType

    def __call__(self, *args, **kwargs):
        return self.name

    def __repr__(self):
        return 'Method(%s, %s, %s, %s)' % \
               (repr(self.name), repr(self.description), repr(self.deprecated), repr(self.params))


class Property(Atom):
    # noinspection PyPep8Naming
    def __init__(self, name, editorType=None, defaultValue=None, description=None, type=None, rw=None,
                 deprecated=False, editorArgs=None, alwaysSend=False):
        self.name = name
        self.type = type
        self.editor_type = editorType
        self.default_value = defaultValue
        self.description = description
        self.rw = rw
        if isinstance(deprecated, str):
            self.deprecated = deprecated == 'true'
        else:
            self.deprecated = deprecated
        self.editor_args = editorArgs
        self.always_send = alwaysSend

    def __call__(self, component, *args, **kwargs):
        return component.properties[self.name]

    def __repr__(self):
        return 'Property(%r, %r, %r, %r, %r, %r, %r)' % \
               (self.name, self.editor_type, self.default_value, self.description, self.type, self.rw, self.deprecated)


class Event(Atom):
    def __init__(self, name, description, deprecated, params):
        self.name = name
        self.description = description
        if isinstance(deprecated, str):
            self.deprecated = deprecated == 'true'
        else:
            self.deprecated = deprecated
        self.params = [param if isinstance(param, Parameter) else Parameter(**param) for param in params]

    def __call__(self, *args, **kwargs):
        return self.name

    def __repr__(self):
        return 'Event(%r, %r, %r, %r)' % (self.name, self.description, self.deprecated, self.params)


class Parameter(Atom):
    def __init__(self, name, type):
        self.name = name
        self.type = type

    def __call__(self, *args, **kwargs):
        return self.name

    def __repr__(self):
        return 'Parameter(%r, %r)' % (self.name, self.type)


class RecursiveIterator(object):
    def __init__(self, container, order='breadth', test=None, skip=None):
        self.stack = [container]
        self.order = order
        self.test = test
        self.skip = skip

    def __iter__(self):
        while len(self.stack) > 0:
            item = self.stack.pop(0)
            failed = self.test and not self.test(item)
            if self.skip and failed:
                continue
            if self.order == 'breadth':
                self.stack.extend(item.children())
            elif self.order == 'depth':
                self.stack = list(filter(lambda x: x, [child if child != item else None for child in item.children()])) + \
                             self.stack
            else:
                raise NotImplementedError(f'Recursive order {self.order} is unknown.')
            if not failed:
                yield item


class ComponentType(Atom):
    # noinspection PyShadowingBuiltins
    def __init__(self, name, methods=None, events=None, properties=None):
        self.name = name
        self.type = None
        self.external = False
        self.version = 1
        self.category_string = None
        self.help_string = None
        self.show_on_palette = True
        self.visible = False
        self.icon_name = None
        self.methods = None
        self.events = None
        self.properties = None
        if methods is not None:
            self.methods = {name: Method(**m) if isinstance(m, dict) else m for name, m in methods.items()}
            for name, method in self.methods.items():
                setattr(self, method.name, method)
        if events is not None:
            self.events = {name: Event(**e) if isinstance(e, dict) else e for name, e in events.items()}
            for name, event in self.events.items():
                setattr(self, event.name, event)
        if properties is not None:
            self.properties = {name: Property(**p) if isinstance(p, dict) else p for name, p in properties.items()}
            for name, property in self.properties.items():
                setattr(self, property.name, property)

    def __call__(self, *args, **kwargs):
        return self.name

    def __repr__(self):
        return 'aiatools.component_types.%s' % self.name

    def __str__(self):
        return self.name


class Extension(ComponentType):
    def __init__(self, *args, **kwargs):
        super(Extension, self).__init__(*args, **kwargs)
        self.external = True


class Component(object):
    _DISALLOWED_KEYS = {'$Components', '$Name', '$Type', '$Version', 'Uuid'}
    TYPES = {}

    def __init__(self, parent, uuid, type, name, version, properties=None):
        """

        :param parent:
        :type parent: ComponentContainer|None
        :param uuid:
        :param type:
        :param name:
        :param version:
        :param properties:
        """
        self.id = uuid
        self.parent = parent
        self.uuid = uuid
        self.type = type
        self.name = name
        self.version = version
        self.properties = properties
        self.path = '%s/%s' % (parent.name, self.name) if parent is not None else self.name

    def __repr__(self):
        # return '%s(%r, %r, %r, %r, %r, %r)' % (self.__class__.__name__, self.parent, self.uuid, self.type, self.name,
        #                                        self.version, self.properties)
        return '%s(%r, %r)' % (self.type, self.uuid, self.name)

    def children(self):
        return []

    @classmethod
    def from_json(cls, parent, json_repr):
        typename = json_repr['$Type']
        type = Component.TYPES[typename] if typename in Component.TYPES else Extension(typename)
        properties = {k: v for k, v in json_repr.items() if k not in Component._DISALLOWED_KEYS}
        return cls(parent, json_repr['Uuid'], type, json_repr['$Name'], json_repr['$Version'], properties)


class FilterableDict(dict):
    def filter(self, rule):
        if rule is None:
            return self
        else:
            return FilterableDict({k: v for k, v in self.items() if rule(k, v)})
