"""
Python packaging file for setup tools.
"""

# isort: STDLIB
import os

# isort: THIRDPARTY
import setuptools


def local_file(name):
    """
    Function to obtain the relative path of a filename.
    """
    return os.path.relpath(os.path.join(os.path.dirname(__file__), name))


README = local_file("README.rst")

with open(local_file("src/stratis_cli/_version.py")) as o:
    exec(o.read())  # pylint: disable=exec-used

setuptools.setup(
    name="stratis-cli",
    version=__version__,  # pylint: disable=undefined-variable
    author="Anne Mulhern",
    author_email="amulhern@redhat.com",
    description="prototype stratis cli",
    long_description=open(README, encoding="utf-8").read(),
    platforms=["Linux"],
    license="Apache 2.0",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Topic :: Software Development :: Libraries",
        "Topic :: System :: Filesystems",
        "Topic :: Systems Administration",
    ],
    install_requires=[
        "dbus-client-gen>=0.4",
        "dbus-python-client-gen>=0.7",
        "justbytes==0.11",
        "python-dateutil",
        "semantic_version",
        "wcwidth",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages("src"),
    scripts=["bin/stratis"],
)
