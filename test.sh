#!/usr/bin/env sh


set -e

vagrant up
vagrant provision
for file in setup.py requirements*.txt; do
    echo Uploading file $file
    cat $file | vagrant ssh -- "cat > /pipeline/$file"
done
echo Running test
vagrant ssh -- -t 'cd /pipeline && python setup.py -v'
