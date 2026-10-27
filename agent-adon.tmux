#!/bin/sh
# TPM entrypoint: the user's border remains unchanged.
set -eu
plugin_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec "$plugin_dir/plugin/agent-adon.tmux"
