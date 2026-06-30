"""Root conftest — ensures the repo root is on sys.path before any suite runs.

Required for --import-mode=importlib (set in pyproject.toml so duplicate test
filenames across suites don't collide). With importlib mode, pytest does not
prepend directories to sys.path automatically, so the editable-install finder
(``__editable___wdb_0_1_0_finder``) is the only path into the packages. That
finder handles top-level packages fine, but when wdb_api.app imports wdb_router
at module level and the editable finder hasn't been triggered for that package
yet in the importlib context, the import fails. Adding the repo root here (which
runs before any conftest.py lower in the tree) ensures all packages are findable
via the plain path in every import context.
"""
import sys
from pathlib import Path

_ROOT = str(Path(__file__).resolve().parent)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
