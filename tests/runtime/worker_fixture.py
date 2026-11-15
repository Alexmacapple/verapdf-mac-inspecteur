"""Moteur synthétique pour exercer les vrais états Swift, sans validateur ni données privées."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

if os.getpgrp() != os.getpid():
    os.setsid()
parser = argparse.ArgumentParser()
parser.add_argument('--pdf', required=True)
parser.add_argument('--report')
parser.add_argument('--output-dir', required=True)
args = parser.parse_args()
pdf = Path(args.pdf)
if pdf.name.startswith('sleep'):
    program = 'import signal,time; '
    if 'stubborn' in pdf.name:
        program += 'signal.signal(signal.SIGTERM, signal.SIG_IGN); '
    program += 'time.sleep(60)'
    streams = dict(stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) if 'closed' in pdf.name else {}
    child = subprocess.Popen([sys.executable, '-c', program], **streams)
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    (Path(args.output_dir)/'enfant.pid').write_text(str(child.pid))
    time.sleep(60)
elif args.report or pdf.name.startswith('bad'):
    print(json.dumps({'error': 'Rapport incompatible : résultat précédent conservé.'}))
    sys.exit(1)
else:
    print(json.dumps(dict(profile='PDF/UA-1 validation profile', failedChecks=0, passedChecks=3,
        failedRules=0, pageCount=2, issues=[], pdfPath=str(pdf), pdfHash='témoin',
        reportPath=str(Path(args.output_dir)/'rapport-temoin.xml'), provenance='Validation témoin.',
        fresh=True, complete=True, coverage=[])))
