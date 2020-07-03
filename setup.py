import setuptools
from ywh2bt import (
    version as library_version,
)

with open("README.md", "r") as fh:
    long_description = fh.read()

install_requires = [
    "PyYAML==5.3.1",
    "colorama==0.4.3",
    "yeswehack==0.4",
    "jira==2.0.0",
    "html2text==2020.1.16",
    "beautifulsoup4==4.8.2",
    "coloredLogs==10.0",
    "PyGithub==1.47",
    "python-gitlab==2.1.2",
    "requests==2.23.0",
    "pyotp==2.3.0",
    "lxml==4.5.0",
]

setuptools.setup(
    name="ywh2bt",
    version=library_version,
    author="Jean Lou Hau",
    author_email="jl.hau@yeswehack.com",
    description="YesWeHack BugTracker",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://yeswehack.com",
    packages=setuptools.find_packages(),
    install_requires=install_requires,
    python_requires='>=3',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={"console_scripts": ["ywh-bugtracker=ywh2bt.ywh2bt:main"]},
)
