import setuptools

from os import path
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setuptools.setup(
    name="robotframework-sapguilibrary",
    version="1.0",
    author="Frank van der Kuur",
    author_email="frank.vanderkuur@closesure.nl",
    description="A Robot Framework Library for automating the SAP GUI desktop client",
    long_description=long_description,
    long_description_content_type='text/markdown',
    url="https://github.com/frankvanderkuur/robotframework-sapguilibrary",
    packages=setuptools.find_packages(),
    classifiers=(
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.6",
        "Operating System :: OS Independent",
    ),
    install_requires=["pywin32>=218", "robotframework>=2.9"]
)