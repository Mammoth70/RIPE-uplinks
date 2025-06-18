#!/usr/bin/python3
# -*- coding: utf-8 -*-
'''
The script builds a tree of uplinks of an autonomous system.
'''

import argparse
import requests
import json
import re

def sort_asn(asn):
    '''
    Used as a key to properly sort ASN.
    '''
    return int(asn)


def true_ip(ip_address):
    '''
    Checks if the IP address string is valid.
    '''
    if (not(type(ip_address) is str)) or (not ip_address):
        return False
    octets = ip_address.split('.')
    if len(octets) != 4:
        return False
    for octet in octets:
        if (not octet.isdigit()) or (int(octet) < 0) or (int(octet) > 255):
            return False
    return True


def true_as(as_number):
    '''
    Checks if a string with ASN is valid.
    '''
    return as_number.isdigit() and (int(as_number) > 0) and (int(as_number) <= 4294967296)


def http_get_as_number(ip_address):
    '''
    Makes a request with an IP address to the stat.ripe.net API and returns an AS number.
    '''
    try:
        ipinfo = requests.get(f"http://stat.ripe.net/data/network-info/data.json?resource={ip_address}")
        if ipinfo.status_code == 200:
            ipinfo_data = ipinfo.json()
            if ipinfo_data['data']['asns'] != []:
                return ipinfo_data['data']['asns'][0]
        else:
            return ''
    except Exception as err:
            return ''


def http_get_as_holder(as_number):
    '''
    Makes a request with ASN to the stat.ripe.net API and returns the AS name.
    '''
    try:
        asinfo = requests.get(f"http://stat.ripe.net/data/as-overview/data.json?resource=AS{as_number}")
        if asinfo.status_code == 200:
            return asinfo.json()['data']['holder']
        else:
            return ''
    except Exception as err:
            return ''


def http_get_as_attribute(as_number):
    '''
    Makes an ASN request to the rest.db.ripe.net API and returns a list of ASN attribute information.
    '''
    try:
        asinfo = requests.get(f"http://rest.db.ripe.net/ripe/aut-num/as{as_number}", headers = {'Accept': 'application/json', 'Connection': 'Close'})
        if asinfo.status_code == 200:
            return asinfo.json()['objects']['object'][0]['attributes']['attribute']
        else:
            return None
    except Exception as err:
            return None


def query_ripe(as_number, level=0, deep=0):
    '''
    Requests are made to the RIPE DB.
    The AS uplink tree is built recursively.
    The depth of the uplink search is limited by the deep variable.
    '''
    regex = re.compile('^from AS(?P<asn>\d{1,6})')
    as_attribute = http_get_as_attribute(as_number)
    if as_attribute:
        as_set = set()
        for attr in as_attribute:
            if (attr['name'] == 'import') and (attr['value'].endswith(' accept ANY')):
                match = regex.search(attr['value'])
                if match:
                    asn = match.group('asn')
                    as_set.add(asn)
        for asn in sorted(as_set, key=sort_asn):
            as_name = http_get_as_holder(asn)
            if (level <= deep ):
                fs = ' '*level*4
                print(f'{fs}└── {asn:<6}  {as_name}')
                if (level < deep):
                    query_ripe(asn, level=level+1, deep=deep)


def tree_as(args):
    '''
    The command line arguments from the parser are parsed and checked.
    The main body of the script is executed.
    '''
    asn = args.asn
    if true_ip(asn):
        as_number = http_get_as_number(asn)
        print(f'[{asn}]')
    else:
        as_number = asn
    if true_as(as_number):
        as_name = http_get_as_holder(as_number)
        print(f'{as_number:<6}  {as_name}')
        query_ripe(as_number, deep=args.deep-1)


def create_parser():
    '''
    Command line parser.
    '''
    parser = argparse.ArgumentParser(prog = 'RIPE-uplinks.py',
            description = 'The script builds a tree of uplinks of an autonomous system.',
            add_help = False,
            epilog = 'ver. 1.0.2 - 08.05.2024' )
    pr_group = parser.add_argument_group(title='command line parameters')
    pr_group.add_argument('--help', '-h', action='help',                                         help='help output')
    pr_group.add_argument('--asn',  '-a', dest='asn',  required=True,                            help='AS number or IP address')
    pr_group.add_argument('--deep', '-d', dest='deep', default=1, type=int, choices=range(1, 4), help='recursion depth')
    pr_group.set_defaults(func=tree_as)
    return parser


if __name__ == '__main__':
    parser = create_parser()
    args = parser.parse_args()
    if not vars(args):
        parser.print_usage()
    else:
        args.func(args)
