#!/usr/bin/env bash
SCRIPT_PATH=$(realpath "$BASH_SOURCE")
PROJECT_DIR=$(dirname "$SCRIPT_PATH")
case "$1" in
*/)
    DEST_DER=$1
    ;;
*)
    DEST_DER="$1/"
    ;;
esac
for py in $PROJECT_DIR/*.py
do
  cp "$py" "$DEST_DER"
done