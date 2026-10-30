import sys
from pathlib import Path

# Make the service root importable (`src.…`) wherever pytest is invoked from.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
