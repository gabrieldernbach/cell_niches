FROM python:3.11

RUN apt-get update && apt-get install gdal-bin libgdal-dev -y

COPY . /repo
WORKDIR /repo
RUN pip install -r requirements.txt
ENTRYPOINT /bin/bash
