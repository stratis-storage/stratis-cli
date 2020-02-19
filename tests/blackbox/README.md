The intention for the tests in this directory are for verifying that a
released, packaged, and installed instance of Stratis is functional.

Run the tests as root and supply 3 or more block devices on the
command line that are blank for test use.

The `stratisd` test may be run without the installation of the `stratis`
command line interface.

```bash
# python3 stratisd_cert.py -v --disk /dev/vdb --disk /dev/vdc --disk /dev/vdd
```

The stratis-cli test assumes that the `stratisd` daemon is installed,
although the test will start the daemon if needed.

```bash
# python3 stratis_cli_cert.py -v --disk /dev/vdb --disk /dev/vdc --disk /dev/vdd
```
