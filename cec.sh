#!/bin/bash
DIR=$(dirname -- "$( readlink -f -- "$0"; )")

pushd $DIR
.venv/bin/python3 -m cec_control -d 1
popd
