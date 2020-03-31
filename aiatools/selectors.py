# -*- mode: python; coding: utf-8; -*-
# Copyright © 2017 Massachusetts Institute of Technology, All rights reserved.

"""
The :py:mod:`aiatools.selectors` modules provides high level selection and aggregation operations that can be executed
over a project.

.. testsetup:
    from aiatools import *
    project = AIAFile('test_aias/LondonCholeraMap.aia')
"""


from aiatools.algebra import Expression, AndExpression, identity
from aiatools.common import Block, Component, ComponentType, FilterableDict, RecursiveIterator
from aiatools.block_types import procedures_defnoreturn, procedures_defreturn, procedures_callnoreturn, \
    procedures_callreturn
from functools import reduce

__author__ = 'Evan W. Patton <ewpatton@mit.edu>'


class AggregateOperations:
    """
    :py:class:`AggregateOptions` is a mixin class that provides functionality for aggregation operations on selections.
    """

    # noinspection PyTypeChecker
    def count(self, group_by=None):
        """
        Counts the number of entities in a collection, optionally grouping by the ``group_by`` argument. ``group_by``
        will be called each element in the collection.

        .. doctest::

            >>> project.components().count()
            4
            >>> project.blocks(top_level).count(group_by=type)
            {'component_event': 2}
            >>> project.blocks().count(group_by=(type, mutation.component_type))
            {('component_event', 'Button'): 1, ('component_method', 'Map'): 2, ('component_event', 'Map'): 1, ('component_set_get', 'Marker'): 4}

        :param group_by: If given, a :py:class:`~aiatools.algebra.Functor` or tuple thereof, the value(s) of which
            will be used to group the entities in the collection for counting.
        :type group_by: tuple[aiatools.algebra.Functor or callable] or aiatools.algebra.Functor or callable or None
        :return: The count of the number of entities or a dictionary mapping unique ``group_by`` values to counts.
        :rtype: int or dict[(Atom, str) or Atom or str, int]
        """
        if group_by is None:
            result = 0
            for _ in self:
                result += 1
            return result
        elif not isinstance(group_by, tuple):
            group_by = (group_by,)
        result = FilterableDict()
        for value in self:
            attr = tuple(x(value) for x in group_by)
            if None not in attr:
                if len(attr) == 1:
                    attr = attr[0]
                if attr in result:
                    result[attr] += 1
                else:
                    result[attr] = 1
        return result

    def avg(self, func, group_by=None):
        """
        Averages the values of ``func`` applied to the collection, optionally grouping by the ``group_by`` argument.
        ``group_by`` will be called on each element in the collection.

        .. doctest::

            >>> project.blocks(top_level).avg(height)
            4.0
            >>> project.blocks().avg(depth)
            3.347826086956522

        :param func: The function to apply to the entities in the collection for which the average will be computed.
        :type func: aiatools.algebra.Functor or callable
        :param group_by: If given, a :py:class`~aiatools.algebra.Functor` or tuple thereof, the value(s) of which will
            be used to group the entities in the collection for averaging.
        :type group_by: tuple[aiatools.algebra.Functor or callable] or aiatools.algebra.Functor or callable or None
        :return: The average of the values of ``func`` applied to the entities of the collection or a dictionary
            mapping the value(s) of ``group_by`` applied to the entities to the average of ``func`` applied to the
            entities in the subset identified by the dictionary key.
        :rtype: int or dict[(Atom, str) or Atom or str, int]
        """
        if group_by is None:
            results = list(map(func, self))
            return sum(results) / len(results)
        elif not isinstance(group_by, tuple):
            group_by = (group_by,)
        state = {}
        for value in self:
            attr = tuple(x(value) for x in group_by)
            if None not in attr:
                if len(attr) == 1:
                    attr = attr[0]
                if attr in state:
                    state[attr]['sum'] += func(value)
                    state[attr]['count'] += 1
                else:
                    state[attr] = {'sum': func(value), 'count': 1}
        return FilterableDict({k: v['sum'] / v['count'] for k, v in state})

    def max(self, func, group_by=None):
        """
        Obtains the maximum value of ``func`` applied to the collection, optionally grouping by the ``group_by``
        argument. ``group_by`` will be called on each element in the collection.

        .. doctest::

            >>> project.blocks(type == component_event).max(height)
            6

        :param func: The function to apply to the entities in the collection for which the maximum will be computed.
        :type func: aiatools.algebra.Functor or callable
        :param group_by: If given, a :py:class:`~aiatools.algebra.Functor` or tuple thereof, the value(s) of which will
            be used to group the entities in the collection for determining the maximum.
        :type group_by:
        :return: The maximum of the values of ``func`` applied to the entities of the collection or a dictionary
            mapping the value(s) of ``group_by`` applied to the entities to the maximum of ``func`` applied to the
            entities in the subset identified by the dictionary key.
        :rtype: int or dict[(Atom, str) or Atom or str, int]
        """
        if group_by is None:
            return max(list(map(func, self)))
        elif not isinstance(group_by, tuple):
            group_by = (group_by,)
        result = FilterableDict()
        for value in self:
            attr = tuple(x(value) for x in group_by)
            if None not in attr:
                if len(attr) == 1:
                    attr = attr[0]
                attr_value = func(value)
                if (attr in result and result[attr] < attr_value) or attr not in result:
                    result[attr] = attr_value
        return result

    def min(self, func, group_by=None):
        """
        Obtains the minimum value of ``func`` applied to the collection, optionally grouping by the ``group_by``
        argument. ``group_by`` will be called on each element in the collection.

        .. doctest::

            >>> project.blocks(type == component_event).min(height)
            2
            >>> project.blocks(category == Components).min(height, group_by=type)
            {'component_event': 2, 'component_method': 1, 'component_set_get': 1}
            >>> project.blocks().min(height, group_by=(type, mutation.component_type))
            {('component_event', 'Button'): 2, ('component_method', 'Map'): 1, ('component_event', 'Map'): 6, ('component_set_get', 'Marker'): 1}

        :param func: The function to apply to the enetities in the collection for which the minimum will be computed.
        :type func: aiatools.algebra.Functor or callable
        :param group_by: If given, a :py:class:`~aiatools.algebra.Functor` or tuple thereof, the value(s) of which will
            be used to group the entities in the collection determining the minimum.
        :type group_by: tuple[aiatools.
        :return: The minimum of the values of ``func`` applied to the entities of the collection or a dictionary
            mapping the value(s) of ``group_by`` applied to the entities to the minimum of ``func`` applied to the
            entities in the subset identified by the dictionary key.
        :rtype: int or dict[(Atom, str) or Atom or str, int]
        """
        if group_by is None:
            return min(list(map(func, self)))
        elif not isinstance(group_by, tuple):
            group_by = (group_by,)
        result = FilterableDict()
        for value in self:
            attr = tuple(x(value) for x in group_by)
            if None not in attr:
                if len(attr) == 1:
                    attr = attr[0]
                attr_value = func(value)
                if (attr in result and result[attr] > attr_value) or attr not in result:
                    result[attr] = attr_value
        return result

    def empty(self):
        """
        Tests whether the result of the selector chains up to and including the current selection is empty.

        .. doctest::

            >>> project.components(type == Voting).empty()
            True
            >>> project.components(type == Button).empty()
            False

        :return: ``True`` if the selection is empty, otherwise ``False``.
        :rtype: bool
        """
        for _ in self:
            return False
        return True

    def __iter__(self):
        raise NotImplemented()


class Selectors:
    """
    :py:class:`Selectors` is a mixin class for collections that enables selecting entities related to entities in the
    collection.
    """
    def __init__(self, *args):
        pass

    def screens(self, test=None, *args):
        """
        Select the screens containing the elements in the collection.

        Returns
        -------
        Selector[Screen]
            A selector over the screens containing the entities in the collection.

        Todo
        ----
            - (ewpatton) Implement subset selection on screens
        """
        test = identity if test is None else test
        screens = {item.id: item for item in self
                   if ((isinstance(item.type, ComponentType) and item.type.name == 'Form') or item.type == 'Form')
                   and test(item)}
        block_screens = {item.screen.id: item.screen for item in self if (isinstance(item, Block) and test(item))}
        screens.update(block_screens)
        return Selector(screens)

    def components(self, test=None, *args):
        """
        Select the subset of entities in the current selection that are :py:class:`Component`.

        Returns
        -------
        Selector[Component]
            A selector for further selection of entities. The selector will only contain :py:class:`Component`.

        Todo
        ----
            - (ewpatton) Implement subset selection on components
        """
        test = identity if test is None else test
        return Selector({item.id: item for item in self if (isinstance(item, Component) and test(item))})

    def blocks(self, test=None, *args):
        """
        Select blocks under the current node. The following filters can be applied:

        Returns
        -------
        Selector[Block]
            A selector for further selection of entities. The selector will only contain :py:class:`Block`.

        Todo
        ----
            - (ewpatton) Implement subset selection on blocks.
        """
        test = identity if test is None else test
        return Selector({item.id: item for item in self if (isinstance(item, Block) and test(item))})

    def callers(self, *args):
        """
        Select any blocks that result in a call to any callable blocks in the selection.

        Note
        ----
            Only operates on procedures at this time. See TODO about adding support for components.

        Returns
        -------
        Selector[Block]
            A selector over the callers (if any) of the callable blocks contained in the collection. The selector will
            only contain :py:class:`Block`.

        Todo
        ----
            - (ewpatton) Implement subset selection on the blocks
            - (ewpatton) Add call graph so that component method/event blocks can be included
        """
        _filter = args[0] if len(args) > 0 else lambda x: True
        return Selector({block.id: block for item in self
                         if item.type in (procedures_defreturn(), procedures_defnoreturn())
                         for block in item.screen.blocks
                         if block.type in (procedures_callnoreturn(), procedures_callreturn()) and
                         block.fields['PROCNAME'] == item.fields['NAME'] and _filter(block)})

    def callees(self, *args, **kwargs):
        """
        Select procedure definition blocks (if any) that are called by the procedure call blocks in the collection.

        Note
        ----
            Only operates on procedures at this time. See TODO about adding support for components.

        Returns
        -------
        Selector[Block]
            A selector over the callees (if any) of the caller blocks contained in the collection. The selector will
            only container :py:class:`Block`.

        Todo
        ----
            - (ewpatton) Implement subset selection on the blocks
            - (ewpatton) Add call graph so that component method/event blocks can be included
        """
        pass

    def branch(self, branch_id):
        """
        Retrieve

        Parameters
        ----------
        branch_id : int
            Retrieve the __branch_id__th branch of any blocks in this collection that have a statement input. This can
            be used to walk an if-elseif-else block, for example.

        Todo
        ----
            - (ewpatton) Implementation
        """
        pass

    def map(self, functor):
        """
        Applies ``functor`` to the entities in the selection.

        Parameters
        ----------
        functor : callable

        Returns
        -------
        list
            A list in the value space of ``functor``.
        """
        return [functor(x) for x in self if functor(x) is not None]

    def select(self, selector):
        """
        Selects a subset of the entities in the selection for which ``selector(item)`` is True.

        Parameters
        ----------
        selector : Expression
            The expression to be applied to filter the current selection.

        Returns
        -------
        Selector[T]
            The subset of the selection. The exact contents of the subset depends on the type of content of the
            current selection.
        """
        return Selector({item.id: selector(item) for item in self if selector(item) is not None})

    def descendants(self, test=None, order='natural', skip_failures=False):
        """
        Selects all of the descendants of the entities in the current selection.

        Parameters
        ----------
        test : callable
            An optional test used to filter out items from the iteration. Default: None

        order : str
            The order of iteration. Options are 'natural', 'breadth', or 'depth'. Default: 'natural'

        skip_failures : bool
            If skip_failures is true and test is provided but fails for an element, the subtree starting at the element
            is pruned.

        Returns
        -------
        Selector[T]
            The descendants of the entities in the current selection, if any.
        """
        def order_type(m):
            return order if order != 'natural' else ('depth' if isinstance(m, Block) else 'breadth')
        return Selector({obj.id: obj if not test or test(obj) else None for match in self
                         for obj in RecursiveIterator(match, order_type(match), test, skip_failures)})

    def __iter__(self):
        raise NotImplemented()


class Selector(AggregateOperations, Selectors):
    """
    :py:class:`Selector` provides a lazily computed application of an expression over a collection. Items in the
    underlying collection can be accessed in three ways:

    1. Through use of an iterable. :py:class:`Selector` is an iterable, and iterating over it yields its values. There
       is also :py:meth:`iteritems`, which iterates over key, value pairs in the collection similar to how the
       iteritems method in :py:obj:`dict` works.
    2. Through an identifier/key. For example, accessing the Component called Button1 can be done with
       ``selection['Button1']``.
    3. Through an index. For example, if ``children`` is a :py:class:`Selector, ``children[5]`` will give the 6th
       element in the selection. This is not random access, but linear in ``n``, so if accessing elements in sequence is
       required using the iteration method is recommended.

    Selectors can also be called, in which case they will return a new Selector whose elements are given by applying
    the first argument of the function call to each element in the underlying collection.

    Parameters
    ----------
    collection : collections.Iterable[{id}] or dict[{id}]
        A collection of objects
    """
    def __init__(self, collection):
        super(Selector, self).__init__()
        if not hasattr(collection, '__iter__'):
            collection = NamedCollection({collection.id: collection})
        self._collection = collection

    def __call__(self, *args, **kwargs):
        _filter = args[0] if len(args) == 1 else lambda x: True
        subset = NamedCollection()
        for item in self._collection.values():
            if _filter(item):
                subset[item.id] = item
        return Selector(subset)

    def __getitem__(self, item):
        if isinstance(item, int):
            i = item if item >= 0 else item + len(self)
            for v in self:
                if i == 0:
                    return v
                else:
                    i -= 1
            raise IndexError(item)
        try:
            return self._collection[item]
        except KeyError:
            return NamedCollection()

    def __contains__(self, item):
        return item in self._collection

    def __setitem__(self, key, value):
        raise NotImplementedError('Cannot modify read-only collection')

    def __repr__(self):
        return repr(list(self))

    def __iter__(self):
        return iter(self._collection.values())

    def values(self):
        return iter(self._collection.values())

    def items(self):
        return iter(self._collection.items())

    def __len__(self):
        return len(list(iter(self)))


class PrefixedSelector(Selector):
    def __init__(self, prefix, collection):
        super(PrefixedSelector, self).__init__(collection)
        self.prefix = prefix

    def __getitem__(self, item):
        try:
            return super(PrefixedSelector, self).__getitem__('%s/%s' % (self.prefix, item))
        except KeyError:
            # Fallback to non-prefixed implementation
            return super(PrefixedSelector, self).__getitem__(item)

    def __contains__(self, item):
        return super(PrefixedSelector, self).__contains__('%s/%s' % (self.prefix, item)) or \
            super(PrefixedSelector, self).__contains__(item)

    def __setitem__(self, key, value):
        raise NotImplementedError()

    def __iter__(self):
        return iter(self._collection.values())

    def iteritems(self):
        for k, v in self._collection.items():
            if not k.startswith(self.prefix):
                yield '%s/%s' % (self.prefix, k), v
            else:
                yield k, v

    def itervalues(self):
        return iter(self._collection.values())


class NamedCollection(dict, AggregateOperations, Selectors):
    def __call__(self, functor=None, *args, **kwargs):
        """

        :param functor:
        :param args:
        :param kwargs:
        :return:
        :rtype: NamedCollectionView
        """
        if len(args) > 0:
            for i in range(len(args)):
                functor = functor & args[i]
        return NamedCollectionView(self, functor)

    def __getitem__(self, item):
        if isinstance(item, Expression):
            return NamedCollectionView(self, item)
        elif isinstance(item, tuple):
            return NamedCollectionView(self, reduce(AndExpression, item))
        else:
            return super(NamedCollection, self).__getitem__(item)


class NamedCollectionView(AggregateOperations, Selectors):
    def __init__(self, parent, functor):
        super(NamedCollectionView, self).__init__()
        self.parent = parent
        self.functor = functor

    def __iter__(self):
        parent, functor = self.parent, self.functor

        if functor is not None:
            def generator():
                for key, value in parent.items():
                    if functor(value):
                        yield key, value
                raise StopIteration
            return generator()
        else:
            return iter(self.parent.items())

    def iteritems(self):
        return iter(self)

    def filter(self, rule):
        return self if rule is None else NamedCollectionView(self, rule)

    def __repr__(self):
        return repr(dict(iter(self)))


class UnionSelector(AggregateOperations, Selectors):
    def __init__(self, collection, field):
        super(UnionSelector, self).__init__()
        self.collection = collection
        self.field = field

    def __iter__(self):
        for c in self.collection.values():
            if hasattr(c, self.field):
                for v in getattr(c, self.field):
                    yield v

    def itervalues(self):
        for c in self.collection:
            if hasattr(c, self.field):
                child = getattr(c, self.field)
                for v in child.values():
                    yield v

    def iteritems(self):
        for c in self.collection:
            if hasattr(c, self.field):
                child = getattr(c, self.field)
                for k, v in child.items():
                    yield k, v

    def __call__(self, *args, **kwargs):
        if len(args) == 1:
            functor = args[0]
        else:
            def functor(_):
                return True
        if len(kwargs) > 0:
            pass
        else:
            return Selector({v.id: v for v in iter(self) if functor(v)})

    def __getitem__(self, item):
        if isinstance(item, int):
            i = item if item >= 0 else item + len(self)
            for v in self:
                if i == 0:
                    return v
                else:
                    i -= 1
            raise IndexError(item)
        else:
            for v in self.collection.values():
                if hasattr(v, self.field):
                    haystack = getattr(v, self.field)
                    if item in haystack:
                        return haystack[item]
                    else:
                        # TODO(ewpatton): Make support ID paths, e.g. Screen1/Arrange1/Button1
                        for u in haystack.values():
                            if u.name == item:
                                return u
        raise KeyError(item)

    def __len__(self):
        return len(list(iter(self)))


def select(item):
    """
    :py:func:`~aiatools.selectors.select` is a convenience method for creating a selection out of a single item. This
    allows one to select a specific component for further exploration
    :param item:
    :return:
    """
    return Selector(item)
