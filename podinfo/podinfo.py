#! /usr/bin/env python3
# -*- coding: utf-8 -*-

# TODO: Remove from output pod that podname terminate with -deploy

import argparse
import subprocess
import sys
import logging
import json
import pprint
import prettytable


KUBE_BIN = 'oc'

##############################################################################
# Parses the command line arguments
##############################################################################
def parse_parameters():
    # epilog message: Custom text after the help
    epilog = '''
    Example of use:
        %s diag
        %s limit
    ''' % (sys.argv[0], sys.argv[0])
    # Create the argparse object and define global options
    parser = argparse.ArgumentParser(description='podinfo',
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog=epilog)
    parser.add_argument('--debug', '-d',
                        action='store_true',
                        dest='debug',
                        help='debug flag')
    # Add subcommands options
    subparsers = parser.add_subparsers(title='Commands', dest='command')
    # diag
    diag_parser = subparsers.add_parser('diag',
                                        help='Show details for pods not healthy')
    diag_parser.set_defaults(func=cmd_diag)
    # limit
    limit_parser = subparsers.add_parser('limit',
                                         help='Show resource limits')
    limit_parser.set_defaults(func=cmd_limits)
    # probe
    probe_parser = subparsers.add_parser('probe',
                                         help='Show containers probe')
    probe_parser.set_defaults(func=cmd_probe)
    # image
    image_parser = subparsers.add_parser('image',
                                         help='Show containers image')
    image_parser.set_defaults(func=cmd_image)
    # affinity
    affinity_parser = subparsers.add_parser('affinity',
                                            help='Show pod affinity')
    affinity_parser.set_defaults(func=cmd_affinity)
    # ports
    ports_parser = subparsers.add_parser('ports',
                                         help='Show pod ports')
    ports_parser.set_defaults(func=cmd_ports)

    # If there is no parameter, print help
    if len(sys.argv) < 2:
        parser.print_help()
        sys.exit(0)

    return parser.parse_args()


def setup_logging(logfile=None, *,
                  filemode='a', date_format=None, log_level='DEBUG'):
    """
    Configure logging

    Arguments (opt):
        logfile     (str): log file to write the log messages
                               If not specified, it shows log messages
                               on screen (stderr)
    Keyword arguments (opt):
        filemode    (a/w): a - log messages are appended to the file (default)
                           w - log messages overwrite the file
        date_format (str): date format in strftime format
                           default is %m/%d/%Y %H:%M:%S
        log_level   (str): specifies the lowest-severity log message
                           DEBUG, INFO, WARNING, ERROR or CRITICAL
                           default is DEBUG
    """
    dict_level = {'DEBUG': logging.DEBUG,
                  'INFO': logging.INFO,
                  'WARNING': logging.WARNING,
                  'ERROR': logging.ERROR,
                  'CRITICAL': logging.CRITICAL}

    if log_level not in dict_level:
        raise ValueError("Invalid log_level")
    if filemode not in ['a', 'w']:
        raise ValueError("Invalid filemode")

    if not date_format:
        date_format = '%m/%d/%Y %H:%M:%S'

    log_fmt = '%(asctime)s %(module)s %(funcName)s %(levelname)s %(message)s'

    try:
        logging.basicConfig(level=dict_level[log_level],
                            format=log_fmt,
                            datefmt=date_format,
                            filemode=filemode,
                            filename=logfile)
    except:
        raise

    return logging.getLogger(__name__)


def run_cmd(cmd):
    """
    Execute a command on the operating system

    Arguments:
        cmd    (str): the command to be executed

    Return:
        - If command complete with return code zero
        return: command_return_code, stdout

        - If command completes with return code different from zero
        return: command_return_code, stderr
    """
    process = subprocess.Popen(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True)

    # Poll process for new output until finished
    stdout_output = ""
    while True:
        nextline = process.stdout.readline()
        if nextline == '' and process.poll() is not None:
            break
        # print lines to stdout
        #sys.stdout.write(nextline)
        #sys.stdout.flush()
        stdout_output += nextline

    stderr = process.communicate()[1]

    if process.returncode:
        return process.returncode, stderr
    else:
        return process.returncode, stdout_output


def msg(color,
        msg_text,
        exitcode=0,
        *,
        end='\n'):
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
        print(msg_text)
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


def print_table(header, rows, *, sortby='', alignl='', alignr='', hrules=''):
    """
    Print table using module prettytable
    Arguments:
        header     (list): List with table header
        rows       (list): Nested list with table rows
                           [ [row1], [row2], [row3], ... ]

    Keyword arguments (optional):
        sortby      (str): header name to sort the output
        alignl     (list): headers name to align to left
        alignr     (list): headers name to align to right
        hrules      (str): Controls printing of horizontal rules after rows.
                           Allowed values: FRAME, HEADER, ALL, NONE
    """
    output = prettytable.PrettyTable(header)
    output.format = True
    if hrules:
        output.hrules = getattr(prettytable, hrules)

    for row in rows:
        row_entry = list()
        for pos in row:
            row_entry.append(pos)
        output.add_row(row_entry)

    if sortby:
        # if sortby is invalid, ie, does not exist on header,
        # sort by first column by default
        output.sortby = sortby if sortby in header else header[0]
    for left in alignl:
        output.align[left] = 'l'
    for right in alignr:
        output.align[right] = 'r'

    print(output)


##############################################################################
# Return a value from a dictionary key
##############################################################################
def return_dict_value(dictionary, keys):
    """
    Return a value from a dictionary keys.
    Recursively iterate over a dictionary (can be nested) and return value
    for the key

    Args:
        dictionary  (dict):  dictionary
        key         (list):  A list with keys
    """
    log.debug("-------------------------------------------")
    log.debug("Dictionary: %s", pprint.pformat(dictionary))
    log.debug("Keys: %s", keys)
    if len(keys) > 1:
        log.debug("There are more keys: %s", keys[1:])
        log.debug("Call recursive with dictionary: %s", pprint.pformat(dictionary[keys[0]]))
        if isinstance(dictionary, dict):
            try:
                return return_dict_value(dictionary[keys[0]], keys[1:])
            except KeyError:
                return ''
        else:
            log.debug("Key passed is not a key. It is a value: %s", dictionary)
            return ''
    else:
        if isinstance(dictionary, dict):
            try:
                return dictionary[keys[0]]
            except KeyError:
                log.debug("Last key not found: '%s'", keys)
                return ''
        else:
            log.debug("Last key passed is not key, it is a value: %s", dictionary)
            return ''


class Container():
    def __init__(self, containername):
        self.name = containername
        self.image = ''
        self.imageid = ''
        self.imagepullpolicy = ''
        self.limit_cpu = ''
        self.limit_mem = ''
        self.request_cpu = ''
        self.request_mem = ''
        self.readinessprobe = ''
        self.livenessprobe = ''
        self.ready = ''
        self.restart = ''
        self.state = ''
        self.ports = ''

    def return_container_json(self, containers_json):
        for i in containers_json:
            if i['name'] == self.name:
                return i
        return

    def load_container_spec(self, specjson):
        spec = self.return_container_json(specjson)
        self.image = spec['image']
        self.imagepullpolicy = spec['imagePullPolicy']
        self.readinessprobe = return_dict_value(spec, ['readinessProbe'])
        self.livenessprobe = return_dict_value(spec, ['livenessProbe'])
        self.limit_cpu = return_dict_value(spec, ['resources', 'limits', 'cpu'])
        self.limit_mem = return_dict_value(spec, ['resources', 'limits', 'memory'])
        self.request_cpu = return_dict_value(spec, ['resources', 'requests', 'cpu'])
        self.request_mem = return_dict_value(spec, ['resources', 'requests', 'memory'])
        self.ports = return_dict_value(spec, ['ports'])

    def load_container_status(self, containerstatusjson):
        cont_status = self.return_container_json(containerstatusjson)
        self.ready = cont_status['ready']
        self.restart = cont_status['restartCount']
        self.state = list(cont_status['state'])[0]
        self.imageid = cont_status['imageID']


class Pod():
    def __init__(self, podname, podjson):
        self.podname = podname
        self.qosclass = podjson['status']['qosClass']
        self.status = podjson['status']['phase']
        self.conditions = podjson['status']['conditions']
        self.message = return_dict_value(podjson, ['status', 'message'])
        self.reason = return_dict_value(podjson, ['status', 'reason'])
        self.nodename = return_dict_value(podjson, ['spec', 'nodeName'])
        self.affinity = return_dict_value(podjson, ['spec', 'affinity'])
        self.nodeselector = return_dict_value(podjson, ['spec', 'nodeSelector'])
        self.starttime = return_dict_value(podjson, ['status', 'startTime'])
        self.containers = list()
        self.containers = [Container(i['name'])
                           for i in podjson['spec']['containers']]
        # Load container details
        for container in self.containers:
            container.load_container_spec(podjson['spec']['containers'])
            try:
                container.load_container_status(podjson['status']['containerStatuses'])
            except KeyError:
                pass

    def num_containers_ready(self, status):
        """
        Return number of containers with specific status:

        Args:
            status (True/False):   container ready status
        """
        num_containers = 0
        for container in self.containers:
            if container.ready == status:
                num_containers += 1
        return num_containers

    def num_containers(self):
        """
        Return number of containers on the pod
        """
        return len(self.containers)

    def is_all_containers_ready(self):
        """
        Check if all containers are ready.

        Returns:
            True: All containers ready
            False: At least one container is not ready
        """
        return self.num_containers() == self.num_containers_ready(True)


##############################################################################
# Instantiate all Pods
# Return a list with all Pod objects
##############################################################################
def create_pods_inst(*, podsjson):
    return [Pod(i['metadata']['name'], i) for i in podsjson['items']]


##############################################################################
# Show container image
##############################################################################
def cmd_image(pods):
    for pod in pods:
        msg("blue", "Pod: {}".format(pod.podname))
        for container in pod.containers:
            msg("green", " - container: {}".format(container.name))
            msg("cyan", "     image: ", end='')
            msg("nocolor", "{}".format(container.image))
            msg("cyan", "     imageId: ", end='')
            msg("nocolor", "{}".format(container.imageid))
            msg("cyan", "     imagePullPolicy: ", end='')
            msg("nocolor", "{}".format(container.imagepullpolicy))


##############################################################################
# Show container probe
##############################################################################
def cmd_probe(pods):
    for pod in pods:
        msg("blue", "Pod: {}".format(pod.podname))
        for container in pod.containers:
            msg("green", " - container: {}".format(container.name))
            msg("cyan", "   readinessprobe:")
            if container.readinessprobe:
                pprint.pprint(container.readinessprobe)
            msg("cyan", "   livenessprobe:")
            if container.livenessprobe:
                pprint.pprint(container.livenessprobe)


##############################################################################
# Show pod ports
##############################################################################
def cmd_ports(pods):
    for pod in pods:
        msg("blue", "Pod: {}".format(pod.podname))
        for container in pod.containers:
            msg("cyan", "  - Container: {}".format(container.name))
            for port in container.ports:
                msg("nocolor", "      {} {}".format(port['protocol'],
                                                    port['containerPort']))

##############################################################################
# Show pod affinity
##############################################################################
def cmd_affinity(pods):
    for pod in pods:
        msg("blue", "Pod: {}".format(pod.podname))
        msg("cyan", " affinity:")
        if pod.affinity:
            for aff_type in pod.affinity:
                for is_required in pod.affinity[aff_type]:
                    msg("nocolor", "{}".format(aff_type))
                    msg("nocolor", "  {}".format(is_required))
                    msg("nocolor", "     {}".format(
                        pprint.pformat((pod.affinity[aff_type][is_required]))))
        msg("cyan", " nodeSelector:")
        msg("nocolor", "   {}".format(pprint.pformat(pod.nodeselector)))


##############################################################################
# Show container limits
##############################################################################
def cmd_limits(pods):
    for pod in pods:
        msg("blue", "Pod: {}".format(pod.podname))
        msg("nocolor", " qosClass: {}".format(pod.qosclass))
        for container in pod.containers:
            msg("green", " - container: {}".format(container.name))
            msg("nocolor", "     Request - cpu: {} mem: {}".
                format(container.request_cpu, container.request_mem))
            msg("nocolor", "     Limit   - cpu: {} mem: {}".
                format(container.limit_cpu, container.limit_mem))


##############################################################################
# Show diag information
##############################################################################
def cmd_diag(pods):
    pods_ready = list()
    pods_notready = list()
    for pod in pods:
        if pod.is_all_containers_ready():
            pods_ready.append(pod)
        else:
            pods_notready.append(pod)

    msg("cyan", "There are {} pods on this space. {}/{} are ready".
        format(len(pods), len(pods_ready), len(pods)))

    for pod in pods_ready:
        msg("blue", "Pod: {} All containers ready".format(pod.podname))

    for pod in pods_notready:
        msg("red", "Pod: {} ".format(pod.podname))
        msg("yellow", "- Pod nodename: ", end='')
        msg("nocolor", "{} ".format(pod.nodename))
        msg("yellow", "- Pod status: ", end='')
        msg("nocolor", "{}".format(pod.status))
        msg("yellow", "- Pod conditions:")
        pprint.pprint(pod.conditions)
        for container in pod.containers:
            if container.ready is True:
                msg("nocolor", "Container {} is ready".format(container.ready))
            else:
                msg("yellow", "- Container name: ", end='')
                msg("nocolor", "{}".format(container.name))
                msg("yellow", "  * Container events:")
                oc_output = run_cmd(
                    "{} get events --field-selector='involvedObject.name={}'".
                    format(KUBE_BIN, pod.podname))
                print(oc_output[1])
                msg("yellow", "  * Container logs:")
                oc_output = run_cmd("{} logs {} -c {} | head -10".format(
                    KUBE_BIN, pod.podname, container.name))
                print(oc_output[1])


##############################################################################
# Main function
##############################################################################
def main():
    global log
    # Parser the command line
    args = parse_parameters()

    # Configure log if --debug
    log = setup_logging() if args.debug else logging
    log.debug('CMD line args: %s', vars(args))

    oc_output = run_cmd("{} get pod -o json".format(KUBE_BIN))
    if oc_output[0] > 0:
        msg("red", oc_output[1], 1)

    # Create a list with all pods instances
    pods = create_pods_inst(podsjson=json.loads(oc_output[1]))

    args.func(pods)


##############################################################################
# Run from command line
##############################################################################
if __name__ == '__main__':
    main()

# vim: ts=4
