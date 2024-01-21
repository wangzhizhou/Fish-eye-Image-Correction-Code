FROM ubuntu:20.04

ARG DEBIAN_FRONTEND=noninteractive

ENV TZ=Etc/GMT-8

RUN apt-get update && apt-get install -y cmake git clang

COPY . /opt

WORKDIR /opt

# RUN ./build.sh