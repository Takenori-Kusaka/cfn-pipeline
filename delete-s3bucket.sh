#!/usr/bin/bash

bucket_name="$1"

# Abort the process if there is no argument
if [ $# != 1 ]; then
    echo "Please enter an argument."
    exit 1
fi

# Get the list of buckets to be deleted
backet_list=`aws s3api list-buckets | \
    jq -r ".Buckets[].Name" | \
    grep ${bucket_name} `

# There is no target bucket
if [ -z "${backet_list}" ]; then
    echo "There was no target bucket."
    exit 0
fi

# Confirm that you want to delete the bucket
echo "${backet_list}"
while true; do
    read -p "Do you want to delete this buckets? (y/n)" yn
    case $yn in
        [Yy]* ) break;;
        [Nn]* ) exit 0;;
        * ) echo "Please answer yes or no.";;
    esac
done

echo "Start deleting the bucket."


# Delete the bucket
echo "${backet_list}" | while read backet_name
do
    echo "Deleting ${backet_name} ..."
    aws s3 rb s3://$backet_name --force
done

echo "done"
