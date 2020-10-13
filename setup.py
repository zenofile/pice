#!/usr/bin/env python3

import os
import re
import setuptools

with open("README.md", "r") as f:
    readme = f.read()

with open("requirements.txt", "rt") as f:
    requirements = f.read().splitlines()

with open(os.path.join("pice", "__init__.py"), "rt") as f:
    version = re.search('__version__ = "([^"]+)"', f.read()).group(1)

setuptools.setup(
    name="pice",
    version=version,
    author="Thorsten Schubert",
    author_email="tschubert@bafh.org",
    description="Script without external dependencies for reading raspberry pi temperatures (arm, gpu) and throttling flags.",
    long_description=readme,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    install_requires=requirements,
    entry_points={"console_scripts": ["pice = pice.cli:main"]},
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: POSIX",
        "Operating System :: POSIX :: Linux",
    ],
    python_requires=">=3.7",
)
