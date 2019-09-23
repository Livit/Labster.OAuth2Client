#!/usr/bin/env bash

COVER_FAIL_UNDER=80
PYLINT_FAIL_UNDER=10
DIFF_COVER_FAIL_UNDER=95

export POSTGRES_DB=test
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=""
export POSTGRES_HOST=postgres
export POSTGRES_PORT=5432

TMPFILE=/tmp/file

source scripts/cicd/validate.sh

mkdir -p reports/diff_coverage


echo "Running tests for  py27-django111"
tox -e  py27-django111
TESTS_STATUS=$?
validate $TESTS_STATUS 0
echo "$STATE $RESULT"
./scripts/cicd/github-status.sh $STATE "tests" "${RESULT}" $DRONE_BUILD_LINK


COVERAGE=$(grep "TOTAL" $TMPFILE | awk '{print $4}' | sed 's/%//')
echo "Coverage is $COVERAGE% of $COVER_FAIL_UNDER% required"
validate $COVER_FAIL_UNDER $COVERAGE '%'
./scripts/cicd/github-status.sh $STATE "coverage" "${RESULT}" $DRONE_BUILD_LINK


DIFF_COVER=$(grep "Coverage: " $TMPFILE | awk '{print $2}' | sed 's/%//')
if [ -n "$DIFF_COVER" ]; then
  echo "Diff_cover is $DIFF_COVER% of $DIFF_COVER_FAIL_UNDER% required"
  validate $DIFF_COVER_FAIL_UNDER $DIFF_COVER '%'
  ./scripts/cicd/github-status.sh $STATE "diff coverage" "${RESULT}" $DRONE_BUILD_LINK
else
  ./scripts/cicd/github-status.sh success "diff coverage" "100%" $DRONE_BUILD_LINK
fi

if [ $(( + $TESTS_STATUS + $COVERAGE_STATUS + $DIFF_COVER_STATUS)) -gt 0 ]; then
  echo "We have something to fix"
  exit 1
fi


echo "Running tests for  py37-django22"
tox -e  py37-django22
TESTS_STATUS=$?
validate $TESTS_STATUS 0
echo "$STATE $RESULT"
./scripts/cicd/github-status.sh $STATE "tests" "${RESULT}" $DRONE_BUILD_LINK


COVERAGE=$(grep "TOTAL" $TMPFILE | awk '{print $4}' | sed 's/%//')
echo "Coverage is $COVERAGE% of $COVER_FAIL_UNDER% required"
validate $COVER_FAIL_UNDER $COVERAGE '%'
./scripts/cicd/github-status.sh $STATE "coverage" "${RESULT}" $DRONE_BUILD_LINK


DIFF_COVER=$(grep "Coverage: " $TMPFILE | awk '{print $2}' | sed 's/%//')
if [ -n "$DIFF_COVER" ]; then
  echo "Diff_cover is $DIFF_COVER% of $DIFF_COVER_FAIL_UNDER% required"
  validate $DIFF_COVER_FAIL_UNDER $DIFF_COVER '%'
  ./scripts/cicd/github-status.sh $STATE "diff coverage" "${RESULT}" $DRONE_BUILD_LINK
else
  ./scripts/cicd/github-status.sh success "diff coverage" "100%" $DRONE_BUILD_LINK
fi

if [ $(( + $TESTS_STATUS + $COVERAGE_STATUS + $DIFF_COVER_STATUS)) -gt 0 ]; then
  echo "We have something to fix"
  exit 1
fi
