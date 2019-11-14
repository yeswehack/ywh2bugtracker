import setuptools
import ywh2bt

with open("README.md", "r") as fh:
    long_description = fh.read()
#
setuptools.setup(
    name="ywh2bt",
    version="0.2a4",
    author="Jean Lou Hau",
    author_email="jl.hau@yeswehack.com",
    description="YesWeHack BugTracker",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://yeswehack.com",
    packages=setuptools.find_packages(),
    install_requires=[
        "requests",
        "python-gitlab",
        "pygithub",
        "jira",
        "colorama",
        "pyotp",
        "pyyaml",
        "html2text",
        "coloredLogs",
        "yeswehack"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={"console_scripts": ["ywh-bugtracker=ywh2bt.ywh2bt:main"]},
)
