#!/usr/bin/env sh


set -e

vagrant up
vagrant provision
for file in setup.py requirements*.txt; do
    cat $file | vagrant ssh -- "cat > /pipeline/$file"
done
vagrant ssh -- -t 'cd /pipeline && python setup.py -v'
