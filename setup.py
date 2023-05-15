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


with open(local_file("src/stratis_cli/_version.py"), encoding="utf-8") as o:
    exec(o.read())  # pylint: disable=exec-used #nosec B102

with open(local_file("README.rst"), encoding="utf-8") as o:
    long_description = o.read()

setuptools.setup(
    name="stratis-cli",
    version=__version__,  # pylint: disable=undefined-variable
    author="Anne Mulhern",
    author_email="amulhern@redhat.com",
    description="Stratis CLI",
    long_description=long_description,
    platforms=["Linux"],
    license="Apache-2.0",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
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
        "justbytes>=0.14",
        "packaging",
        "psutil",
        "python-dateutil",
        "wcwidth",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages("src"),
    scripts=["bin/stratis"],
)
