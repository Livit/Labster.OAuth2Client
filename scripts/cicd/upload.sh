#!/usr/bin/env bash

set -e
set -o pipefail

ITEM=$1

source env/bin/activate

S3_PATH="$S3_BUCKET/$DRONE_REPO_NAME/$DRONE_BUILD_NUMBER/$DRONE_COMMIT_SHA"

export AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID:-$ECR_ACCESS_KEY}"
export AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY:-$ECR_SECRET_KEY}"

echo "We are going to upload $ITEM to $S3_PATH/$ITEM"
aws s3 sync $ITEM s3://$S3_PATH

ARTIFACTS_URL="https://$ARTIFACTS_SERVER/$DRONE_REPO_NAME/$DRONE_BUILD_NUMBER/$DRONE_COMMIT_SHA/"
echo "Artifacts url: $ARTIFACTS_URL"

./scripts/cicd/github-status.sh success 'ci/cd artifacts' 'uploaded' ${ARTIFACTS_URL}
