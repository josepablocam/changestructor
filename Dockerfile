FROM ubuntu:18.04

# Basic prereqs
RUN apt update
RUN apt-get update
RUN apt-get install -y make
RUN apt-get install -y wget
RUN apt-get install -y zip
RUN apt-get install -y vim
RUN apt-get install -y git
RUN apt-get install -y curl
RUN apt-get install -y build-essential

USER root
ADD . /root/changestructor/
WORKDIR /root/changestructor/


RUN  git config --global user.email "root@chgstructor.com"
RUN  git config --global user.name "Root Docker Container"


RUN bash install.sh
RUN echo "export PATH=~/miniconda3/bin/:${PATH}" >> ~/.bashrc
RUN echo "source ~/miniconda3/etc/profile.d/conda.sh" >> ~/.bashrc
Run echo "export PATH=${PATH}:$(realpath bin/)" >> ~/.bashrc

ENTRYPOINT bash
