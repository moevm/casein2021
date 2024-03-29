FROM ubuntu:18.04
ENV LANG en_US.UTF-8
RUN apt update

# install python3.8
RUN apt install -y software-properties-common
RUN add-apt-repository -y ppa:deadsnakes/ppa
RUN apt install -y python3-pip python3.8-dev mongo-tools
RUN apt install libffi-dev

ADD . /code
WORKDIR /code
RUN python3.8 -m pip install -r src/requirements.txt
CMD cd src/ && python3.8 main.py