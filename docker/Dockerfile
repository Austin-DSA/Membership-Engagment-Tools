FROM python:3

LABEL maintainer="Austin-DSA"

ARG DEBIAN_FRONTEND=noninteractive

EXPOSE 8000

COPY requirements.txt /code/

RUN pip3 install --no-cache-dir -r requirements.txt

COPY . /code/

WORKDIR /code