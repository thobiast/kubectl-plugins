#!/usr/bin/env bash
#
# Print nodes resources requests and limits
#
# If no parameters, it display resources only for compute=true nodes, and
# remove nodes with label glusterfs
# Params:
#    all - Display resources for all group of labels
#
##############################################################################

# Show colored output
COLOR='1'

# Kubectl command
KUBE_BIN='oc'

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

		# No color if COLOR is disabled or color is blank
        if [ "$COLOR" = "0" ] || [ "$c" = "" ]; then
                echo "$*"
		# If color y (yellow) send text to stderr
        elif [ "$c_char" = "Y" ]; then
                if [ "$COLOR" = "0" ]; then
                        echo "$*" >&2
                else
                        echo -e "$c${*}$nc" >&2
                fi
		# Colored message to stdout
        else
                echo -e "$c${*}$nc"
        fi
}


##############################################################################
# Print resource requests and limits for a node
##############################################################################
print_node_requests()
{
	$KUBE_BIN describe node "$node"      |
		sed -n '/^ *Resource/{N;N;N;p;}' |
		sed 's/^ \+/        /'
}


##############################################################################
# Main
##############################################################################

[ "${KUBECTL_PLUGINS_CALLER}" ] && KUBE_BIN="${KUBECTL_PLUGINS_CALLER}"

all_nodes="$($KUBE_BIN get nodes --show-labels --no-headers)"

labels=$(echo "$all_nodes"                                 |
		 sed 's/node-role.kubernetes.io\/\([^,]\+\),/\1,/' |
		 sed 's/,[^,]*kubernetes[^,]\+//g'                 |
		 awk '{print $6}'                                  |
		 sort                                              |
		 uniq)

for label in $labels; do
	if [ "$1" == "all" ]; then
		# Get all nodes that have the labels
		nodes=$(echo "$all_nodes"        |
				grep -E "${label//,/.*}" |
				awk '{print $1}')
	else
		nodes=$(echo "$all_nodes"        |
				grep -E "${label//,/.*}" |
				grep 'compute=true'      |
				grep -v 'glusterfs'      |
				awk '{print $1}')
	fi
	[ "$nodes" ] && _echo "B" "$label"
	# For each now, show the resource requests and limits
	for node in $nodes; do
		_echo "G" "  - $node"
		print_node_requests "$node"
	done
done

# vim: ts=4
