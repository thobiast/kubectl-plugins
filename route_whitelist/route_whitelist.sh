#!/usr/bin/env bash

if [ -z "$1" ]; then
    echo "Error: You must specify route name"
    exit 1
fi

: "${KUBECTL_PLUGINS_CALLER:=oc}"

"$KUBECTL_PLUGINS_CALLER" get route "$1" -o \
    jsonpath="{.metadata.annotations.haproxy\.router\.openshift\.io/ip_whitelist}{'\n'}"

# vim: ts=4
