#!/bin/bash

username=$(cat username)

for i in *;
do
chown $username $i;
chmod a+rx $i;

done

