#!/usr/bin/env bash

validate() {
  THRESHOLD=$1
  RESULT=$2
  POSTFIX=$3
  if (( $(echo "$RESULT >= $THRESHOLD" | bc -l) )); then
    STATE='success'
    RESULT="$2$POSTFIX"
  else
    STATE='error'
    RESULT="$2$POSTFIX but should be $1$POSTFIX"
  fi
}
