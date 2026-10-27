"""The desktop shortcut uses pythonw, which has no stdout or stderr."""
import subprocess
import sys
import unittest
from pathlib import Path


class LauncherTest(unittest.TestCase):
    def test_import_succeeds_without_console_streams(self):
        result = subprocess.run([sys.executable, '-c',
            'import sys; sys.stdout=None; sys.stderr=None; import launch; '
            'assert sys.stdout is not None; assert sys.stderr is not None'],
            cwd=Path(__file__).resolve().parents[1], capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr.decode(errors='replace'))


if __name__ == '__main__':
    unittest.main()
