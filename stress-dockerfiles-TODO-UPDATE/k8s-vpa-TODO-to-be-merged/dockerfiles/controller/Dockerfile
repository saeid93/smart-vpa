FROM python:3.7-alpine

MAINTAINER Alireza Karami "alireza.karami.m@gmail.com"

RUN apk --no-cache --update add gfortran build-base py3-numpy

# install required libraries
RUN pip install flask requests numpy schedule

# copy app.py into container
COPY ./ /app

# change working directory to /app
WORKDIR /app

# run the program
ENTRYPOINT python ./app.py