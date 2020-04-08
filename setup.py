import setuptools
import ywh2bt
from ywh2bt.ywh2bt import __VERSION__

with open("README.md", "r") as fh:
    long_description = fh.read()

install_requires = [
    "requests==2.23.0",
    "python-gitlab==2.1.2",
    "pyyaml==5.3.1",
    "pygithub==1.47",
    "jira==2.0.0",
    "html2text==2020.1.16",
    "colorama==0.4.3",
    "pyotp==2.3.0",
    "coloredLogs==10.0",
    "yeswehack",
    "beautifulsoup4==4.8.2",
    "lxml==4.5.0",
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
