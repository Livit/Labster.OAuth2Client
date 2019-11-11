#!/usr/bin/env bash

source ./.env

docker run --name postgres-oauth2client \
	-e "POSTGRES_DB=$POSTGRES_DB" \
	-e "POSTGRES_USER=$POSTGRES_USER" \
	-e "POSTGRES_PASSWORD=$POSTGRES_PASSWORD" \
	-p $POSTGRES_PORT:5432 \
	-d \
	postgres:9.6.9
