#!/bin/bash

TEMP=`getopt -o f:: --long file-name:: --"$@"`
eval set -- "$TEMP"

while true ; do
	case "$1" in
		-f|--file-name)
			fileName=$2; shift 2 ;;
	esac ;;
done

echo "test"
