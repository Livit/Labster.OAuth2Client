#!/usr/bin/env bash
TESTENV=$1

pip install virtualenv
virtualenv -p python3 env
source env/bin/activate
pip install awscli==1.16.208

export S3_PATH="$S3_BUCKET/$DRONE_REPO_NAME/$DRONE_BUILD_NUMBER/$DRONE_COMMIT_SHA/$TESTENV"
export ARTIFACTS_URL="https://$ARTIFACTS_SERVER/$DRONE_REPO_NAME/$DRONE_BUILD_NUMBER/$DRONE_COMMIT_SHA/$TESTENV"

scripts/cicd/upload.sh "artifacts/$TESTENV"
