"""Contre-exemples ShipGuard sur les rapports et la mémoire de localisation."""
from collections import Counter
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET
from unittest.mock import patch

import pikepdf
import test_inspection as fixtures
from analyzer import fingerprint, parse_report
from locations import Locator


class ShipGuardRegressions(unittest.TestCase):
    def setUp(self):
        fixtures.InspectionTests.setUp(self)

    def tearDown(self):
        fixtures.InspectionTests.tearDown(self)

    def test_contradictory_zero_failures_cannot_be_reported_as_complete(self):
        root = ET.fromstring(fixtures.report(self.path))
        root.find('.//details').set('failedChecks', '0')
        rule = root.find('.//rule')
        rule.remove(rule.find('check'))
        with self.assertRaisesRegex(ValueError, 'incohérent'):
            parse_report(ET.tostring(root), self.path)

    def test_selected_pdf_is_hashed_at_most_once_for_foreign_jobs(self):
        root = ET.fromstring(fixtures.report(self.path))
        jobs = root.find('jobs')
        for index in range(10):
            foreign = self.folder/f'autre-{index}.pdf'
            foreign.write_bytes(bytes([index])*self.path.stat().st_size)
            job = ET.SubElement(jobs, 'job')
            item = ET.SubElement(job, 'item', size=str(foreign.stat().st_size))
            ET.SubElement(item, 'name').text = str(foreign)
        with patch('analyzer.fingerprint', wraps=fingerprint) as digest:
            result = parse_report(ET.tostring(root), self.path)
        counts = Counter(Path(call.args[0]).resolve() for call in digest.call_args_list)
        self.assertLessEqual(counts[self.path.resolve()], 1)
        self.assertEqual(result['failedChecks'], 1)

    def test_text_cache_does_not_retain_raster_payloads(self):
        with pikepdf.open(self.path, allow_overwriting_input=True) as pdf:
            page = pdf.pages[0]
            page.Resources.Font = pikepdf.Dictionary(F1=pikepdf.Dictionary(
                Type=pikepdf.Name.Font, Subtype=pikepdf.Name.Type1, BaseFont=pikepdf.Name.Helvetica))
            page.obj['/Contents'] = pdf.make_stream(page.Contents.read_bytes()+b'\nBT /F1 12 Tf 50 200 Td (Texte) Tj ET')
            pdf.save(self.path)
        locator = Locator(self.path)
        try:
            self.assertEqual(len(locator.render[0].get_images()), 1)
            result = locator.resolve('root/pages[0]/font[0](Helvetica)')
            self.assertTrue(result[0]['rects'])
            self.assertTrue(all(block['type'] == 0 for block in locator.text_cache[1]))
            self.assertFalse(any('image' in block for block in locator.text_cache[1]))
        finally:
            locator.close()
