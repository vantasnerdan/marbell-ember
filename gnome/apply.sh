#!/usr/bin/env bash
# Desktop settings/assets only; optional Shell/icon installers own their state.
set -euo pipefail
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
exec /usr/bin/python3 "$here/configure.py" apply "$@"
