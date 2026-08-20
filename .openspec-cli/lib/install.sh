#!/bin/sh
# Redirect to the canonical installer at .openspec-cli/install.sh
exec sh "$(dirname "$0")/../install.sh" "$@"
