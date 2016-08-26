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
    license='GPL 2+',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Software Development :: Libraries',
        ],
    install_requires = [
        'dbus-python'
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages("src"),
    scripts=['bin/stratis']
    )
