#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
cd "$SCRIPT_DIR"

for i in *.es
do
  echo "$i"
  arib-es-extract "$i" > "${i}.txt"
done

