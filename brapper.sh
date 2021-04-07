#!/usr/bin/env bash

bwd=$(printf "%q\n" "$(pwd)")
cd $1
sudo ./bbuck.sh $bwd