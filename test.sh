#!/usr/bin/env sh


set -eu

if [[ ! "$#" == 1 ]]; then
    echo "Program usage: $0 (centos|debian)" >&2
    exit 1
fi

box="$1"

vagrant up "${box}"
vagrant provision "${box}"
cat setup.py | vagrant ssh "${box}" -- "cat > /pipeline/setup.py"
echo Running test
vagrant ssh "${box}" -- -t 'cd /pipeline && time python setup.py -v'
