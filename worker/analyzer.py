"""Contrôle PDF/UA-1 et lecture de rapports, sans écrire dans le PDF."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

from locations import Locator

MAX_XML = 64 * 1024 * 1024
MAX_ISSUES = 2000


def natural(value, label):
    try:
        if value is None or not re.fullmatch(r'\d+', str(value)):
            raise ValueError()
        return int(value)
    except ValueError as error:
        raise ValueError(f'Rapport XML : {label} absent ou non numérique.') from error


class SafeTreeBuilder(ET.TreeBuilder):
    def doctype(self, name, pubid, system):
        raise ValueError('Rapport XML contenant une déclaration interdite.')


def fingerprint(path):
    with open(path, 'rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def explain(clause, test):
    known = {
        ('7.3', '1'): ('Figure sans alternative', 'Décrire l’information de l’image. Si elle est purement décorative, confirmer son classement comme artefact dans l’outil de correction.'),
        ('7.21.4.1', '1'): ('Police non incorporée', 'Réexporter en incorporant cette police, ou la remplacer dans le document source par une police incorporable.'),
        ('7.18.5', '2'): ('Lien sans description', 'Renseigner une description explicite dans l’entrée Contents de l’annotation de lien.'),
        ('7.18.1', '2'): ('Annotation sans description', 'Décrire l’annotation dans Contents ou dans l’alternative de sa balise. Le même lien peut déclencher une autre règle.'),
        ('5', '1'): ('Identification PDF/UA absente', 'Finaliser l’identification PDF/UA dans les métadonnées après correction et examen du document. Ajouter la déclaration ne corrige pas les autres défauts.'),
    }
    return known.get((clause, test), (f'Exigence PDF/UA {clause}, test {test}',
                    'Consulter l’exigence et son message technique ci-dessous ; confirmer la correction dans l’outil source ou sur une copie.'))


def parse_report(xml, pdf_path, pdf_hash=None):
    if len(xml) > MAX_XML or re.search(br'<!\s*(DOCTYPE|ENTITY)\b', xml, re.I):
        raise ValueError('Rapport XML trop volumineux ou contenant une déclaration interdite.')
    try:
        root = ET.fromstring(xml, parser=ET.XMLParser(target=SafeTreeBuilder()))
    except ET.ParseError as error:
        raise ValueError('Rapport XML mal formé ou incomplet.') from error
    for element in root.iter():
        element.tag = element.tag.rsplit('}', 1)[-1]
    jobs = root.findall('.//job')
    matches = []
    selected = pdf_path.resolve()
    selected_size = selected.stat().st_size
    digests = {selected: pdf_hash} if pdf_hash else {}

    def digest(path):
        path = path.resolve()
        if path not in digests:
            digests[path] = fingerprint(path)
        return digests[path]
    for job in jobs:
        name = job.findtext('./item/name', '')
        candidate = Path(name).expanduser()
        same_file = candidate.is_file() and (candidate.resolve() == selected or
                    (candidate.stat().st_size == selected_size and digest(candidate) == digest(selected)))
        item = job.find('item')
        moved = (bool(name) and not candidate.exists() and candidate.name == pdf_path.name and
                 item is not None and item.get('size') == str(selected_size))
        if same_file or moved:
            matches.append(job)
    if len(matches) != 1:
        raise ValueError('Ce rapport ne désigne pas un seul fichier correspondant au PDF ouvert. Relancer une analyse pour produire le bon rapport.')
    job = matches[0]
    report = job.find('validationReport')
    if report is None or report.get('jobEndStatus') != 'normal':
        raise ValueError('Validation absente ou interrompue : aucun diagnostic complet disponible.')
    profile = report.get('profileName', '')
    if profile != 'PDF/UA-1 validation profile':
        raise ValueError(f'Profil reçu : {profile}. Cet inspecteur attend PDF/UA-1 ; relancer une analyse.')
    declared_size = natural(job.find('item').get('size'), 'taille du fichier')
    if declared_size != pdf_path.stat().st_size:
        raise ValueError('La taille du PDF diffère de celle déclarée dans le rapport. Relancer une analyse.')
    details = report.find('details')
    if details is None:
        raise ValueError('Rapport sans résultats détaillés.')
    failed = natural(details.get('failedChecks'), 'nombre d’échecs')
    passed = natural(details.get('passedChecks'), 'nombre de contrôles réussis')
    failed_rules = natural(details.get('failedRules'), 'nombre de règles en échec')
    failed_nodes = details.findall("rule[@status='failed']")
    if ((failed == 0) != (failed_rules == 0) or failed_rules > failed or
            len(failed_nodes) > failed_rules or (failed == 0 and failed_nodes)):
        raise ValueError('Rapport incohérent : les compteurs et les règles en échec se contredisent.')
    issues, coverage = [], []
    for rule in details.findall('rule'):
        if rule.get('status') != 'failed':
            continue
        clause, test = rule.get('clause', ''), rule.get('testNumber', '')
        title, advice = explain(clause, test)
        start = len(issues)
        for check in rule.findall('check'):
            if check.get('status') != 'failed' or len(issues) >= MAX_ISSUES:
                continue
            issues.append(dict(id=str(len(issues)), clause=clause, test=test, title=title,
                               translated=not title.startswith('Exigence PDF/UA'),
                               advice=advice, requirement=rule.findtext('description', ''),
                               message=check.findtext('errorMessage', ''),
                               context=check.findtext('context', ''), locations=[]))
        observed = len(rule.findall("check[@status='failed']"))
        total = natural(rule.get('failedChecks', str(observed)), 'nombre d’échecs de la règle')
        if total < observed or (rule.get('failedChecks') is not None and total == 0):
            raise ValueError('Rapport incohérent : le total d’une règle échouée contredit ses occurrences.')
        coverage.append(dict(clause=clause, test=test, displayed=len(issues)-start, total=total))
    reported = sum(c['total'] for c in coverage)
    if reported > failed or (len(failed_nodes) == failed_rules and
            all(rule.get('failedChecks') is not None for rule in failed_nodes) and reported != failed):
        raise ValueError('Rapport incohérent : le total des occurrences diffère du total déclaré.')
    if failed > 0 and not issues:
        raise ValueError('Ce rapport signale des échecs sans leurs occurrences détaillées. Relancer une analyse.')
    return dict(profile=profile, failedChecks=failed,
                coverage=coverage, complete=len(failed_nodes) == failed_rules and len(issues) == failed and
                all(c['displayed'] == c['total'] for c in coverage),
                passedChecks=passed, failedRules=failed_rules, issues=issues)


def analyze(pdf_path, report_path=None, output_dir=None):
    pdf_path = Path(pdf_path).resolve(strict=True)
    if pdf_path.stat().st_size > 256 * 1024 * 1024:
        raise ValueError('PDF au-delà de la limite locale de 256 Mio.')
    before = fingerprint(pdf_path)
    generated = report_path is None
    if generated:
        executable = Path(os.environ.get('VERAPDF_COMMAND', '/opt/homebrew/bin/verapdf'))
        if not executable.is_file():
            raise ValueError('veraPDF est introuvable. Installer le validateur ou importer un rapport XML existant.')
        completed = subprocess.run([str(executable), '--format', 'xml', '--flavour', 'ua1',
                                    '--maxfailuresdisplayed', str(MAX_ISSUES), str(pdf_path)],
                                   capture_output=True, timeout=120)
        xml = completed.stdout
        if not xml.strip():
            raise ValueError('veraPDF n’a produit aucun rapport XML exploitable.')
        directory = Path(output_dir) if output_dir else Path(tempfile.mkdtemp(prefix='inspecteur-verapdf-'))
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        report_path = directory / f'{before[:12]}-{os.urandom(6).hex()}.xml'
        report_path.write_bytes(xml)
        report_path.chmod(0o600)
    else:
        report_path = Path(report_path).resolve(strict=True)
        if report_path.stat().st_size > MAX_XML:
            raise ValueError('Rapport XML au-delà de 64 Mio.')
        xml = report_path.read_bytes()
    result = parse_report(xml, pdf_path, pdf_hash=before)
    locator = Locator(pdf_path)
    try:
        for issue in result['issues']:
            issue['locations'] = locator.resolve(issue['context'])
        result['pageCount'] = len(locator.pdf.pages)
    finally:
        locator.close()
    if before != fingerprint(pdf_path):
        raise ValueError('Le PDF a changé pendant le contrôle ; relancer sur un fichier stable.')
    result.update(pdfPath=str(pdf_path), pdfHash=before, reportPath=str(report_path),
                  provenance='Validation fraîche sur ce PDF ; empreinte inchangée.' if generated else
                  'Rapport importé : association par fichier et taille, sans preuve des octets au moment du contrôle.',
                  fresh=generated)
    return result


def main():
    # Isolation du moteur et de veraPDF pour une annulation sans processus orphelin.
    if os.getpgrp() != os.getpid():
        os.setsid()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pdf', required=True)
    parser.add_argument('--report')
    parser.add_argument('--output-dir')
    args = parser.parse_args()
    try:
        result = analyze(args.pdf, args.report, args.output_dir)
        print(json.dumps(result, ensure_ascii=False, allow_nan=False))
    except Exception as error:
        if isinstance(error, subprocess.TimeoutExpired):
            message = 'veraPDF a dépassé le délai de validation de 120 secondes.'
        elif isinstance(error, FileNotFoundError):
            message = 'Un fichier ou le validateur est introuvable. Vérifier les chemins sélectionnés.'
        elif isinstance(error, PermissionError):
            message = 'Accès refusé à un fichier. Vérifier les droits de lecture et d’écriture.'
        elif isinstance(error, ValueError):
            message = str(error)
        else:
            message = 'Le document ou le rapport n’a pas pu être lu. Vérifier son intégrité et les dépendances installées.'
        print(json.dumps({'error': message}, ensure_ascii=False))
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
