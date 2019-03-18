#!/usr/bin/env bash
# Show pod events

if [ ! "$1" ]; then
	echo "Erro: You must specify a pod"
	exit 1
fi

oc get events -o yaml --field-selector="involvedObject.name=$1" |
	sed '/- apiVersion:/{x;p;x;}; ${p;x;p;}' |
 	sed -n '/- apiVersio\|count\|firstTimestamp\|message\|lastTimestamp\|reason/p'
