#!/usr/bin/env bash

if [ ! -n "$1" ]; then
	echo "Error: You must specify route name"
	exit 1
fi

oc get route "$1" -o \
	jsonpath="{.metadata.annotations.haproxy\.router\.openshift\.io/ip_whitelist}{'\n'}"

# vim: ts=4
