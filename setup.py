import distutils
import platform
import sys
import zipfile
from pathlib import Path
from typing import Union, Sequence, Dict

from setuptools import find_packages, setup

NAME = "openopal"
EXE_NAME = "open-opal"
VERSION = "0.1.0"

required_packages = find_packages(exclude=["*demos.*", "*demos"])

with open('requirements.txt') as f:
    required = [line for line in f.read().splitlines() if not line.startswith("-")]


def zip_dir(dir: Union[Path, str], filename: Union[Path, str]):
    """Zip the provided directory without navigating to that directory using `pathlib` module"""

    # Convert to Path object
    dir = Path(dir)

    with zipfile.ZipFile(filename, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for entry in dir.rglob("*"):
            zip_file.write(entry, entry.relative_to(dir))


class Distribution(distutils.cmd.Command):
    description = "Distribute with pyinstaller"
    user_options = [
        ("zip", None, "Create a zip package"),
        ("macos-universal2", None, "Create MacOS universal2 package")
    ]

    @staticmethod
    def _create_cmd(command: str, modules: Sequence) -> Sequence[str]:
        tokens = []
        for module in modules:
            tokens.append(command)
            tokens.append(module)
        return tokens

    def run(self) -> None:
        import PyInstaller.__main__

        # find system name
        system_name = sys.platform
        system_arch = platform.machine()

        # correct system name
        if system_name.startswith("linux"):
            system_name = "linux"
        elif system_name.startswith("darwin"):
            system_name = "macosx"
        elif system_name.startswith("win"):
            system_name = "windows"

        # additional arguments
        collect_binaries_modules = ["depthai", "pyvirtualcam"]
        collect_data_modules = []
        collect_all_modules = ["nanogui", "cv2"]

        additional_files: Dict[str, str] = {}
        additional_files["README.md"] = "."

        system_asset_dir = Path(f"assets").joinpath(system_name)
        if system_asset_dir.exists():
            additional_files[str(system_asset_dir)] = "."

        # create arguments
        delimiter = ";" if sys.platform.startswith("win") else ":"
        additional_files_args = [f"{src}{delimiter}{dsc}" for src, dsc in additional_files.items()]
        arguments = [
            f"{NAME}/__main__.py",
            "--name", EXE_NAME,
            "--onefile",
            "--clean",
            "--icon=assets/open-opal.ico",
            "-y",
            *self._create_cmd("--add-data", additional_files_args),
            *self._create_cmd("--collect-binaries", collect_binaries_modules),
            *self._create_cmd("--collect-data", collect_data_modules),
            *self._create_cmd("--collect-all", collect_all_modules)
        ]

        if sys.platform == "darwin" and self.macos_universal2:
            print("building universal binary")
            arguments.append("--target-arch")
            arguments.append("universal2")

        print("Arguments: pyinstaller %s" % " ".join(arguments))
        PyInstaller.__main__.run(arguments)

        if self.zip:
            print("creating zip file...")
            build_system_info = f"{system_name}-{system_arch}".lower()
            zip_dir(f"dist/{NAME}", f"dist/{NAME}-{build_system_info}.zip")

    def initialize_options(self) -> None:
        self.zip = False
        self.macos_universal2 = False

    def finalize_options(self) -> None:
        pass


setup(
    name=NAME,
    version=VERSION,
    packages=required_packages,
    entry_points={
        'console_scripts': [
            f'{EXE_NAME} = openopal.__main__:main',
        ],
    },
    url='https://github.com/cansik/open-opal-c1',
    license='MIT License',
    author='Florian Bruggisser',
    author_email='github@broox.ch',
    description='A simple Opal C1 controller software.',
    install_requires=required,
    cmdclass={
        "distribute": Distribution,
    },
)