
The intention for the test in this directory are for verifying that a
released, packaged, and installed instance of Stratis is functional.
Thus the test assumes that the `stratisd` daemon and the `stratis` command
line are installed, although the test will start the daemon if needed.
Initially this test is only expected to run for fedora packaging tests, but
we could run with Travis CI or Jenkins tests as well if
we elected to build installable packages during the CI process too.

Run the test as root and supply 3 or more block devices on the
command line that are blank for test use, eg.

```bash
# python3 stratis_cert.py -v --disk /dev/vda --disk /dev/vdb --disk /dev/vdc
```

Notes
* Some tests are expecting to fail at this time.  When the issues are corrected
the test will be updated to change its expectation.
* The test is written with the expectation that it's running on an rpm based
distribution.  To make this work on different installed distributions we need
to modify `./tests/blackbox/testlib/utils.py` function `rpm_package_version` to
work on all, to retrieve the packaged version installed.

```python
import rpm


def rpm_package_version(name):
    """
    Retrieve the version of the specified package
    :param name: Name of package
    :return: String representation of version, None if package not found.
    """
    ts = rpm.TransactionSet()
    mi = ts.dbMatch('name', name)

    for i in mi:
        return i["version"].decode("utf-8")

    return None

```
