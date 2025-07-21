# DEPRECATED: This file is kept for backward compatibility.
# The project now uses Pixi for dependency management.
# See pixi.toml and MIGRATION.md for more information.

import re
from pathlib import Path

from setuptools import find_packages, setup


def get_version():
    with open("vecorel_cli/version.py", "r") as file:
        content = file.read()
        return re.search(r'__version__\s*=\s*"([^"]+)"', content)[1]


def get_description():
    this_directory = Path(__file__).parent
    return (this_directory / "README.md").read_text()


setup(
    name="vecorel-cli",
    version=get_version(),
    license="Apache-2.0",
    description="CLI tools such as validation and file format conversion for vecorel.",
    long_description=get_description(),
    long_description_content_type="text/markdown",
    author="Matthias Mohr",
    url="https://github.com/vecorel/cli",
    install_requires=[
        "jsonschema[format]>=4.20",
        "pyyaml>=6.0",
        "pyarrow>=14.0",
        "fsspec>=2024.0",
        "click>=8.1",
        "geopandas>=1.0.0",
        "requests>=2.30",
        #   "aiohttp>=3.9",
        "shapely>=2.0",
        "numpy>=1.20.0",
        "py7zr>=0.21.0",
        "rarfile>=4.0",
        "semantic-version>=2.10.0",
        "json-stream>=2.3.0",
    ],
    extras_require={
        # Optional dependencies for datasets converters go here
    },
    packages=find_packages(),
    package_data={"vecorel_cli": []},
    entry_points={"console_scripts": ["vec=vecorel_cli:vecorel_cli"]},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3",
    ],
)
