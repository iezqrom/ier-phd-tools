#!/bin/bash

username=$(cat $2/username)
# echo $username

for i in $1/*;
do
# echo $1
chown $username $i;
chmod a+rx $i;
done


# for i in ./*;
# do
# # echo $1
# chown $username $i;
# chmod a+rx $i;
# done