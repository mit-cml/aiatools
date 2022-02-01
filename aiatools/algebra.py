# -*- mode: python; coding: utf-8; -*-
# Copyright © 2017 Massachusetts Institute of Technology, All rights reserved.

"""
aiatools.algebra defines the expressions and evaluation rules for querying the contents of AIA files.
"""
try:
    from collections.abc import Callable
except ImportError:
    from collections import Callable


__author__ = 'Evan W. Patton <ewpatton@mit.edu>'


def _reduce_expression(expr, op):
    while isinstance(expr, Expression) and not isinstance(expr, Atom):
        expr = expr(op)
    return expr


def identity(x):
    """
    Helper function that returns its input.

    >>> identity("string")
    'string'
    >>> identity(True)
    True
    >>> identity(None)

    :param x: any value
    :return: x
    """
    return x


def needs_eval(x):
    """
    Tests whether its input needs ot be evaluated.

    >>> needs_eval(Expression())
    True
    >>> needs_eval(Atom())
    False

    :param x: the input expression
    :type x: Expression|callable
    :return:
    """
    if isinstance(x, Expression):
        return not isinstance(x, Atom)
    elif isinstance(x, Callable):
        return True
    return False


class Expression(object):
    """
    Base interface for constructing expressions over App Inventor projects.

    Expressions by default support the following operations:

    1. ``left == right``: Accepts an entity if and only if ``left(entity) == right(entity)``
    2. ``left != right``: Accepts an entity if and only if ``left(entity) != right(entity)``
    3. ``left < right``: Accepts an entity if and only if ``left(entity) < right(entity)``
    4. ``left > right``: Accepts an entity if and only if ``left(entity) > right(entity)``
    5. ``left <= right``: Accepts an entity if and only if ``left(entity) <= right(entity)``
    6. ``left >= righ``: Accepts an entity if and only if ``left(entity >= right(entity)``
    7. ``left & right``: Accepts an entity if and only if ``left(entity) and right(entity)`` is True.
    8. ``left | right``: Accepts an entity if and only if ``left(entity) or right(entity)`` is True.
    9. ``~expr``: Accepts an entity if and only if ``not expr(entity)`` is True
    """
    def __eq__(self, other):
        """
        Constructs a new EquivalenceExpression with this expression as the left hand side and ``other`` as the right
        hand side.

        :param other: The other thing to check for equivalence with this expression when evaluated.
        :type other: Expression
        :return: A new equivalence expression
        :rtype: EquivalenceExpression
        """
        return EquivalenceExpression(self, other)

    def __ne__(self, other):
        """
        Constructs a new NotnequivalenceExpression with this expression as the left hand side and ``expr`` as the right
        hand side.

        :param other: The other expression to check for nonequivalence with this expression when evaluated.
        :type other: Expression
        :return:
        """
        return NonequivalenceExpression(self, other)

    def __hash__(self):
        return id(self)

    def __lt__(self, other):
        return LessThanExpression(self, other)

    def __gt__(self, other):
        return GreaterThanExpression(self, other)

    def __le__(self, other):
        return LessThanOrEqualExpression(self, other)

    def __ge__(self, other):
        return GreaterThanOrEqualExpression(self, other)

    def __and__(self, other):
        return AndExpression(self, other)

    def __or__(self, other):
        return OrExpression(self, other)

    def __invert__(self):
        return NotExpression(self)

    def __call__(self, operand, *args, **kwargs):
        raise NotImplementedError


class BinaryExpression(Expression):
    """
    Abstract base class for an Expression taking two clauses.

    Concrete implementations of this class must provide an implementation of the ``__call__`` special method to evaluate
    the truth value of the left and right hand sides.

    Parameters
    ----------
    left : Expression
        The left hand side of the binary expression.
    right : Expression
        The right hand side of the binary expression.
    """
    def __init__(self, left, right):
        self.left = ComputedAttribute(left) if isinstance(left, Callable) and not isinstance(left, Expression) else left
        self.right = ComputedAttribute(right) if isinstance(right, Callable) and not isinstance(right, Expression) else right

    def __call__(self, operand, *args, **kwargs):
        raise NotImplementedError


class EquivalenceExpression(BinaryExpression):
    """
    :py:class:`EquivalenceExpression` compares the output of two expressions for equivalent values, however == is
    defined on those values. An EquivalenceExpression is typically constructed by using the == operator on an existing
    pair of expressions, for example:

        >>> from aiatools.attributes import name
        >>> name == 'Button1'
        NamedAttributeTuple(('name', 'instance_name')) == 'Button1'
    """
    def __call__(self, operand, *args, **kwargs):
        left_val = _reduce_expression(self.left, operand)
        right_val = _reduce_expression(self.right, operand)
        return (left_val == right_val) is True

    def __repr__(self):
        return '%r == %r' % (self.left, self.right)


class NonequivalenceExpression(BinaryExpression):
    """
    :py:class:`NonequivalenceExpression` compares the output of two expressions for nonequivalent values, however != is
    defined on those values. A NonequivalenceExpression is typically constructed by using the != operator on an existing
    pair of expressions, for example:

        >>> from aiatools.attributes import name
        >>> name != 'Button1'
        NamedAttributeTuple(('name', 'instance_name')) != 'Button1'
    """
    def __call__(self, operand, *args, **kwargs):
        left_val = self.left(operand) if isinstance(self.left, Expression) else self.left
        right_val = self.right(operand) if isinstance(self.right, Expression) else self.right
        return (left_val != right_val) is True

    def __repr__(self):
        return '%r != %r' % (self.left, self.right)


class LessThanExpression(BinaryExpression):
    """
    :py:class:`LessThanExpression` compares the output of two expressions and returns True if the value of the left hand
    side of the expression is less than the value of the right hand expression, for the definition of the less than
    operation on the two values. A LessThanExpression is typically constructed by using the < operator on an existing
    pair of expressions, for example:

        >>> from aiatools.attributes import version
        >>> version < 5
        NamedAttribute('version') < 5
    """
    def __call__(self, operand, *args, **kwargs):
        left_val = self.left(operand) if isinstance(self.left, Expression) else self.left
        right_val = self.right(operand) if isinstance(self.right, Expression) else self.right
        return (left_val < right_val) is True

    def __repr__(self):
        return '%r < %r' % (self.left, self.right)


class GreaterThanExpression(BinaryExpression):
    """
    :py:class:`GreaterThanExpression` compares the output of two expressions and returns True if the value of the left
    handl side of the expression is greater than the value of the right hand expression, for the definition of the
    greater than operation on the two values. A GreaterThanExpression is typically constructed by using the > operator
    on an existing pair of expressions, for example:

        >>> from aiatools.attributes import version
        >>> version > 5
        NamedAttribute('version') > 5
    """
    def __call__(self, operand, *args, **kwargs):
        left_val = self.left(operand) if isinstance(self.left, Expression) else self.left
        right_val = self.right(operand) if isinstance(self.right, Expression) else self.right
        return (left_val > right_val) is True

    def __repr__(self):
        return '%r > %r' % (self.left, self.right)


class LessThanOrEqualExpression(BinaryExpression):
    def __call__(self, operand, *args, **kwargs):
        left_val = self.left(operand) if isinstance(self.left, Expression) else self.left
        right_val = self.right(operand) if isinstance(self.right, Expression) else self.right
        return (left_val <= right_val) is True

    def __repr__(self):
        return '%r <= %r' % (self.left, self.right)


class GreaterThanOrEqualExpression(BinaryExpression):
    def __call__(self, operand, *args, **kwargs):
        left_val = self.left(operand) if isinstance(self.left, Expression) else self.left
        right_val = self.right(operand) if isinstance(self.right, Expression) else self.right
        return (left_val >= right_val) is True

    def __repr__(self):
        return '%r >= %r' % (self.left, self.right)


class AndExpression(BinaryExpression):
    def __call__(self, operand, *args, **kwargs):
        left_val = self.left(operand) if isinstance(self.left, Expression) else self.left
        right_val = self.right(operand) if isinstance(self.right, Expression) else self.right
        return left_val and right_val

    def __repr__(self):
        return '%r & %r' % (self.left, self.right)


class OrExpression(BinaryExpression):
    """

    """
    def __call__(self, operand, *args, **kwargs):
        left_val = self.left(operand) if isinstance(self.left, Expression) else self.left
        right_val = self.right(operand) if isinstance(self.right, Expression) else self.right
        return left_val or right_val

    def __repr__(self):
        return '%s | %s' % (self.left, self.right)


class NotExpression(Expression):
    """
    :py:class:`NotExpression` is a unary expression that logically negates the output of the expression it encapsulates.
    NotExpressions are typically instantiated by using the unary prefix operator ~ to invert the expression. Note that
    ~ binds tightly, so most expressions, unless they are :py:class:`Atom`, must be wrapped in parentheses.

    Note
    ----
    NotExpression will optimize its own inversion so that two operators will cancel one another out. For example:

        >>> from aiatools.attributes import disabled
        >>> ~disabled
        ~NamedAttribute('disabled')
        >>> ~~disabled
        NamedAttribute('disabled')

    Parameters
    ----------
    expr : Expression
        The expression to negate.
    """
    def __init__(self, expr):
        self.expr = ComputedAttribute(expr) if isinstance(expr, Callable) and not isinstance(expr, Expression) else expr

    def __call__(self, operand, *args, **kwargs):
        return not (self.expr(operand) if isinstance(self.expr, Expression) else self.expr)

    def __repr__(self):
        if isinstance(self.expr, Expression) and not isinstance(self.expr, (Functor, Atom)):
            return '~(%r)' % self.expr
        return '~%r' % self.expr

    def __invert__(self):
        return self.expr


class Atom(Expression):
    """
    :py:class:`Atom` represents an entity in the grammar, such as a specific component type (Button) or block type
    (component_set_get). Atoms cannot be modified and evaluate to themselves.
    """
    def __eq__(self, other):
        if isinstance(other, Atom):
            return other is self
        elif isinstance(other, Expression):
            return other == self
        elif isinstance(other, str):
            return other == self()
        else:
            return False

    def __hash__(self):
        return id(self)

    def __ne__(self, other):
        if isinstance(other, Atom):
            return other is not self
        else:
            return other != self

    def __call__(self, operand, *args, **kwargs):
        return self


class Functor(Expression):
    """
    :py:class:`Functor` is an abstract base class that serves as the root of the class tree of classes that apply
    functions to entities. Unlike most expressions, these typically compute non-Boolean values that may then undergo
    further computation.
    """
    def __call__(self, obj, *args, **kwargs):
        if needs_eval(obj):
            return FunctionComposition(self, obj)
        raise NotImplemented()


class Collection(Atom):
    """
    :py:class:`Collection` is an :py:class:`Atom` wrapping a collection, such as a list or tuple, of entities. Calls to
    the Collection will filter the collection given an Expression.

    Parameters
    ----------
    collection : collections.Iterable[aiatools.common.Component|aiatools.common.Block]
        The Python collection of entities to be wrapped into the new atomic collection.
    """
    def __init__(self, collection):
        self.collection = collection

    def __call__(self, *args, **kwargs):
        return Collection(list(filter(args[0], self.collection)))


class FunctionComposition(Functor):
    """
    :py:class:`ComposedAttribute` is a :py:class:`Functor` that wraps other Functors, Python functions, or lambda
    expressions. Functions are evaluated from left to right.

        >>> from aiatools import *
        >>> isinstance(root_block(declaration), FunctionComposition)
        True
        >>> proctest = AIAFile('test_aias/ProcedureTest2.aia')
        >>> proctest.blocks(is_procedure).callers(root_block(declaration)).map(fields.PROCNAME)
        ['i_am_called']

    Parameters
    ----------
    *args
        Functions to compose into a new function
    """
    def __init__(self, *args):
        self.functors = list(args) + [identity]

    def __call__(self, obj, *args, **kwargs):
        if needs_eval(obj):
            self.functors = [obj] + self.functors
            return self
        else:
            for op in self.functors:
                obj = op(obj)
            return obj


class ComputedAttribute(Functor):
    """
    :py:class:`ComputedAttribute` is a :py:class:`Functor` that wraps a Python function or lambda expression. This
    allows for arbitrary computations to be used in evaluating entities in a project.

    Parameters
    ----------
    functor : callback
        The functor that should be applied to the entity when the ComputedAttribute needs to be computed. Note that the
        return value is not memoized, so the given functor should be time efficient as possible when computing its
        value.
    """
    def __init__(self, functor):
        self.functor = functor

    def __call__(self, obj, *args, **kwargs):
        if needs_eval(obj):
            return FunctionComposition(self, obj)
        return self.functor(obj, *args, **kwargs)

    def __hash__(self):
        return hash(self.functor)

    def equals(self, other):
        return id(self.functor) == id(other.functor)

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.functor)


and_ = AndExpression
or_ = OrExpression
not_ = NotExpression
