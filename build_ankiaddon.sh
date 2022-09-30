#!/usr/bin/env bash
SCRIPT_PATH=$(realpath "$BASH_SOURCE")
PROJECT_DIR=$(dirname "$SCRIPT_PATH")
cd "$PROJECT_DIR"
rm -f play-only-one-in-the-group.ankiaddon
zip -r play-only-one-in-the-group.ankiaddon __init__.py only_one.py only_one_qt5.py \
    only_one_qt6.py play_group.py play_only_one.css play_only_one.js
