"""Contre-exemples de la revue Fable, conservés comme non-régressions."""
import copy
import subprocess
import sys
import unittest
import xml.etree.ElementTree as ET
from unittest.mock import patch

import pikepdf
import test_inspection as fixtures
from analyzer import analyze, parse_report
from locations import Locator


class ReviewRegressions(unittest.TestCase):
    def setUp(self):
        fixtures.InspectionTests.setUp(self)

    def tearDown(self):
        fixtures.InspectionTests.tearDown(self)

    def change(self, action):
        with pikepdf.open(self.path, allow_overwriting_input=True) as pdf:
            action(pdf, pdf.pages[0], pdf.Root.StructTreeRoot.K[0])
            pdf.save(self.path)

    def figure(self):
        locator = Locator(self.path)
        try:
            a, b = locator.pdf.Root.StructTreeRoot.K[0].objgen
            return locator.resolve(f'root/StructTreeRoot/K[0]({a} {b} obj SEFigure)')
        finally:
            locator.close()

    def test_truncation_is_measured_per_rule(self):
        root = ET.fromstring(fixtures.report(self.path))
        details = root.find('.//details')
        details.set('failedChecks', '151')
        rule = details.find('rule')
        rule.set('failedChecks', '151')
        first = rule.find('check')
        for _ in range(99):
            rule.append(copy.deepcopy(first))
        result = parse_report(ET.tostring(root), self.path)
        coverage = result['coverage'][0]
        self.assertEqual((coverage['displayed'], coverage['total']), (100, 151))
        self.assertFalse(result['complete'])

    def test_fresh_validation_requests_more_than_default_100(self):
        completed = subprocess.CompletedProcess([], 0, fixtures.report(self.path), b'')
        with patch.dict('os.environ', {'VERAPDF_COMMAND': sys.executable}), patch('analyzer.subprocess.run', return_value=completed) as run:
            analyze(self.path, output_dir=self.folder/'rapports')
        command = run.call_args.args[0]
        index = command.index('--maxfailuresdisplayed')
        self.assertGreaterEqual(int(command[index+1]), 2000)

    def test_untranslated_rule_exposes_original_requirement(self):
        result = parse_report(fixtures.report(self.path, clause='7.1', test='8'), self.path)
        issue = result['issues'][0]
        self.assertFalse(issue['translated'])
        self.assertEqual(issue['requirement'], 'Exigence témoin')

    def test_text_plus_image_is_partial(self):
        def change(pdf, page, figure):
            page.Resources['/Font'] = pikepdf.Dictionary(F1=pikepdf.Dictionary(
                Type=pikepdf.Name('/Font'), Subtype=pikepdf.Name('/Type1'), BaseFont=pikepdf.Name('/Helvetica')))
            page.obj['/Contents'] = pdf.make_stream(b'/Figure <</MCID 0>> BDC q 80 0 0 40 20 30 cm /Im1 Do Q BT /F1 12 Tf 120 100 Td (Texte utile) Tj ET EMC')
        self.change(change)
        location = self.figure()[0]
        self.assertEqual(location['precision'], 'partial')
        self.assertEqual(len(location['rects']), 1)

    def test_image_inside_form_does_not_look_fully_localized(self):
        def change(pdf, page, figure):
            form = pdf.make_stream(b'q 200 0 0 200 0 0 cm /Im1 Do Q')
            form['/Type'] = pikepdf.Name('/XObject')
            form['/Subtype'] = pikepdf.Name('/Form')
            form['/BBox'] = pikepdf.Array([0, 0, 200, 200])
            form['/Resources'] = pikepdf.Dictionary(XObject=pikepdf.Dictionary(Im1=page.Resources.XObject.Im1))
            page.Resources.XObject['/Fm'] = form
            page.obj['/Contents'] = pdf.make_stream(b'/Figure <</MCID 0>> BDC q 80 0 0 40 20 30 cm /Im1 Do Q /Fm Do EMC')
        self.change(change)
        self.assertEqual(self.figure()[0]['precision'], 'partial')

    def test_clipped_image_does_not_draw_its_unclipped_extent(self):
        self.change(lambda pdf, page, figure: page.obj.__setitem__('/Contents', pdf.make_stream(
            b'/Figure <</MCID 0>> BDC q 20 30 10 10 re W n 300 0 0 300 0 0 cm /Im1 Do Q EMC')))
        location = self.figure()[0]
        self.assertEqual(location['rects'], [])
        self.assertIn('découpe', location['reason'])

    def test_parent_page_is_not_borrowed_by_a_figure(self):
        def change(pdf, page, figure):
            del figure['/Pg']
            parent = pdf.make_indirect(pikepdf.Dictionary(S=pikepdf.Name('/Sect'), Pg=page.obj, K=pikepdf.Array([figure])))
            figure['/P'] = parent
        self.change(change)
        self.assertEqual(self.figure(), [])

    def test_missing_mcid_makes_existing_image_partial(self):
        self.change(lambda pdf, page, figure: figure.__setitem__('/K', pikepdf.Array([0, 99])))
        self.assertEqual(self.figure()[0]['precision'], 'partial')

    def test_mcr_in_another_stream_is_explicitly_partial(self):
        def change(pdf, page, figure):
            stream = pdf.make_stream(b'')
            figure['/K'] = pikepdf.Array([0, pikepdf.Dictionary(Type=pikepdf.Name('/MCR'), Pg=page.obj, Stm=stream, MCID=1)])
        self.change(change)
        self.assertEqual(self.figure()[0]['precision'], 'partial')

    def test_nested_content_limit_is_explicitly_partial(self):
        def change(pdf, page, figure):
            nested = pikepdf.Array([99])
            for _ in range(85):
                nested = pikepdf.Array([nested])
            figure['/K'] = pikepdf.Array([0, nested])
        self.change(change)
        self.assertEqual(self.figure()[0]['precision'], 'partial')

    def test_utf16_doctype_is_rejected_before_expansion(self):
        xml = '<?xml version="1.0" encoding="UTF-16"?><!DOCTYPE report [<!ENTITY t "test">]><report/>'.encode('utf-16')
        with self.assertRaisesRegex(ValueError, 'interdite'):
            parse_report(xml, self.path)

    def test_inline_image_makes_direct_image_partial(self):
        self.change(lambda pdf, page, figure: page.obj.__setitem__('/Contents', pdf.make_stream(
            b'/Figure <</MCID 0>> BDC q 80 0 0 40 20 30 cm /Im1 Do Q '
            b'q 200 0 0 200 50 200 cm BI /W 1 /H 1 /CS /RGB /BPC 8 ID \xff\x00\x00 EI Q EMC')))
        self.assertEqual(self.figure()[0]['precision'], 'partial')

    def test_object_reference_makes_direct_image_partial(self):
        def change(pdf, page, figure):
            annot = pdf.make_indirect(pikepdf.Dictionary(Type=pikepdf.Name('/Annot'),
                Subtype=pikepdf.Name('/Link'), Rect=pikepdf.Array([50, 300, 350, 400])))
            figure['/K'] = pikepdf.Array([0, pikepdf.Dictionary(Type=pikepdf.Name('/OBJR'), Obj=annot)])
        self.change(change)
        self.assertEqual(self.figure()[0]['precision'], 'partial')

    def test_full_page_rectangle_clip_keeps_contained_image(self):
        self.change(lambda pdf, page, figure: page.obj.__setitem__('/Contents', pdf.make_stream(
            b'q 0 0 400 500 re W n /Figure <</MCID 0>> BDC q 80 0 0 40 20 30 cm /Im1 Do Q EMC Q')))
        location = self.figure()[0]
        self.assertEqual(location['precision'], 'image')
        self.assertEqual(location['rects'], [[20, 30, 100, 70]])

    def test_nonrectangular_clip_does_not_keep_image_bbox(self):
        self.change(lambda pdf, page, figure: page.obj.__setitem__('/Contents', pdf.make_stream(
            b'q 0 0 m 400 0 l 200 500 l h W n /Figure <</MCID 0>> BDC q 80 0 0 40 20 30 cm /Im1 Do Q EMC Q')))
        self.assertEqual(self.figure()[0]['rects'], [])

    def test_path_extended_after_clip_operator_is_not_treated_as_rectangle(self):
        self.change(lambda pdf, page, figure: page.obj.__setitem__('/Contents', pdf.make_stream(
            b'q 0 0 400 500 re W* 10 20 100 100 re n /Figure <</MCID 0>> BDC '
            b'q 80 0 0 40 20 30 cm /Im1 Do Q EMC Q')))
        self.assertEqual(self.figure()[0]['rects'], [])

    def test_text_clipping_outside_figure_also_suppresses_image_rectangle(self):
        def change(pdf, page, figure):
            page.Resources['/Font'] = pikepdf.Dictionary(F1=pikepdf.Dictionary(
                Type=pikepdf.Name('/Font'), Subtype=pikepdf.Name('/Type1'), BaseFont=pikepdf.Name('/Helvetica')))
            page.obj['/Contents'] = pdf.make_stream(
                b'q BT /F1 12 Tf 7 Tr 0 0 Td (x) Tj ET /Figure <</MCID 0>> BDC '
                b'q 80 0 0 40 20 30 cm /Im1 Do Q EMC Q')
        self.change(change)
        self.assertEqual(self.figure()[0]['rects'], [])


if __name__ == '__main__':
    unittest.main()
