"""``python -m knobe`` entry point -- delegates to the same argparse
dispatcher as the ``knobe`` console script (configs/pyproject ``[project.scripts]``)."""
from knobe.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
