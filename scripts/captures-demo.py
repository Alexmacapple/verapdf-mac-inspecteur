"""Produit deux captures réelles à partir d’un PDF fictif, sans document utilisateur."""
import json
from pathlib import Path
import plistlib
import shutil
import subprocess
import sys
import tempfile
import time

import pikepdf
from pikepdf import Array, Dictionary, Name, String

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'docs/images'


def text(x, y, size, value, color='0.12 0.17 0.24'):
    value = value.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')
    return f'BT /F1 {size} Tf {color} rg {x} {y} Td ({value}) Tj ET\n'


def create_pdf(path):
    with pikepdf.new() as pdf:
        font = pdf.make_indirect(Dictionary(Type=Name.Font, Subtype=Name.Type1,
            BaseFont=Name.Helvetica, Encoding=Name.WinAnsiEncoding))
        structure = pdf.make_indirect(Dictionary(Type=Name.StructTreeRoot))
        document = pdf.make_indirect(Dictionary(Type=Name.StructElem, S=Name.Document, P=structure, K=Array()))
        structure.K = Array([document])
        parents = Array()
        pages = []
        for index in range(2):
            page = pdf.add_blank_page(page_size=(612, 792))
            page.Resources = Dictionary(Font=Dictionary(F1=font))
            page.obj['/StructParents'] = index
            page.obj['/Tabs'] = Name.S
            paragraph = pdf.make_indirect(Dictionary(Type=Name.StructElem, S=Name.P,
                P=document, Pg=page.obj, K=0))
            document.K.append(paragraph)
            mapping = pdf.make_indirect(Array([paragraph]))
            parents.extend([index, mapping])
            pages.append((page, mapping))
        image = pdf.make_stream(bytes(
            channel for y in range(220) for x in range(510)
            for channel in ((49, 108, 180) if (35 <= y < 75 and 100 <= x < 250) or
                           (95 <= y < 135 and 100 <= x < 360) or
                           (155 <= y < 195 and 100 <= x < 450) else (240, 245, 250))))
        for key, value in dict(Type=Name.XObject, Subtype=Name.Image, Width=510,
                               Height=220, ColorSpace=Name.DeviceRGB, BitsPerComponent=8).items():
            image['/'+key] = value
        page, mapping = pages[1]
        page.Resources.XObject = Dictionary(Im1=image)
        figure = pdf.make_indirect(Dictionary(Type=Name.StructElem, S=Name.Figure,
            P=document, Pg=page.obj, K=1))
        link = pdf.make_indirect(Dictionary(Type=Name.StructElem, S=Name.Link, P=document, Pg=page.obj))
        annotation = pdf.make_indirect(Dictionary(Type=Name.Annot, Subtype=Name.Link,
            Rect=Array([46, 149, 355, 174]), F=4, StructParent=2,
            A=Dictionary(S=Name.URI, URI=String('https://example.invalid/ressource'))))
        link.K = Array([2, Dictionary(Type=Name.OBJR, Pg=page.obj, Obj=annotation)])
        page.obj['/Annots'] = Array([annotation])
        mapping.extend([figure, link])
        document.K.extend([figure, link])
        parents.extend([2, link])
        structure.ParentTree = pdf.make_indirect(Dictionary(Nums=parents))
        pdf.Root.StructTreeRoot = structure
        pdf.Root.MarkInfo = Dictionary(Marked=True)
        pdf.Root.Lang = String('fr-FR')
        pdf.Root.ViewerPreferences = Dictionary(DisplayDocTitle=True)
        pdf.docinfo['/Title'] = 'Exemple pédagogique public'
        for index, (page, _) in enumerate(pages):
            content = '/Artifact BMC 0.12 0.27 0.47 rg 0 688 612 104 re f EMC\n/P <</MCID 0>> BDC\n'
            content += text(46, 739, 23, 'Un PDF à examiner', '1 1 1')
            content += text(46, 710, 12, 'Exemple pédagogique entièrement fictif', '1 1 1')
            if index == 0:
                content += text(46, 626, 21, 'Préparer la correction')
                for y, line in [(585, '1. Choisir une erreur dans la liste.'),
                                (552, '2. Consulter sa page et son explication.'),
                                (519, '3. Corriger dans le document source.'),
                                (463, 'La page suivante contient un graphique et un lien.'),
                                (430, 'Des défauts sont laissés volontairement pour la démonstration.')]:
                    content += text(46, y, 14, line)
            else:
                content += text(46, 626, 22, 'Participation aux ateliers')
                content += text(46, 595, 13, 'Graphique fictif : alternative textuelle à préparer.')
                content += text(46, 554, 14, 'Atelier A : 15 personnes')
                content += text(46, 527, 14, 'Atelier B : 26 personnes')
                content += text(46, 500, 14, 'Atelier C : 35 personnes')
                content += 'EMC\n/Figure <</MCID 1>> BDC q 510 0 0 220 46 245 cm /Im1 Do Q EMC\n'
                content += '/Artifact BMC\n' + text(46, 209, 12, 'Données inventées pour illustrer le diagnostic.') + 'EMC\n'
                content += '/Link <</MCID 2>> BDC\n' + text(46, 158, 15, 'Ressource de démonstration', '0.12 0.35 0.70')
            content += 'EMC\n/Artifact BMC\n' + text(46, 52, 10, 'Document de démonstration - aucune donnée personnelle.') + 'EMC\n'
            page.obj['/Contents'] = pdf.make_stream(content.encode('cp1252'))
        pdf.save(path)


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='verapdf-captures-') as temporary:
        work = Path(temporary)
        demo = work/'Exemple-public.pdf'
        create_pdf(demo)
        app = work/'veraPDF Mac Inspecteur Démo.app'
        resources = app/'Contents/Resources'
        executable = app/'Contents/MacOS/InspecteurVeraPDF'
        resources.mkdir(parents=True)
        executable.parent.mkdir(parents=True)
        for source in (ROOT/'worker').glob('*.py'):
            shutil.copy(source, resources/source.name)
        info = dict(CFBundleIdentifier='org.alex.verapdf-inspecteur.captures',
            CFBundleName='veraPDF Mac Inspecteur', CFBundleExecutable=executable.name,
            CFBundlePackageType='APPL', PythonExecutable=sys.executable)
        (app/'Contents/Info.plist').write_bytes(plistlib.dumps(info))
        source = (ROOT/'Sources/App.swift').read_text()
        needle = '        guard let index = args.firstIndex(of: "--capture")'
        assert needle in source
        selection = '''        if let i = args.firstIndex(of: "--demo-rule"), args.indices.contains(i+1) {
            guard let issue = self.inspection?.issues.first(where: { "\\($0.clause)-\\($0.test)" == args[i+1] }) else { return }
            self.select(issue.id)
        }
'''
        source = source.replace(needle, selection+needle, 1)
        needle = '                    model.run(pdf: pdf, report: report)'
        assert needle in source
        source = source.replace(needle, '                    model.reportFolder = URL(fileURLWithPath: '+json.dumps(str(work/'rapports'))+')\n'+needle)
        entry = work/'App.swift'
        entry.write_text(source)
        sources = [str(p) for p in (ROOT/'Sources').glob('*.swift') if p.name != 'App.swift']
        subprocess.run(['xcrun', 'swiftc', '-swift-version', '5', '-O', '-D', 'INSPECTOR_DIAGNOSTICS',
            '-framework', 'SwiftUI', '-framework', 'AppKit', '-framework', 'PDFKit',
            *sources, str(entry), '-o', str(executable)], check=True)
        subprocess.run(['codesign', '--force', '--sign', '-', str(app)], check=True)
        for rule, name in [('7.3-1', 'figure-sans-alternative.png'), ('7.18.5-2', 'lien-sans-description.png')]:
            shot = OUTPUT/name
            capture = work/name
            process = subprocess.Popen([str(executable), '--pdf', str(demo), '--capture', str(capture), '--demo-rule', rule])
            try:
                deadline = time.monotonic()+90
                while not capture.exists() and time.monotonic() < deadline and process.poll() is None:
                    time.sleep(0.2)
                if not capture.exists():
                    raise RuntimeError('La capture réelle n’a pas été produite : '+rule)
                metadata = json.loads(Path(str(capture)+'.json').read_text())
                assert metadata['page'] == 2 and metadata['zones'] > 0, metadata
                shutil.copy(capture, shot)
                print(shot.relative_to(ROOT), metadata)
            finally:
                process.terminate()
                process.wait(timeout=10)


if __name__ == '__main__':
    main()
