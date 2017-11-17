# -*- mode: python; coding: utf-8; -*-
# Copyright © 2017 Massachusetts Institute of Technology, All rights reserved.

"""

"""

from .common import BlockCategory, BlockType


__author__ = 'Evan W. Patton <ewpatton@mit.edu>'


def define_block_type(name, category):
    globals()[name] = BlockType(name, category)


Control = BlockCategory('Control')
Logic = BlockCategory('Logic')
Math = BlockCategory('Math')
Text = BlockCategory('Text')
Lists = BlockCategory('Lists')
Colors = BlockCategory('Colors')
Variables = BlockCategory('Variables')
Procedures = BlockCategory('Procedures')
# Components is plural to prevent collision with aiatools.common.Component
Components = BlockCategory('Components')

# Control category blocks
for _name in ['controls_if', 'controls_forRange', 'controls_forEach', 'controls_while', 'controls_choose',
              'controls_do_then_return', 'controls_eval_but_ignore', 'controls_openAnotherScreen',
              'controls_openAnotherScreenWithStartValue', 'controls_getStartValue', 'controls_closeScreen',
              'controls_closeScreenWithValue', 'controls_closeApplication', 'controls_getPlainStartText',
              'controls_closeScreenWithPlainText']:
    define_block_type(_name, Control)

# Logic category blocks
for _name in ['logic_boolean', 'logic_false', 'logic_negate', 'logic_compare', 'logic_operation', 'logic_or']:
    define_block_type(_name, Logic)

# Math category blocks
for _name in ['math_number', 'math_compare', 'math_add', 'math_subtract', 'math_multiply', 'math_division',
              'math_power', 'math_random_int', 'math_random_float', 'math_random_set_seed', 'math_on_list',
              'math_single', 'math_abs', 'math_neg', 'math_round', 'math_ceiling', 'math_floor', 'math_divide',
              'math_trig', 'math_cos', 'math_tan', 'math_atan2', 'math_convert_angles', 'math_format_as_decimal',
              'math_is_a_number', 'math_convert_number']:
    define_block_type(_name, Math)

# Text category blocks
for _name in ['text', 'text_join', 'text_length', 'text_isEmpty', 'text_compare', 'text_trim', 'text_changeCase',
              'text_starts_at', 'text_contains', 'text_split', 'text_split_at_spaces', 'text_segment',
              'text_replace_all', 'obfuscated_text', 'text_is_string']:
    define_block_type(_name, Text)

# renamed block
obsfucated_text = globals()['obfuscated_text']

# Lists category blocks
for _name in ['lists_create_with', 'lists_create_with_item', 'lists_add_items', 'lists_is_in', 'lists_length',
              'lists_is_empty', 'lists_pick_random_item', 'lists_position_in', 'lists_select_item', 'lists_insert_item',
              'lists_replace_item', 'lists_remove_item', 'lists_append_list', 'lists_copy', 'lists_is_list',
              'lists_to_csv_row', 'lists_to_csv_table', 'lists_from_csv_row', 'lists_from_csv_table',
              'lists_lookup_in_pairs']:
    define_block_type(_name, Lists)

# Colors category blocks
for _name in ['color_black', 'color_white', 'color_red', 'color_pink', 'color_orange', 'color_yellow', 'color_green',
              'color_cyan', 'color_blue', 'color_magenta', 'color_light_gray', 'color_gray', 'color_dark_gray',
              'color_make_color', 'color_split_color']:
    define_block_type(_name, Colors)

# Variables category blocks
for _name in ['global_declaration', 'lexical_variable_get', 'lexical_variable_set', 'local_declaration_statement',
              'local_declaration_expression']:
    define_block_type(_name, Variables)

# Procedures category blocks
for _name in ['procedures_defnoreturn', 'procedures_defreturn', 'procedures_callnoreturn', 'procedures_callreturn']:
    define_block_type(_name, Procedures)

# Component category blocks
for _name in ['component_event', 'component_method', 'component_set_get', 'component_component_block']:
    define_block_type(_name, Components)
