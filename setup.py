import setuptools
from pathlib import Path

here = Path(__file__).parent.resolve()

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open(here / "src" / "bookkeeper" / "VERSION", "r") as version_file:
    version = version_file.read().strip()


setuptools.setup(
    name="bookkeeper",
    version=version,
    author="Sami J. Lehtinen",
    author_email="sjl+bookkeeper@iki.fi",
    description="Small-scale bookkeeping",
    long_description=long_description,
    long_description_content_type="text/markdown",
    #url="https://github.com/pypa/sampleproject",
    packages=setuptools.find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
    install_requires=["click", "lark-parser"],
    extras_require={
        'dev': ["pytest", "tox", "tox-pyenv", "wheel"],
    },
    entry_points={
        'console_scripts': ["bookkeeper=bookkeeper.main:main"]
    },
    package_data={
        "bookkeeper": ["VERSION"]
    }

)