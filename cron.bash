#!/bin/bash

set -u

export PATH="/usr/local/bin:/usr/bin:/usr/local/sbin:/usr/sbin:/home/centos/.local/bin:/home/centos/bin"

me=$(readlink -m "$0")
me_dir=$(dirname $me)

echo "[$me_dir]"
cd $me_dir || { echo "unable to chdir"; exit 1; }

export ACCOUNT_LIST="alpha bravo charlie"

rm -rf ~/.aws/cli/cache/
bash cloud_monitor.bash
