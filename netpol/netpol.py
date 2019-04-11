#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kubectl plugin to show all network policy
"""

import sys
import pprint
import requests
import kubernetes


def msg(color, msg_text, exitcode=0, *, end='\n'):
    """
    Print colored text.

    Arguments:
        size      (str): color name (blue, red, green, yellow,
                                     cyan or nocolor)
        msg_text  (str): text to be printed
        exitcode  (int, opt): Optional parameter. If exitcode is different
                              from zero, it terminates the script, i.e,
                              it calls sys.exit with the exitcode informed

    Keyword arguments:
        end         (str, opt): string appended after the last value,
                                default a newline


    Exemplo:
        msg("blue", "nice text in blue")
        msg("red", "Error in my script.. terminating", 1)
    """
    color_dic = {'blue': '\033[0;34m',
                 'red': '\033[1;31m',
                 'green': '\033[0;32m',
                 'yellow': '\033[0;33m',
                 'cyan': '\033[0;36m',
                 'resetcolor': '\033[0m'}

    if not color or color == 'nocolor':
        print(msg_text, end=end)
    else:
        try:
            print(color_dic[color] + msg_text + color_dic['resetcolor'],
                  end=end)
        except KeyError as exc:
            raise ValueError("Invalid color") from exc

    # flush stdout
    sys.stdout.flush()

    if exitcode:
        sys.exit(exitcode)


class K8s():
    """
    Class to handle Kubernetes api
    """
    def __init__(self):
        kubernetes.config.load_kube_config()
        configuration = kubernetes.client.Configuration()
        configuration.verify_ssl = False
        api_client = kubernetes.client.ApiClient(configuration)

        self.corev1api = kubernetes.client.CoreV1Api(api_client)
        self.networkingv1api = kubernetes.client.NetworkingV1Api(api_client)
        self.active_namespace = self.get_active_context_namespace()

    @classmethod
    def get_active_context_namespace(cls):
        """
        Return namespace for the active context
        """
        contexts, active_context = kubernetes.config.list_kube_config_contexts()
        if not active_context:
            print("Error: No active context found in kube-config file.")
            pprint.pprint(active_context['context']['namespace'])

        return active_context['context']['namespace']

    def get_namespaces(self):
        namespaces = self.corev1api.list_namespace(watch=False)
        return [i.metadata.name for i in namespaces.items]

    def list_all_networkpolicy(self):
        return self.networkingv1api.list_network_policy_for_all_namespaces()

    def list_networkpolicy(self, namespace):
        return self.networkingv1api.list_namespaced_network_policy(namespace)

    def read_networkpolicy(self, namespace, network_policy_name):
        return self.networkingv1api.read_namespaced_network_policy(
            network_policy_name, namespace)


##############################################################################
# Show target Pods for the network policy
##############################################################################
def show_networkpolicy_target_pods(netpol):
    msg("cyan", "      Pods targets for this networkpolicy: ", end='')
    if not netpol.spec.pod_selector.match_expressions and \
       not netpol.spec.pod_selector.match_labels:
        msg("nocolor", "All pods on this namespace")
    else:
        msg("nocolor", "")
        if netpol.spec.pod_selector.match_expressions:
            msg("nocolor", "      {}".format(
                pprint.pformat(netpol.spec.pod_selector.match_expressions)))
        if netpol.spec.pod_selector.match_labels:
            for key, value in netpol.spec.pod_selector.match_labels.items():
                msg("nocolor", "        label: {}={}".format(key, value))


##############################################################################
# Show destination ports for the network policy
##############################################################################
def show_networkpolicy_dest_ports(ingress_from_entry):
    if ingress_from_entry.ports:
        ports = ""
        for port in ingress_from_entry.ports:
            ports += "{}/{} ".format(port.port, port.protocol)
        msg("nocolor", " {}".format(ports))
    else:
        msg("nocolor", " All ports")


##############################################################################
# Show network policy source traffic details
##############################################################################
def show_ingress_entry_from(entry_from, add_new_line):
    if not entry_from.ip_block and \
       not entry_from.namespace_selector and \
       not entry_from.pod_selector.match_expressions and \
       not entry_from.pod_selector.match_labels:
        msg("nocolor", "All pods on same namespace")
        return

    if add_new_line:
        msg("nocolor", "")

    if entry_from.namespace_selector:
        msg("cyan", "            - From namespace:")
        if entry_from.namespace_selector.match_expressions:
            msg("nocolor", "                {}".format(pprint.pformat(
                entry_from.namespace_selector.match_expressions)))
        if entry_from.namespace_selector.match_labels:
            for key, value in entry_from.namespace_selector.match_labels.items():
                msg("nocolor", "                label: {}={}".format(key, value))

    if entry_from.pod_selector:
        msg("cyan", "            - From pod_selector:")
        if entry_from.pod_selector.match_expressions:
            msg("nocolor", "                {}".format(pprint.pformat(
                entry_from.pod_selector.match_expressions)))
        if entry_from.pod_selector.match_labels:
            for key, value in entry_from.pod_selector.match_labels.items():
                msg("nocolor", "                label: {}={}".format(key, value))

    if entry_from.ip_block:
        msg("cyan", "            - From ip_block:")
        if entry_from.ip_block._except:
            msg("nocolor", "                except: {}".format(pprint.pformat(
                entry_from.ip_block._except)))
        if entry_from.ip_block.cidr:
            msg("nocolor", "                cidr: {}".format(pprint.pformat(
                entry_from.ip_block.cidr)))


##############################################################################
# Show ingress traffic for the network policy
##############################################################################
def show_networkpolicy_ingress(ingress):
    # If ingress is None, all traffic is denied
    # If ingress._from is None, accept traffic from any source
    if ingress:
        for ingress_entry in ingress:
            msg("cyan", "      - Dest ports:", end='')
            show_networkpolicy_dest_ports(ingress_entry)
            msg("cyan", "          Source traffic: ", end='')
            if ingress_entry._from:
                for idx, entry_from in enumerate(ingress_entry._from):
                    add_new_line = True if idx < 1 else False
                    show_ingress_entry_from(entry_from, add_new_line)
            else:
                msg("nocolor", "Accept traffic from any source")
    else:
        msg("nocolor", "      No traffic allowed. Deny all ports")


##############################################################################
# Main function
##############################################################################
def main():
    requests.packages.urllib3.disable_warnings()

    k8s = K8s()
    namespace = k8s.get_active_context_namespace()
    msg("blue", "Namespace: {}".format(namespace))

    netpols = k8s.list_networkpolicy(namespace)

    # Check if there are network policy defined for the namespace
    if not netpols.items:
        msg("red", "  There is no network policy defined")
    else:
        # For each network policy, show details
        for netpol in netpols.items:
            msg("green", "  - {}".format(netpol.metadata.name))
#            pprint.pprint(netpol)
            show_networkpolicy_target_pods(netpol)
            show_networkpolicy_ingress(netpol.spec.ingress)


##############################################################################
# Run from command line
##############################################################################
if __name__ == '__main__':
    main()

# vim: ts=4
