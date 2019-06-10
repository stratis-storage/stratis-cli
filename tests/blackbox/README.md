The intention for the test in this directory are for verifying that a
released, packaged, and installed instance of Stratis is functional.
Thus the test assumes that the `stratisd` daemon and the `stratis` command
line are installed, although the test will start the daemon if needed.

Run the test as root and supply 3 or more block devices on the
command line that are blank for test use, eg.

```bash
# python3 stratis_cert.py -v --disk /dev/vdb --disk /dev/vdc --disk /dev/vdd
```
