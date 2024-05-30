FROM python:3.11

# RUN apt-get update && apt-get install gdal-bin libgdal-dev -y # only necessary for using geopandas

COPY . /repo
WORKDIR /repo
RUN pip install -r requirements.txt
ENV PYTHONPATH "${PYTHONPATH}:/repo/"
ENTRYPOINT /bin/bash
