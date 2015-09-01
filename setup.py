from setuptools import setup, find_packages

setup(
    # Application name:
    name="pandanas",

    # Version number (initial):
    version="0.0.1",

    # Application author details:
    author="Shestakov Dmitriy",
    author_email="6reduk@gmail.com",

    # Packages
    packages=find_packages(),

    # Include additional files into the package
    include_package_data=True,

    # Details
    url="https://github.com/6reduk/pandanas",

    #
    license="LICENSE.txt",
    description="Micro framework for fast building unix daemon application carcass.",

    # long_description=open("README.txt").read(),

    # Dependent packages (distributions)
    install_requires=[
        "pep3143daemon",
    ],
)