#!/usr/bin/env bash

bwd=$(printf "%q\n" "$(pwd)")
# echo $bwd 
# echo $1
sudo $1/bbuck.sh $bwd $1