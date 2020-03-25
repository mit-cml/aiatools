# AIA Tools
AIA Tools is a Python library for interacting with App Inventor Application (AIA) files in Python. It is useful for opening, summarizing, and analyzing AIA files for research inquiries. The query API is inspired by SQLalchemy

## Installing

```shell
$ pip install aiatools
```

For development:

```shell
$ pyenv install 3.6.3
$ pyenv virtualenv 3.6.3 aiatools
$ pyenv activate aiatools
$ pip install -r requirements.txt
$ pip install .
```

## Usage Examples

```python
from aiatools import AIAFile

with AIAFile('MyProject.aia') as aia:
    print('Number of screens: %d\n' % len(aia.screens))
    print('Number of components: %d\n' % len(aia.screens['Screen1'].componentiter()))
    print('Number of blocks: %d\n' % len(aia.screens['Screen1'].blockiter()))
    print('Number of event blocks: %d\n' % len(aia.screens['Screen1'].blockiter(type='component_event')))
    aia.screens['Screen1'].blocks(type=='component_event').count(by='event_name')
```

```python
from aiatools import AIAFile
from aiatools.attributes import event_name, type
from aiatools.block_types import *
from aiatools.component_types import *

aia = AIAFile('MyProject.aia')

# Count the number of screens
print len(aia.screens)

# Count the number of distinct component types used on Screen1
print aia.screens['Screen1'].components().count(group_by=type)

# Count the number of Button components on Screen1
print aia.screens['Screen1'].components(type==Button).count()

# Count the number of component_event blocks, grouped by event name
print aia.screens['Screen1'].blocks(type==component_event).count(group_by=event_name)

# Compute the average depth of the blocks tree in Button.Click handlers
print aia.screens['Screen1'].blocks(type==component_event && event_name == Button.Click).avg(depth)

# Count the number of blocks referencing a specific component
print aia.screens['Screen1'].components(name=='Button1').blocks().count()

# Count the number of event handlers where the event opens another screen
print aia.blocks(type==component_event).descendants(type==control_openAnotherScreen).count()

# Get the screens where the user has included more than one TinyDB
print aia.screens().components(type==TinyDB).count(group_by = Screen.name).filter(lambda k,v: v > 1)
```

## Selectors

```python
project = AIAFile('project.aia')

project.screens()  # Select all screens
project.screens('Screen1')  # Select Screen1
project.screens(Button.any)  # Select any screen with at least 1 button
project.screens(Control.open_another_screen)  # Select any screen containing an open_another_screen block
project.screens(Component.Name == 'TinyDb1')  # Select any screen containing a component named TinyDb1
```

```python
class Block(object):
    """
    :py:class:`Block` represents an individual block in the blocks workspace.

    .. Arguments ::
        id_ The block ID
        type_ :py:class:`BlockType` The block type
    """
    def __init__(self, id_, type_):
        self.id = id_
        self.type = type_
        self.parent = None
        self.children = []


class Component(object):
    """
    :py:class:`Component` represents a component in the designer view.

    .. Arguments ::
        id_
        type_ :py:class:`ComponentType`
    """
    def __init__(self, id_, type_):
        self.id = id_
        self.type = type_
        self.properties = {}


class ComponentContainer(Component):
    def __init__(self, id_, type_):
        super(self, ComponentContainer).__init__(id_, type_)
        self.components = []


class BlockType(object):
    def __init__(self, name):
        self.name = name
        self.mutators = []


class ComponentType(object):
    def __init__(self, name, class_name):
        self.name = name
        self.class_name = class_name


class Screen(object):
    def __init__(self, scm=None, bky=None):
        self.name = ''
        self.properties = {}
        self.components = FilterableDict()
        self.blocks = FilterableDict()
        self.top_blocks = FilterableDict()
        if scm is not None:
            self._read_scheme(scm)
        if bky is not None:
            self._read_blocks(bky)


class Project(object):
    def __init__(self, file=None):
        self.name = ''
        self.screens = FilterableDict()
        self.components = FilterableDict()
        self.components.parent = self.screens
        self.blocks = FilterableDict()
        self.blocks.parent = self.screens
        if file is not None:
            self.read(file)


class FilterableDict(dict):
    def __call__(self, filter_):
        return FilterableDict([k, v for k, v in self.iteritems() if filter_(v) else None, None])


class Filter(object):
    def __call__(self, o):
        throw NotImplementedError()

    def __and__(self, right):
        return and_(self, right)

    def __or__(self, right):
        return or_(self, right)

    def __eq__(self, right):
        return eq(self, right)

    def __ne__(self, right):
        return ne(self, right)

    def __lt__(self, right):
        return lt(self, right)

    def __gt__(self, right):
        return gt(self, right)

    def __le__(self, right):
        return le(self, right)

    def __ge__(self, right):
        return ge(self, right)


class AndFilter(Filter):
    def __init__(self, l, r):
        self.l = l
        self.r = r

    def __call__(self, o):
        return self.l(o) and self.r(o)


class OrFilter(Filter):
    def __init__(self, l, r):
        self.l = l
        self.r = r

    def __call__(self, o):
        return self.l(o) or self.r(o)


class NotFilter(Filter):
    def __init__(self, expression):
        self.expression = expression

    def __call__(self, o):
        return not self.expression(o)


class EqualFilter(Filter):
    def __init__(self, l, r):
        self.l = l
        self.r = r

    def __call__(self, o):
        return self.l(o) == self.r(o)


class NotEqualFilter(Filter):
    def __init__(self, l, r):
        self.l = l
        self.r = r

    def __call__(self, o):
        return self.l(o) != self.r(o)


class LessThanFilter(Filter):
    def __init__(self, l, r):
        self.l = l
        self.r = r

    def __call__(self, o):
        return self.l(o) < self.r(o)


class GreaterThanFilter(Filter):
    def __init__(self, l, r):
        self.l = l
        self.r = r

    def __call__(self, o):
        return self.l(o) > self.r(o)


class LessThanOrEqualFilter(Filter):
    def __init__(self, l, r):
        self.l = l
        self.r = r

    def __call__(self, o):
        return self.l(o) <= self.r(o)


class GreaterThanOrEqualFilter(Filter):
    def __init__(self, l, r):
        self.l = l
        self.r = r

    def __call__(self, o):
        return self.l(o) <= self.r(o)


class ScreenFilter(Filter):
    pass


class ComponentFilter(Filter):
    pass


class BlockFilter(Filter):
    pass
```

## Attributes

`depth` - For a component, this is the depth of the component hierarchy rooted at that component. For components that are not containers this value is always 1. For containers and blocks, this is the longest length of the paths from this root node to any of its leaf nodes.

`length` - The number of direct descendants of the target. If the target is a component container, it will be the number of direct chidlren. For a block, it will be the number of

`children` - The list of children for the item(s) in the set. If more than one item is in the set, the children will be provided in the order of their parents.

`mutators` - If the block has mutations, a list of strings indicating the types of the mutations, e.g. ['if', 'elseif', 'elseif', 'else'].

`callers` - For procedures, the number of caller blocks in the workspace. For variables and component methods and properties, the number of getter blocks.

## Aggregation

`max` - Maximum value of the filter

`min` - Minimum value of the filter

`avg` - Average value of the filter

`count` - Count of items matching the filter

`median` - Median value of the attribute
