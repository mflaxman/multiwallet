from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="multiwallet",
    version="0.0.1",
    author="Example Author",
    author_email="author@example.com",
    description="Multisig bitcoin wallet",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mflaxman/multiwallet",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=["buidl==0.1.9"],
)
