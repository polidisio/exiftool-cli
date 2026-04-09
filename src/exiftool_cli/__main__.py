"""Entry point for exiftool-cli."""

import sys
from .cli import main, InteractiveMode

if __name__ == "__main__":
    if len(sys.argv) == 1:
        InteractiveMode().run()
    else:
        main()
