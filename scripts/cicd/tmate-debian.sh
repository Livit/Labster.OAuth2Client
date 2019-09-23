#!/usr/bin/env bash

apt-get install -y openssh-server tmate
cat /dev/zero | ssh-keygen -q -N ""

echo "Starting tmate!"
tmate -S /tmp/tmate.sock new-session -d

echo "Waiting for tmate!"
tmate -S /tmp/tmate.sock wait tmate-ready

tmate -S /tmp/tmate.sock display -p '#{tmate_ssh}'

echo "Tailing /dev/null, use ssh to access container"

tail -f /dev/null
