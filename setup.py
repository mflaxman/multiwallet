#! /usr/bin/env bash

from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()


with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="multiwallet",
    version="0.3.6",
    author="Michael Flaxman",
    author_email="multiwallet@michaelflaxman.com",
    description="Stateless multisig bitcoin wallet",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mflaxman/multiwallet",
    entry_points={
        "console_scripts": ["multiwallet_gui=multiwallet_gui.app:main"],
    },
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=requirements,
)
