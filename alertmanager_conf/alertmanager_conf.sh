#!/usr/bin/env bash

oc get secret alertmanager-main -o json -n openshift-monitoring |
    jq -r '.data["alertmanager.yaml"]'                          |
    base64 -d

# vim: ts=4
