"""Vérifie le nettoyage des seuls processus possédés par une capture."""
import importlib.util
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest

spec = importlib.util.spec_from_file_location('captures', Path(__file__).resolve().parents[1]/'scripts/captures-demo.py')
captures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(captures)


class CaptureCleanup(unittest.TestCase):
    def test_cleanup_kills_stubborn_worker_group_and_application(self):
        with tempfile.TemporaryDirectory() as folder:
            ready = Path(folder)/'ready'
            app = subprocess.Popen([sys.executable, '-c',
                'import signal,time,pathlib,sys; signal.signal(signal.SIGTERM, signal.SIG_IGN); '
                'pathlib.Path(sys.argv[1]).touch(); time.sleep(60)', str(ready)], start_new_session=True)
            try:
                deadline = time.monotonic()+5
                while not ready.exists() and time.monotonic() < deadline:
                    time.sleep(0.01)
                self.assertTrue(ready.exists())
                captures.stop_capture(app)
                self.assertEqual(app.wait(timeout=5), -signal.SIGKILL)
                self.assertIsNotNone(app.poll())
            finally:
                for process in (app,):
                    if process.poll() is None:
                        os.kill(process.pid, signal.SIGKILL)
                    process.wait(timeout=5)

    def test_swift_path_encodes_unicode_and_control_characters(self):
        path = Path('/tmp/épreuve "avec" antislash\\ et\nretour')
        literal = captures.swift_path(path)
        self.assertNotIn('é', literal)
        self.assertNotIn('\\u', literal)
        self.assertNotIn('\n', literal)


if __name__ == '__main__':
    unittest.main()
