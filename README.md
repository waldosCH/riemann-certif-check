# Riemann certificate check
Check days left for SSL certificate(s) and send event(s) to riemann (https://riemann.io)

## Requirements
* pyOpenSSL
* datetime
* argparse
* pyyaml
* riemann_client
* validators

## Usage
    checkSSL.py [-h] [--domain DOMAIN] [--port PORT]
                [--riemann-server RIEMANN_SERVER]
                [--riemann-port RIEMANN_PORT] [--riemann-ttl RIEMANN_TTL]
                [--critical CRITICAL] [--config CONFIG]
                
## Config file

config_example.yaml

    ---
    riemann:
      server: 'localhost'
      port: 5555
      ttl: 300
    criticality: 10
    domains:
      www.google.com:
        port : 443
      www.github.com:
