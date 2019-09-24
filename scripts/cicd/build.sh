#!/usr/bin/env bash

PACKAGES=(
  ca-certificates
  libffi
  postgresql-client
  zlib
)

DEV_PACKAGES=(
  bc
  curl
  gcc
  git
  libffi-dev
  linux-headers
  make
  musl-dev
  postgresql-dev
  zlib-dev
)

apk add --update --no-cache ${PACKAGES[@]}
apk add --no-cache --virtual .build-dependencies -q ${DEV_PACKAGES[@]}
