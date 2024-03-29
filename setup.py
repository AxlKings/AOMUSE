from setuptools import setup, find_packages
import codecs
import os

# read the contents of your README file
from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

VERSION = '0.0.9'
DESCRIPTION = 'AO Muse package'

# Setting up
setup(
    name="AOMUSE",
    version=VERSION,
    author="AxelReyesO (Axel Reyes O)",
    author_email="<axel.reyes@sansano.usm.cl>",
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=find_packages(),
    install_requires=['numpy', 'pandas', 'pony', 'astropy'],
    url="https://github.com/AxlKings/AOMUSE",
    keywords='python adaptative optics muse',
    license='MIT',
    classifiers=[
        "Development Status :: 1 - Planning",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Operating System :: Unix",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
    ]
)