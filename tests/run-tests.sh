#!/bin/bash

for i in *.es
do
  echo "$i"
  arib-es-extract "$i" > "${i}.txt"
done

