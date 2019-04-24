#!/usr/bin/env bash

: "${KUBECTL_PLUGINS_CALLER:=oc}"

"$KUBECTL_PLUGINS_CALLER" get nodes --show-labels  |
    sed 's/beta.kubernetes.io\///g;
         s/kubernetes.io\/hostname=[^,]\+,//;
         s/node-role.kubernetes.io\///'            |
    awk '{print $1" "$2" "$3" "$4" "$6}'           |
    column -t

# vim: ts=4
