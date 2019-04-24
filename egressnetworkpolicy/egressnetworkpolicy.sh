#!/usr/bin/env bash
# Show egressnetworkpolicy kind for namespaces
#
# If no params specified, do not show egress network policy for
# openshift/kubernetes namespaces
# Params:
#        all  - display egress network policy for all namespaces
#   namespace - display egress network policy for an specific namespace

# Show colored output
COLOR='1'

# Kubectl command
KUBE_BIN='oc'

# Do not check network policy against the following namespaces
REMOVE_NAMESPACES='default|glusterfs|kube-.*|openshift-.*|openshift'

##############################################################################
##############################################################################
usage()
{
	echo "
Show Egress Network Policy

$0 [options]

options:
    -h           # show help
    all          # show egress network policy for all namespaces
    namespace    # show egress network policy for a specific namespace

If no parameter, do not show egress network policy for
openshift/kubernetes namespaces
"
	exit
}


##############################################################################
# Print messages
# $1 - color
#     B = blue
#     Y = yellow
#     G = green
#     R = red
#     N = nocolor
# $2 - text message to print
#
# PS: Y - send output to stderr
##############################################################################
_echo()
{
	local c_char="$1"
	local nc='\033[0m' # No Color
	local c

	case "$1" in
		B ) c='\e[1;34m'                            ;;
		Y ) c='\e[0;33m'                            ;;
		G ) c='\e[0;32m'                            ;;
		R ) c='\e[1;31m'                            ;;
		C ) c='\e[0;96m'                            ;;
		N ) c=''                                    ;;
		* ) _error "Erro: _echo cor invalida '$1'"  ;;
		esac

	shift

	# color estiver desabilitada ou color for N
	# imprime sem cor na stdout
	if [ "$COLOR" = "0" ] || [ "$c" = "" ]; then
		echo "$*"
	# se for Y (yellow) manda para a stderr
	elif [ "$c_char" = "Y" ]; then
		if [ "$COLOR" = "0" ]; then
			echo "$*" >&2
		else
			echo -e "$c${*}$nc" >&2
		fi
	# manda para stdout colorido
	else
		echo -e "$c${*}$nc"
	fi
}


##############################################################################
# Return egressnetworkpolicy formatted
##############################################################################
check_egress_policy()
{
	local egresspolicy

	egresspolicy=$($KUBE_BIN get egressnetworkpolicy "$2" -n "$1" -o yaml)
	echo "$egresspolicy"                                      |
		sed '1,/^  *egress:$/d'                               |
		sed 's/^ *//'                                         |
		sed ':a ; /type:/{ s/^-//; s/\n/ /g; P; D;} ; N ; ba' |
		column -t                                             |
		sed 's/^/    /'
}


##############################################################################
# Main
##############################################################################

[ "$1" == "help" ] && usage

[ "${KUBECTL_PLUGINS_CALLER}" ] && KUBE_BIN="${KUBECTL_PLUGINS_CALLER}"

all_namespaces=$($KUBE_BIN get projects -o name | sed 's#.*/##')
namespaces=$(echo "$all_namespaces" | grep -v -E "^($REMOVE_NAMESPACES)")

while [ "$1" != "" ]
do
	case "$1" in
		"all") namespaces="$all_namespaces"
			   shift ;;
		*    ) namespaces=$(echo "$all_namespaces" | grep -w "$1")
			   shift ;;
	esac
done

[ -n "$namespaces" ] || { _echo R "Error: namespace not found"; exit 1; }

for namespace in $namespaces; do
	_echo B "- Checking $namespace"
	egress_name=$($KUBE_BIN get egressnetworkpolicy -n "$namespace" -o name | sed 's#.*/##')
	if [ -n "$egress_name" ]; then
		_echo N "  ${egress_name}:"
		check_egress_policy "$namespace" "$egress_name"
	else
		_echo R "  No egressnetworkpolicy found."
	fi
done

# vim: ts=4
