FROM debian

MAINTAINER Simon Walker <s.r.walker101@googlemail.com>

RUN apt-get update
RUN apt-get install -y \
        git \
        python \
        python-pip
RUN mkdir -p /pipeline
ADD setup.py /pipeline/setup.py
RUN mkdir -p ~/.ssh && ssh-keyscan github.com >> ~/.ssh/known_hosts
WORKDIR /pipeline
ENTRYPOINT ["python"]
CMD ["setup.py", "-v"]
