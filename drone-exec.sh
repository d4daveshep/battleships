#!/bin/bash

# build / update application image
docker build -f Dockerfile.ci -t battleships:latest .

# run the CI pipeline
docker run --rm --group-add 999 -v /var/run/docker.sock:/var/run/docker.sock -v $(pwd):$(pwd) -w $(pwd) drone/cli:latest exec
