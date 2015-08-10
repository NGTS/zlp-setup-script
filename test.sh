#!/usr/bin/env sh


set -e

vagrant up
vagrant provision
cat setup.py | vagrant ssh -- "cat > /pipeline/setup.py"
echo Running test
vagrant ssh -- -t 'cd /pipeline && time python setup.py -v'
