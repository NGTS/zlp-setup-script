FROM debian

MAINTAINER Simon Walker <s.r.walker101@googlemail.com>

RUN apt-get update && apt-get install -y \
        python \
        python-pip
RUN mkdir /pipeline
ADD setup.py /pipeline/setup.py
WORKDIR /pipeline
ENTRYPOINT ["python"]
CMD ["setup.py", "-v"]
