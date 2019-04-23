#!/bin/bash
set -e

# Jenkins will set WORKSPACE to the top level directory that contains
# the stratis-cli git repo
if [ -z "$WORKSPACE" ]
then
    echo "Required WORKSPACE environment variable not set"
    exit 1
fi

export STRATIS_DEPS_DIR=$WORKSPACE/stratis-deps

cd $WORKSPACE

# If there is a stale STRATIS_DEPS_DIR remove it
if [ -d $STRATIS_DEPS_DIR ]
then
    rm -rf $STRATIS_DEPS_DIR
fi


mkdir $STRATIS_DEPS_DIR
cd $STRATIS_DEPS_DIR

# Clone the dependencies
git clone https://github.com/stratis-storage/dbus-python-client-gen.git
git clone https://github.com/stratis-storage/dbus-client-gen.git
git clone https://github.com/stratis-storage/into-dbus-python.git
git clone https://github.com/stratis-storage/dbus-signature-pyparsing.git
git clone https://github.com/stratis-storage/stratisd.git

if [ ! -f  /etc/dbus-1/system.d/stratisd.conf ]
then
    cp $STRATIS_DEPS_DIR/stratisd/stratisd.conf /etc/dbus-1/system.d/.
fi

cd $STRATIS_DEPS_DIR/stratisd
make build

# Set the PYTHONPATH to use the dependencies
cd $STRATIS_DEPS_DIR/dbus-client-gen
git fetch --tags
    LATEST_TAG=$(git describe --tags `git rev-list --tags --max-count=1`)
echo "checking out $LATEST_TAG"
git checkout $LATEST_TAG
cd $STRATIS_DEPS_DIR/dbus-signature-pyparsing
git pull origin master
cd $STRATIS_DEPS_DIR/dbus-python-client-gen
git pull origin master
cd $STRATIS_DEPS_DIR/into-dbus-python
git pull origin master
cd $WORKSPACE
export PYTHONPATH=src:$STRATIS_DEPS_DIR/dbus-client-gen/src:$STRATIS_DEPS_DIR/dbus-python-client-gen/src:$STRATIS_DEPS_DIR/into-dbus-python/src:$STRATIS_DEPS_DIR/dbus-signature-pyparsing/src
export STRATISD=$STRATIS_DEPS_DIR/stratisd/target/x86_64-unknown-linux-gnu/debug/stratisd
make dbus-tests
