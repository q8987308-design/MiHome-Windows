"""Launch this custom build using the original application's user data."""
import os
import sys
from pathlib import Path

# mijiaAPI's logger calls stdout.isatty() at import time. pythonw has no
# console streams, so supply harmless streams before importing the library.
if sys.stdout is None:
    sys.stdout = open(os.devnull, 'w', encoding='utf-8')
if sys.stderr is None:
    sys.stderr = open(os.devnull, 'w', encoding='utf-8')

os.environ.setdefault('MIHOME_DATA_DIR', str(Path(os.environ['LOCALAPPDATA']) / 'MiHome-Windows'))

from run import main

if __name__ == '__main__':
    raise SystemExit(main())
