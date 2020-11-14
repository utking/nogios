#!/bin/bash

cp -R . /tmp/app && cd /tmp/app/web && \
  npm install && \
  npm run build
