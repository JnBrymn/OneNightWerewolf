#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/../frontend"
npm run typecheck
npm test -- --watchAll=false "$@"
