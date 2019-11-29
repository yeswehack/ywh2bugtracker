import setuptools
import ywh2bt
from ywh2bt.ywh2bt import __VERSION__

with open("README.md", "r") as fh:
    long_description = fh.read()

install_requires = [
    "requests",
    "python-gitlab",
    "pygithub",
    "jira",
    "colorama",
    "pyotp",
    "pyyaml",
    "html2text",
    "coloredLogs",
    "yeswehack",
    "beautifulsoup4",
    "lxml",
]

setuptools.setup(
    name=ywh2bt.name,
    version=__VERSION__,
    author="Jean Lou Hau",
    author_email="jl.hau@yeswehack.com",
    description="YesWeHack BugTracker",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://yeswehack.com",
    packages=setuptools.find_packages(),
    install_requires=install_requires,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={"console_scripts": ["ywh-bugtracker=ywh2bt.ywh2bt:main"]},
)
