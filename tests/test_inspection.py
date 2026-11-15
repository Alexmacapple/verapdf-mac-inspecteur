"""Cas discriminants de provenance et localisation, sans PDF utilisateur."""
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from xml.sax.saxutils import escape

import pikepdf

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'worker'))
from analyzer import analyze, parse_report, fingerprint
from locations import Locator, image_rect, compose


def report(path, *, profile='PDF/UA-1 validation profile', context='', clause='7.3', test='1', size=None):
    return f'''<report><jobs><job><item size="{size if size is not None else path.stat().st_size}"><name>{escape(str(path))}</name></item>
    <validationReport profileName="{profile}" jobEndStatus="normal"><details passedChecks="3" failedChecks="1" failedRules="1">
    <rule status="failed" clause="{clause}" testNumber="{test}"><description>Exigence témoin</description>
    <check status="failed"><context>{escape(context)}</context><errorMessage>Défaut témoin</errorMessage></check>
    </rule></details></validationReport></job></jobs></report>'''.encode()


class InspectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.folder = Path(self.temp.name)
        self.path = self.folder / 'témoin & test.pdf'
        with pikepdf.new() as pdf:
            page = pdf.add_blank_page(page_size=(400, 500))
            image = pdf.make_stream(bytes([255, 0, 0]))
            image['/Type'] = pikepdf.Name('/XObject')
            image['/Subtype'] = pikepdf.Name('/Image')
            image['/Width'] = 1
            image['/Height'] = 1
            image['/ColorSpace'] = pikepdf.Name('/DeviceRGB')
            image['/BitsPerComponent'] = 8
            page.obj['/Resources'] = pikepdf.Dictionary(XObject=pikepdf.Dictionary(Im1=image))
            page.obj['/Contents'] = pdf.make_stream(b'/Figure <</MCID 0>> BDC q 80 0 0 40 20 30 cm /Im1 Do Q EMC')
            struct = pdf.make_indirect(pikepdf.Dictionary(Type=pikepdf.Name('/StructTreeRoot')))
            figure = pdf.make_indirect(pikepdf.Dictionary(Type=pikepdf.Name('/StructElem'), S=pikepdf.Name('/Figure'),
                                                       Pg=page.obj, K=pikepdf.Array([0]), P=struct))
            struct['/K'] = pikepdf.Array([figure])
            pdf.Root['/StructTreeRoot'] = struct
            annot = pdf.make_indirect(pikepdf.Dictionary(Type=pikepdf.Name('/Annot'), Subtype=pikepdf.Name('/Link'),
                                                        Rect=pikepdf.Array([150, 100, 210, 125])))
            page.obj['/Annots'] = pikepdf.Array([annot])
            pdf.save(self.path)
        with pikepdf.open(self.path) as pdf:
            self.figure_ref = pdf.Root.StructTreeRoot.K[0].objgen
            self.annot_ref = pdf.pages[0].Annots[0].objgen

    def tearDown(self):
        self.temp.cleanup()

    def test_rule_and_occurrence_are_distinct(self):
        data = parse_report(report(self.path), self.path)
        self.assertEqual((data['failedRules'], data['failedChecks'], len(data['issues'])), (1, 1, 1))
        self.assertEqual(data['issues'][0]['title'], 'Figure sans alternative')

    def test_profile_mismatch_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Profil reçu'):
            parse_report(report(self.path, profile='PDF/A-1b'), self.path)

    def test_wrong_file_and_stale_size_are_rejected(self):
        other = self.folder / 'autre.pdf'
        other.write_bytes('pas le même PDF'.encode())
        with self.assertRaisesRegex(ValueError, 'correspondant'):
            parse_report(report(other), self.path)
        with self.assertRaisesRegex(ValueError, 'taille'):
            parse_report(report(self.path, size=1), self.path)

    def test_xml_entity_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'interdite'):
            parse_report(b'<!DOCTYPE r [<!ENTITY a SYSTEM "file:///etc/passwd">]><r/>', self.path)

    def test_failures_without_details_never_look_green(self):
        xml = report(self.path)
        start, end = xml.index(b'<check '), xml.index(b'</check>')+len(b'</check>')
        with self.assertRaisesRegex(ValueError, 'sans leurs occurrences'):
            parse_report(xml[:start]+xml[end:], self.path)

    def test_malformed_marked_content_never_produces_precise_zone(self):
        with pikepdf.open(self.path, allow_overwriting_input=True) as pdf:
            pdf.pages[0].obj['/Contents'] = pdf.make_stream(b'/Figure <</MCID 0>> BDC q 80 0 0 40 20 30 cm /Im1 Do Q')
            pdf.save(self.path)
        locator = Locator(self.path)
        try:
            a, b = self.figure_ref
            result = locator.resolve(f'root/StructTreeRoot/K[0]({a} {b} obj SEFigure)')
            self.assertEqual(result[0]['rects'], [])
            self.assertEqual(result[0]['precision'], 'page')
        finally:
            locator.close()

    def test_repeated_jobs_are_ambiguous(self):
        xml = report(self.path)
        job = xml.split(b'<jobs>')[1].split(b'</jobs>')[0]
        with self.assertRaisesRegex(ValueError, 'un seul fichier'):
            parse_report(b'<report><jobs>'+job+job+b'</jobs></report>', self.path)

    def test_image_and_annotation_rectangles(self):
        locator = Locator(self.path)
        try:
            a, b = self.figure_ref
            figure = locator.resolve(f'root/StructTreeRoot/K[0]({a} {b} obj SEFigure)')
            self.assertEqual(figure[0]['page'], 1)
            self.assertEqual(figure[0]['rects'], [[20.0, 30.0, 100.0, 70.0]])
            a, b = self.annot_ref
            annotation = locator.resolve(f'root/pages[0]/annots[0]({a} {b} obj PDLinkAnnot)')
            self.assertEqual(annotation[0]['rects'], [[150.0, 100.0, 210.0, 125.0]])
        finally:
            locator.close()

    def test_global_and_invalid_page_never_get_arbitrary_zone(self):
        locator = Locator(self.path)
        try:
            self.assertEqual(locator.resolve('root/metadata[0]'), [])
            self.assertEqual(locator.resolve('root/pages[999]'), [])
            self.assertEqual(locator.resolve('root/pages[0]/contentStream[0]')[0]['rects'], [])
        finally:
            locator.close()

    def test_import_is_explicit_and_pdf_is_unchanged(self):
        before = fingerprint(self.path)
        xml = self.folder/'rapport.xml'
        xml.write_bytes(report(self.path))
        result = analyze(self.path, xml)
        self.assertFalse(result['fresh'])
        self.assertEqual(result['pdfHash'], before)
        self.assertEqual(fingerprint(self.path), before)

    def test_rotated_image_matrix(self):
        self.assertEqual(image_rect((0, 50, -20, 0, 100, 80)), [80.0, 80.0, 100.0, 130.0])
        self.assertEqual(compose((2, 0, 0, 2, 10, 5), (1, 0, 0, 1, 3, 4)), (2, 0, 0, 2, 16, 13))


if __name__ == '__main__':
    unittest.main()
