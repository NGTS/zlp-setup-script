#!/usr/bin/env sh


set -e

vagrant up
vagrant provision
cat setup.py | vagrant ssh -- 'cat > /pipeline/setup.py'
vagrant ssh -- -t 'cd /pipeline && python setup.py -v'
