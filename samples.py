#!/usr/bin/env python
# -*- mode: python; coding: utf-8; -*-
# Copyright © 2017 Massachusetts Institute of Technology, All rights reserved.

"""
Query samples for AIATools
"""


from aiatools import *


__author__ = 'Evan W. Patton <ewpatton@mit.edu>'


def plot(sel, title, y_label):
    import matplotlib.pyplot as plt
    import numpy as np
    width = 0.35
    fig, ax = plt.subplots()
    ind = np.arange(len(sel))
    ax.bar(ind, list(sel.values()), width, color='r')
    ax.set_ylabel(y_label)
    ax.set_title(title)
    ax.set_xticks(ind)
    ax.set_xticklabels(iter(sel.keys()))
    plt.xticks(rotation=90)
    plt.show()


def radar_plot(sel, title):
    import matplotlib.pyplot as plt
    from plot import radar_factory
    num_vars = len(sel)
    theta = radar_factory(num_vars)
    fig, ax = plt.subplots(subplot_kw=dict(projection='radar'))
    labels = list(sel.keys())
    values = list(sel.values())
    min_values = min(values)
    max_values = max(values)
    the_range = max_values - min_values
    if the_range <= 5:
        ax.set_rgrids(list(range(min_values, max_values)))
    elif the_range <= 10:
        ax.set_rgrids(list(range(min_values, max_values, 2)))
    elif the_range <= 20:
        ax.set_rgrids(list(range(min_values, max_values, 4)))
    else:
        ax.set_rgrids(list(range(min_values, max_values, round(the_range / 5))))  # I chose round, but int could work
    ax.set_title(title, weight='bold')
    ax.plot(theta, values)
    ax.fill(theta, values, alpha=0.25)
    ax.set_varlabels(labels)
    plt.show()


def is_infinite_recursion(block):
    visited = {block}
    callers = list(select(block).callers())
    while len(callers) > 0:
        caller = rootBlock(callers.pop(0))
        if caller in visited:
            return True
        callers.extend(select(caller).callers())
    return False


is_proc_def = (type == procedures_defreturn) | (type == procedures_defnoreturn)


def main():
    with AIAFile('test_aias/Yahtzee5.aia') as aia:
        print('Components = ', aia.components())
        print('Number of components, by type =', aia.components().count(group_by=type))
        print('Number of buttons =', aia.components(type == Button).count())
        print('Number of labels =', aia.components(type == Label).count())
        radar_plot(aia.blocks().count(group_by=category), 'Blocks by Category (Yahtzee5)')

    with AIAFile('test_aias/LondonCholeraMap.aia') as aia:
        print('Number of screens =', len(aia.screens))
        print('Number of components on Screen1 =', len(aia.screens['Screen1'].components()))
        print('Components on Screen1 =', aia.screens['Screen1'].components())
        print('Number of buttons on Screen1 =', aia.screens['Screen1'].components(type == Button).count())
        print('Is the set of components with FusiontablesControl empty?', \
            aia.components(type == FusiontablesControl).empty())
        print('First button =', aia.components(type == Button)[0])
        print('Component LoadPumpBtn =', aia.components[name == 'LoadPumpBtn'])
        print('All components of type Map =', aia.components(type == Map))
        print('All components, grouped by type =', aia.components().count(group_by=type))
        print('All Logic blocks =', aia.blocks(category == Logic))
        print('All logic comparison blocks with text descendants =', \
            aia.blocks((type == logic_compare) & hasDescendant(type == text)))
        print('All blocks for the Map component =', aia.blocks(mutation.component_type == Map))
        print('Count of all Map component blocks =', aia.blocks(mutation.component_type == Map).count())
        print('Count of all Map component blocks, grouped by block type =', \
            aia.blocks(mutation.component_type == Map).count(group_by=type))
        print('Average depth of the block tree starting at the root blocks =', aia.blocks(top_level).avg(height))
        print('Count of generic blocks, grouped by block type and mutation component type =', \
            aia.blocks(mutation.is_generic).count(group_by=(type, mutation.component_type)))
        print('Descendants of logic blocks =', aia.blocks(category == Logic).descendants())
        plot(aia.blocks().count(group_by=type), 'Blocks by type', 'Count')
        radar_plot(aia.blocks().count(group_by=category), 'Blocks by Category (LondonCholeraMap)')

    with AIAFile('test_aias/ProcedureTest.aia') as aia:
        print('Number of procedure definitions =', \
            aia.blocks(is_procedure).count())
        print('Number of callers of VoidFoo =', aia.blocks(fields.NAME == 'VoidFoo').callers().count())
        print('Number of callers of FooStuff = ', aia.blocks(fields.NAME == 'FooStuff').callers().count())
        print('Active callers of disabled procedures =', \
            aia.blocks(is_proc_def & disabled).callers(~disabled).count())
        print('Callers of disabled procedures =', aia.blocks(is_proc_def & disabled).callers(~disabled))
        print('Recursive functions =', aia.blocks(is_proc_def & is_infinite_recursion).select(fields.NAME))
        print('Uncalled procedures =', aia.blocks(is_proc_def & ~is_called).select(fields.NAME))

    with AIAFile('test_aias/moodring_patched.aia') as aia:
        print('Mood Ring screens =', aia.screens())


if __name__ == '__main__':
    main()
