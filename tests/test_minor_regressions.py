"""Non-régressions des points mineurs de la contre-revue."""
import shutil
import unittest
import xml.etree.ElementTree as ET
from unittest.mock import patch

import fitz
import pikepdf
import test_inspection as fixtures
from analyzer import analyze, parse_report
from locations import Locator


class MinorRegressions(unittest.TestCase):
    def setUp(self):
        fixtures.InspectionTests.setUp(self)

    def tearDown(self):
        fixtures.InspectionTests.tearDown(self)

    def test_moved_pdf_is_importable_with_explicit_weak_provenance(self):
        xml = self.folder/'rapport.xml'
        xml.write_bytes(fixtures.report(self.path))
        destination = self.folder/'déplacé'
        destination.mkdir()
        moved = destination/self.path.name
        shutil.move(self.path, moved)
        result = analyze(moved, xml)
        self.assertFalse(result['fresh'])
        self.assertIn('sans preuve', result['provenance'])

    def test_missing_or_invalid_identity_fields_are_rejected(self):
        for field in ['size', 'jobEndStatus', 'failedChecks', 'passedChecks', 'failedRules']:
            with self.subTest(field=field):
                root = ET.fromstring(fixtures.report(self.path))
                for node in root.iter():
                    node.attrib.pop(field, None)
                with self.assertRaises(ValueError):
                    parse_report(ET.tostring(root), self.path)
        for size in ['abc', '-1']:
            with self.assertRaisesRegex(ValueError, 'non numérique'):
                parse_report(fixtures.report(self.path, size=size), self.path)
        with self.assertRaisesRegex(ValueError, 'Profil reçu'):
            parse_report(fixtures.report(self.path, profile='Préfixe PDF/UA-1 profil inventé'), self.path)

    def test_reversed_annotation_rectangle_is_normalized(self):
        with pikepdf.open(self.path, allow_overwriting_input=True) as pdf:
            pdf.pages[0].Annots[0]['/Rect'] = pikepdf.Array([210, 125, 150, 100])
            pdf.save(self.path)
        locator = Locator(self.path)
        try:
            a, b = locator.pdf.pages[0].Annots[0].objgen
            result = locator.resolve(f'root/pages[0]/annots[0]({a} {b} obj PDLinkAnnot)')
            self.assertEqual(result[0]['rects'], [[150, 100, 210, 125]])
        finally:
            locator.close()

    def test_font_boxes_survive_rotation_and_shifted_cropbox(self):
        for rotation in [0, 90, 180, 270]:
            path = self.folder/f'police-{rotation}.pdf'
            doc = fitz.open()
            page = doc.new_page(width=400, height=500)
            page.insert_text((50, 100), 'Texte témoin', fontname='helv', fontsize=20)
            page.set_cropbox(fitz.Rect(30, 20, 380, 460))
            page.set_rotation(rotation)
            doc.save(path)
            doc.close()
            locator = Locator(path)
            try:
                with patch.object(fitz.Page, 'get_text', wraps=locator.render[0].get_text) as extraction:
                    first = locator.resolve('root/pages[0]/font[0](Helvetica)')
                    second = locator.resolve('root/pages[0]/font[0](Helvetica)')
                self.assertEqual(first, second)
                self.assertEqual(extraction.call_count, 1)
                box = first[0]['rects'][0]
                self.assertAlmostEqual(box[0], 50, places=3)
                self.assertAlmostEqual(box[1], 394.02, places=2)
            finally:
                locator.close()

    def test_font_homonyms_are_not_assigned_to_the_wrong_object(self):
        path = self.folder/'polices.pdf'
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((50, 100), 'Texte', fontname='helv')
        doc.save(path)
        doc.close()
        with pikepdf.open(path, allow_overwriting_input=True) as pdf:
            original = next(iter(pdf.pages[0].Resources.Font.values()))
            duplicate = pdf.make_indirect(pikepdf.Dictionary(original))
            pdf.pages[0].Resources.Font['/Autre'] = duplicate
            pdf.save(path)
        locator = Locator(path)
        try:
            result = locator.resolve('root/pages[0]/font[0](Helvetica)')
            self.assertFalse(result[0]['rects'])
            self.assertIn('ambiguë', result[0]['reason'])
        finally:
            locator.close()


if __name__ == '__main__':
    unittest.main()
