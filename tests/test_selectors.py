# -*- mode: python; coding: utf-8; -*-
"""
Tests for selections that span several screens, where block ids and component Uuids may repeat.

Run with ``python -m unittest discover tests``.
"""

import io
import json
import os
import unittest
import zipfile

from aiatools import AIAFile
from aiatools.attributes import type as block_type
from aiatools.block_types import component_event

TEST_AIAS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'test_aias')

BKY = """<xml xmlns="https://developers.google.com/blockly/xml">
  <block type="component_event" id="1" x="0" y="0">
    <mutation component_type="Button" is_generic="false" instance_name="Button1" event_name="Click"></mutation>
    <field name="COMPONENT_SELECTOR">Button1</field>
    <statement name="DO">
      <block type="controls_if" id="2"></block>
    </statement>
  </block>
</xml>"""


def scm(name):
    return '#|\n$JSON\n' + json.dumps({'YaVersion': '208', 'Source': 'Form', 'Properties': {
        '$Name': name, '$Type': 'Form', '$Version': '27', 'Uuid': '0', 'Title': name,
        '$Components': [{'$Name': 'Button1', '$Type': 'Button', '$Version': '7', 'Uuid': '1'}]}}) + '\n|#'


def make_aia(screens):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as z:
        z.writestr('youngandroidproject/project.properties', 'main=appinventor.ai_test.Repro.Screen1\nname=Repro\n')
        for s in screens:
            z.writestr('src/appinventor/ai_test/Repro/%s.scm' % s, scm(s))
            z.writestr('src/appinventor/ai_test/Repro/%s.bky' % s, BKY)
    buf.seek(0)
    return buf


class TestMultiScreenSelection(unittest.TestCase):
    def test_blocks_with_repeated_ids_are_all_selected(self):
        with AIAFile(make_aia(['Screen1', 'Screen2'])) as aia:
            per_screen = sum(len(s.blocks()) for s in aia.screens)
            self.assertEqual(4, per_screen)
            self.assertEqual(per_screen, len(aia.blocks()))
            self.assertEqual(2, len(aia.blocks(block_type == component_event)))
            self.assertEqual(4, len(aia.blocks()(lambda b: True)))  # re-selecting keeps them distinct
            self.assertEqual({'Screen1', 'Screen2'}, {b.screen.name for b in aia.blocks(block_type == component_event)})

    def test_components_with_repeated_uuids_are_all_selected(self):
        with AIAFile(make_aia(['Screen1', 'Screen2'])) as aia:
            self.assertEqual(4, len(aia.components()))  # two Forms and two Buttons

    def test_single_screen_selection_unchanged(self):
        with AIAFile(make_aia(['Screen1'])) as aia:
            blocks = aia.blocks()
            self.assertEqual(2, len(blocks))
            self.assertEqual('component_event', blocks['1'].type)  # lookup by block id still works

    def test_sample_projects_match_per_screen_counts(self):
        for name in sorted(os.listdir(TEST_AIAS)):
            with self.subTest(name=name), AIAFile(os.path.join(TEST_AIAS, name)) as aia:
                self.assertEqual(sum(len(s.blocks()) for s in aia.screens), len(aia.blocks()))


if __name__ == '__main__':
    unittest.main()
