FROM ubuntu:20.04

ARG DEBIAN_FRONTEND=noninteractive

ENV TZ=Etc/GMT-8

RUN apt-get update && apt-get install -y cmake git clang vim

COPY . /opt

WORKDIR /opt

ENTRYPOINT [ "/bin/bash" ]

CMD [ "build.sh" ]