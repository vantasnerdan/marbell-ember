#!/usr/bin/env bash
set -euo pipefail
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
exec /usr/bin/python3 "$here/configure.py" revert "$@"
