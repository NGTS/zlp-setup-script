FROM debian:squeeze

MAINTAINER Simon Walker s.r.walker101@googlemail.com

RUN apt-get update && apt-get install -y \
        bzip2 \
        g++ \
        gfortran \
        git \
        pkg-config \
        python \
        python-dev \
        python-pip \
        ssh \
        wget

RUN mkdir -p /pipeline
WORKDIR /pipeline
CMD ["python", "/host/setup.py"]
