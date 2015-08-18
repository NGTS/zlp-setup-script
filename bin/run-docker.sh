#!/usr/bin/env bash

set -eu

main() {
    docker run -v ${PWD}:/host $@
}

main "$@"
