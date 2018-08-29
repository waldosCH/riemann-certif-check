#! /usr/bin/env python

import OpenSSL
import ssl, socket
from datetime import datetime
import argparse
import yaml
import io
from riemann_client.transport import TCPTransport
from riemann_client.client import QueuedClient
import validators

DEFAULT_DOMAIN = 'www.google.com'
DEFAULT_SSL_PORT = 443
DEFAULT_RIEMANN_SERVER = 'localhost'
DEFAULT_RIEMANN_PORT = 5555
DEFAULT_RIEMANN_TTL = 300
DEFAULT_CRITICALITY = 10

def getArguments():
    parser = argparse.ArgumentParser(description='Check days left for SSL certificate(s) and send event(s) to riemann (https://riemann.io)')
    parser.add_argument('--domain', help='Domain to be checked', default=DEFAULT_DOMAIN)
    parser.add_argument('--port', help='Port to be checked', default=DEFAULT_SSL_PORT)
    parser.add_argument('--riemann-server', help='Riemann Server', default=DEFAULT_RIEMANN_SERVER)
    parser.add_argument('--riemann-port', help='Riemann Port', default=DEFAULT_RIEMANN_PORT)
    parser.add_argument('--riemann-ttl', help='Riemann Port', default=DEFAULT_RIEMANN_TTL)
    parser.add_argument('--critical', help='Number of day(s) for the status to be set as critical', default=DEFAULT_CRITICALITY)
    parser.add_argument('--config', help="Yaml configuration file")
    return parser.parse_args()

def getCertExpirationDelay(host, port):
    cert = ssl.get_server_certificate((host, port))
    x509 = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, cert)
    certif_expires = datetime.strptime(x509.get_notAfter(), '%Y%m%d%H%M%SZ')
    return certif_expires - datetime.today()

def getCriticallity(days):
    status = "critical"
    if delta.days > args.critical:
        status = "ok"
    return status

def getConfig(file):
    with io.open(file, 'r') as stream:
        config = yaml.load(stream)

        # config check
        if 'riemann' not in config:
            config['riemann'] = {}

        # riemann-server
        if 'server' not in config['riemann']:
            config['riemann']['server'] = args.riemann_server
        if not (validators.domain(config['riemann']['server']) or config['riemann']['server'] == 'localhost'):
            print("riemann.server must be a valid domain")
            exit(1)

        # riemann-port
        if 'port' not in config['riemann']:
            config['riemann']['port'] = args.riemann_port
        if not (type(config['riemann']['port']) is int):
            print("riemann.port must be an integer")
            exit(1)

        # riemann-ttl
        if 'ttl' not in config['riemann']:
            config['riemann']['ttl'] = args.riemann_ttl
        if not (type(config['riemann']['ttl']) is int):
            print("riemann.ttl must be an integer")
            exit(1)

        # crticality
        if 'criticality' not in config:
            config['criticality'] = args.critical
        if not (type(config['criticality']) is int):
            print("criticality must be an integer (how many days)")
            exit(1)

        # domains
        if 'domains' not in config:
            config['domains'] = {}
            config['domains'][args.domain] = {'port': args.port}
        for domain in config['domains']:
            if not validators.domain(domain):
                print("domains." + domain + " must be a valid domain")
                exit(1)
            if type(config['domains'][domain]) is not dict:
                config['domains'][domain] = {'port': DEFAULT_SSL_PORT}
            else:
                if not (type(config['domains'][domain]['port']) is int):
                     print("port for " + domain + " must be an integer")
                     exit(1)

        return config


# main
args = getArguments()
config = getConfig(args.config)
with QueuedClient(TCPTransport(config['riemann']['server'], config['riemann']['port'])) as client:
    for domain in config['domains']:
        delta = getCertExpirationDelay(domain, config['domains'][domain]['port'])
        client.event(service="certif_check_" + str(config['domains'][domain]['port']), metric_f=delta.days, state=getCriticallity(delta.days), ttl=config['riemann']['ttl'], host=domain)
    client.flush()