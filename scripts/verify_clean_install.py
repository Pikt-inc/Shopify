from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import venv
from pathlib import Path
from typing import Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_IMPORT_SMOKE = (
    "import shopify_sdk; "
    "import shopify_sdk.webhooks; "
    "from shopify_sdk import store; "
    "assert store is not None"
)


def run(command: Sequence[str], working_directory: Path) -> None:
    """Run a command and surface failures to the clean-install caller.

    :param command: Command and argument sequence to execute.
    :param working_directory: Directory used as the command working directory.
    """
    subprocess.run(command, check=True, cwd=working_directory)


def virtualenv_python(virtualenv_directory: Path) -> Path:
    """Return the Python executable path for a virtual environment.

    :param virtualenv_directory: Created virtual environment directory.
    :returns: Virtual environment Python executable.
    """
    scripts_directory = "Scripts" if os.name == "nt" else "bin"
    executable_name = "python.exe" if os.name == "nt" else "python"
    return virtualenv_directory / scripts_directory / executable_name


def package_wheel(wheelhouse: Path) -> Path:
    """Return the built SDK wheel from a wheelhouse.

    :param wheelhouse: Directory populated by ``pip wheel``.
    :returns: Built ``shopify_sdk`` wheel.
    :raises RuntimeError: If the SDK wheel cannot be located.
    """
    candidates = sorted(wheelhouse.glob("shopify_sdk-*.whl"))
    if not candidates:
        raise RuntimeError("Clean-install verification could not locate the SDK wheel.")
    return candidates[-1]


def verify_clean_install() -> None:
    """Build, install, and import the SDK from an isolated temporary environment."""
    with tempfile.TemporaryDirectory(prefix="shopify-sdk-clean-install-") as directory:
        temporary_directory = Path(directory)
        wheelhouse = temporary_directory / "wheelhouse"
        environment_directory = temporary_directory / "environment"
        import_directory = temporary_directory / "import-check"
        wheelhouse.mkdir()
        import_directory.mkdir()

        run(
            [
                sys.executable,
                "-m",
                "pip",
                "wheel",
                "--wheel-dir",
                str(wheelhouse),
                str(PROJECT_ROOT),
            ],
            PROJECT_ROOT,
        )
        venv.EnvBuilder(with_pip=True).create(environment_directory)
        python = virtualenv_python(environment_directory)
        run(
            [
                str(python),
                "-m",
                "pip",
                "install",
                "--no-index",
                "--find-links",
                str(wheelhouse),
                str(package_wheel(wheelhouse)),
            ],
            import_directory,
        )
        run([str(python), "-I", "-c", PACKAGE_IMPORT_SMOKE], import_directory)


if __name__ == "__main__":
    verify_clean_install()
