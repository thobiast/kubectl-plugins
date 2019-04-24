#!/usr/bin/env bash

: "${KUBECTL_PLUGINS_CALLER:=oc}"

"$KUBECTL_PLUGINS_CALLER" \
    get secret alertmanager-main -o json -n openshift-monitoring   |
    jq -r '.data["alertmanager.yaml"]'                             |
    base64 -d

# vim: ts=4
