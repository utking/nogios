#!/bin/bash

apt-get update && apt-get upgrade -y
apt-get install -y sqlite
cp -R . /tmp/app && cd /tmp/app && \
pip3 install -r requirements.txt && \
    cp nogios/settings.example.py nogios/settings.py && \
    python3 manage.py check && \
    python3 manage.py test -v 2 && \
    python3 manage.py migrate && \
    python3 manage.py loaddata fixtures/* && \
    python3 manage.py verify
