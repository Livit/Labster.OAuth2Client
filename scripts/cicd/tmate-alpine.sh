#!/usr/bin/env bash

echo http://nl.alpinelinux.org/alpine/edge/testing >> /etc/apk/repositories
apk --update add openssh-server tmate
cat /dev/zero | ssh-keygen -q -N ""

echo "Starting tmate!"
tmate -S /tmp/tmate.sock new-session -d

echo "Waiting for tmate!"
echo "Warning. There is a problem with tmate in alpine 3.9 and 3.9.2."
echo "If tmate ssh path does not appear try to change alpine image to 3.8 "

tmate -S /tmp/tmate.sock wait tmate-ready

tmate -S /tmp/tmate.sock display -p '#{tmate_ssh}'

echo "Tailing /dev/null, use ssh to access container"

tail -f /dev/null
