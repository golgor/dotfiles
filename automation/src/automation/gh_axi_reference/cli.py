"""Refresh the private gh-axi skill's installed command reference."""

import sys

from automation import AutomationError
from automation.gh_axi_reference.reference import refresh
from automation.process import git_root


def main(argv: list[str] | None = None) -> int:
    del argv
    try:
        output = refresh(git_root())
    except AutomationError as error:
        print(f"refresh-gh-axi-reference: {error}", file=sys.stderr)
        return 1
    print(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
