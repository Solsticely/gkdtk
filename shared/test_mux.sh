#!/usr/bin/env bash
set -euxo pipefail
cd "$(dirname "$BASH_SOURCE")"

dbg_str="${DEBUG:-}"

pipename="/tmp/mux_test_pipe"
rm -f "$pipename"
mkfifo "$pipename"

python3 mux.py server "$dbg_str" <"$pipename" |
python3 mux.py client "$dbg_str" >"$pipename"

