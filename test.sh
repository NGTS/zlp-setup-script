#!/usr/bin/env sh


set -e

IMAGENAME=srwalker101/pipelinetest

docker build -t ${IMAGENAME} .
docker run -t ${IMAGENAME}
