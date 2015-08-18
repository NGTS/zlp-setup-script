#!/usr/bin/env bash

set -eu

main() {
    docker run -itv ${PWD}:/host $@
}

main "$@"
