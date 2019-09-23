#!/usr/bin/env bash

STATE=$1
CONTEXT=$2
DESCRIPTION=$3
TARGET_URL=$4

if [ -n "$GITHUB_TOKEN" ]; then
  echo "Notifying GitHub"
  curl -s -k -H "Authorization: token $GITHUB_TOKEN" --request POST \
    --data "{\
      \"state\": \"${STATE}\", \
      \"context\": \"${CONTEXT}\", \
      \"description\": \"${DESCRIPTION}\", \
      \"target_url\": \"${TARGET_URL}\"}" \
    https://api.github.com/repos/$DRONE_REPO/statuses/$DRONE_COMMIT_SHA > /dev/null
else
  echo "Need GITHUB_TOKEN in order to send status to GitHub"
fi
