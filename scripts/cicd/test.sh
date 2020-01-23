#!/usr/bin/env bash
# arg can be one of [py27-django111|py37-django22]

TESTENV=$1

export POSTGRES_DB=test
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=""
export POSTGRES_HOST=postgres
export POSTGRES_PORT=5432

source scripts/cicd/validate.sh

mkdir -p reports/diff_coverage

echo "Running tests for $TESTENV"
tox -e "$TESTENV"
TESTS_STATUS=$?
validate $TESTS_STATUS 0
echo "$STATE $RESULT"
./scripts/cicd/github-status.sh $STATE "$TESTENV" "${RESULT}" $DRONE_BUILD_LINK

mkdir -p "artifacts/$TESTENV"
find reports -maxdepth 1 -mindepth 1 | xargs -i mv {} "artifacts/$TESTENV";

exit $TESTS_STATUS
