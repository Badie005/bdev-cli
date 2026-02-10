"""
bdev-cli package setup.

Enables global installation via: pip install -e .
"""

from setuptools import setup, find_packages
from pathlib import Path


# Read requirements
requirements = []
req_file = Path(__file__).parent / "requirements.txt"
if req_file.exists():
    with open(req_file, "r", encoding="utf-8") as f:
        requirements = [
            line.strip()
            for line in f.readlines()
            if line.strip() and not line.startswith("#")
        ]


setup(
    name="bdev-cli",
    version="0.2.0",
    author="B.DEV",
    author_email="dev@b.dev",
    description="B.DEV Command Line Interface - Development tools and utilities",
    long_description=open("README.md", "r", encoding="utf-8").read()
    if Path("README.md").exists()
    else "B.DEV CLI",
    long_description_content_type="text/markdown",
    url="https://github.com/bdev/bdev-cli",
    packages=find_packages(exclude=["tests", "tests.*", "venv", "venv.*"]),
    python_requires=">=3.10",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-mock>=3.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "bdev=cli.main:run",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "Topic :: Software Development",
        "Topic :: Utilities",
    ],
)
