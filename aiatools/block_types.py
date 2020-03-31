# -*- mode: python; coding: utf-8; -*-
# Copyright © 2017 Massachusetts Institute of Technology, All rights reserved.

"""

"""

from .common import BlockCategory, BlockKind, BlockType

DECL = BlockKind.DECLARATION
STMT = BlockKind.STATEMENT
VAL = BlockKind.VALUE
MUT = BlockKind.MUTATION

__author__ = 'Evan W. Patton <ewpatton@mit.edu>'


def define_block_type(name, category, kind):
    globals()[name] = BlockType(name, category, kind)


Control = BlockCategory('Control')
Logic = BlockCategory('Logic')
Math = BlockCategory('Math')
Text = BlockCategory('Text')
Lists = BlockCategory('Lists')
Colors = BlockCategory('Colors')
Variables = BlockCategory('Variables')
Procedures = BlockCategory('Procedures')
Dictionaries = BlockCategory('Dictionaries')
# Components is plural to prevent collision with aiatools.common.Component
Components = BlockCategory('Components')

# Control category blocks
for _name, _kind in [
        ('controls_if', STMT),
        ('controls_forRange', STMT),
        ('controls_forEach', STMT),
        ('controls_while', STMT),
        ('controls_choose', VAL),
        ('controls_do_then_return', VAL),
        ('controls_eval_but_ignore', STMT),
        ('controls_openAnotherScreen', STMT),
        ('controls_openAnotherScreenWithStartValue', STMT),
        ('controls_getStartValue', VAL),
        ('controls_closeScreen', STMT),
        ('controls_closeScreenWithValue', STMT),
        ('controls_closeApplication', STMT),
        ('controls_getPlainStartText', VAL),
        ('controls_closeScreenWithPlainText', STMT),
        ('controls_break', STMT)]:
    define_block_type(_name, Control, _kind)

# Logic category blocks
for _name in ['logic_boolean', 'logic_false', 'logic_negate', 'logic_compare', 'logic_operation', 'logic_or']:
    define_block_type(_name, Logic, VAL)

# Math category blocks
for _name in ['math_number', 'math_compare', 'math_add', 'math_subtract', 'math_multiply', 'math_division',
              'math_power', 'math_bitwise', 'math_random_int', 'math_random_float', 'math_random_set_seed',
              'math_on_list', 'math_single', 'math_abs', 'math_neg', 'math_round', 'math_ceiling', 'math_floor',
              'math_divide', 'math_trig', 'math_cos', 'math_tan', 'math_atan2', 'math_convert_angles',
              'math_format_as_decimal', 'math_is_a_number', 'math_convert_number']:
    define_block_type(_name, Math, STMT if _name == 'math_random_set_seed' else VAL)

# Text category blocks
for _name in ['text', 'text_join', 'text_length', 'text_isEmpty', 'text_compare', 'text_trim', 'text_changeCase',
              'text_starts_at', 'text_contains', 'text_split', 'text_split_at_spaces', 'text_segment',
              'text_replace_all', 'obfuscated_text', 'text_is_string']:
    define_block_type(_name, Text, VAL)

# renamed block
obsfucated_text = globals()['obfuscated_text']

# Lists category blocks
for _name, _kind in [
        ('lists_create_with', VAL),
        ('lists_create_with_item', VAL),
        ('lists_add_items', STMT),
        ('lists_is_in', VAL),
        ('lists_length', VAL),
        ('lists_is_empty', VAL),
        ('lists_pick_random_item', VAL),
        ('lists_position_in', VAL),
        ('lists_select_item', VAL),
        ('lists_insert_item', STMT),
        ('lists_replace_item', STMT),
        ('lists_remove_item', STMT),
        ('lists_append_list', STMT),
        ('lists_copy', VAL),
        ('lists_is_list', VAL),
        ('lists_to_csv_row', VAL),
        ('lists_to_csv_table', VAL),
        ('lists_from_csv_row', VAL),
        ('lists_from_csv_table', VAL),
        ('lists_lookup_in_pairs', VAL),
        ('lists_join_with_separator', VAL)]:
    define_block_type(_name, Lists, _kind)

# Dictionaries category blocks
for _name, _kind in [
        ('dictionaries_create_with', VAL),
        ('pair', VAL),
        ('dictionaries_lookup', VAL),
        ('dictionaries_set_pair', STMT),
        ('dictionaries_delete_pair', STMT),
        ('dictionaries_recursive_lookup', VAL),
        ('dictionaries_recursive_set', STMT),
        ('dictionaries_getters', VAL),
        ('dictionaries_get_values', VAL),
        ('dictionaries_is_key_in', VAL),
        ('dictionaries_length', VAL),
        ('dictionaries_alist_to_dict', VAL),
        ('dictionaries_dict_to_alist', VAL),
        ('dictionaries_copy', VAL),
        ('dictionaries_combine_dicts', STMT),
        ('dictionaries_walk_tree', VAL),
        ('dictionaries_walk_all', VAL),
        ('dictionaries_is_dict', VAL)]:
    define_block_type(_name, Dictionaries, _kind)

# Colors category blocks
for _name in ['color_black', 'color_white', 'color_red', 'color_pink', 'color_orange', 'color_yellow', 'color_green',
              'color_cyan', 'color_blue', 'color_magenta', 'color_light_gray', 'color_gray', 'color_dark_gray',
              'color_make_color', 'color_split_color']:
    define_block_type(_name, Colors, VAL)

# Variables category blocks
for _name, _val in [
        ('global_declaration', DECL),
        ('lexical_variable_get', VAL),
        ('lexical_variable_set', STMT),
        ('local_declaration_statement', STMT),
        ('local_declaration_expression', VAL)]:
    define_block_type(_name, Variables, _val)

# Procedures category blocks
for _name in ['procedures_defnoreturn', 'procedures_defreturn', 'procedures_callnoreturn', 'procedures_callreturn']:
    define_block_type(_name, Procedures, VAL if 'call' in _name else DECL)

# Component category blocks
for _name, _kind in [('component_event', DECL), ('component_method', MUT), ('component_set_get', MUT),
                     ('component_component_block', VAL)]:
    define_block_type(_name, Components, _kind)
