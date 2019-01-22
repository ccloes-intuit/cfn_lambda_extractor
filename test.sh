#!/bin/bash

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

set -e

echo "Running unit tests"
python3 $DIR/cfn_lambda_extractor/test.py
