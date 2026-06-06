import pytest
import jupytertracker
from IPython.testing.globalipapp import start_ipython

# Start the global IPython app once and keep a reference to it.
_IP = start_ipython()


@pytest.fixture(autouse=True)
def reset_tracker():
    """Reset module-level singleton and IPython execution count between tests."""
    jupytertracker.stop()
    jupytertracker._tracker = None
    if _IP is not None:
        _IP.execution_count = 1
    yield
    jupytertracker.stop()
    jupytertracker._tracker = None


@pytest.fixture
def ip():
    """Return the global IPython instance."""
    return _IP
