import os
import sys
import setuptools
if sys.version_info[0] < 3:
    from codecs import open


def local_file(name):
    return os.path.relpath(os.path.join(os.path.dirname(__file__), name))


README = local_file("README.rst")

with open(local_file("src/stratis_cli/_version.py")) as o:
    exec(o.read())

setuptools.setup(
    name='stratis-cli',
    version=__version__,
    author='Anne Mulhern',
    author_email='amulhern@redhat.com',
    description='prototype stratis cli',
    long_description=open(README, encoding='utf-8').read(),
    platforms=['Linux'],
    license='Apache 2.0',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha', 'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: POSIX :: Linux', 'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Software Development :: Libraries',
        'Topic :: System :: Filesystems', 'Topic :: Systems Administration'
    ],
    install_requires=[
        'dbus-client-gen>=0.4', 'dbus-python-client-gen>=0.5',
        'python-dateutil', 'wcwidth'
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages("src"),
    scripts=['bin/stratis'])
