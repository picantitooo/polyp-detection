"""Run on the EC2 only. Fetch/render secrets without controller round trips."""
import argparse
import ipaddress
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile


def read_secret(parameter, region):
    result = subprocess.run(
        ['aws', 'ssm', 'get-parameter', '--with-decryption', '--name', parameter,
         '--region', region, '--output', 'json'], capture_output=True, check=True,
    )
    secret = json.loads(result.stdout)['Parameter']['Value']
    if not re.fullmatch(r'[a-zA-Z0-9]{64}', secret):
        raise ValueError('Unexpected TURN secret format')
    return secret


def render_proxy(secret, public_ip, private_ip):
    public = ipaddress.IPv4Address(public_ip)
    private = ipaddress.IPv4Address(private_ip)
    if not public.is_global or not private.is_private or private.is_loopback:
        raise ValueError('Invalid proxy public/private addresses')
    return '\n'.join([
        'listening-port=3478', 'min-port=49160', 'max-port=49200',
        f'listening-ip={private}', f'relay-ip={private}',
        'realm=polyp-staging-turn', 'lt-cred-mech', 'use-auth-secret',
        f'static-auth-secret={secret}', f'external-ip={public}/{private}',
        'fingerprint', 'no-cli', 'no-multicast-peers',
        # no-loopback-peers is obsolete in current Coturn; default is deny.
        '# no-loopback-peers: enforced by default and explicit deny rules',
        'denied-peer-ip=127.0.0.0-127.255.255.255', 'denied-peer-ip=::1',
        'denied-peer-ip=169.254.0.0-169.254.255.255',
        'no-tls', 'dtls=0', 'no-tcp-relay',
        'log-file=/dev/null', 'simple-log', 'no-stdout-log', 'pidfile=/tmp/turnserver.pid',
        'user-quota=4', 'total-quota=40', '',
    ])


def validate_proxy(content):
    """Strict validation of our generated config before any container replacement."""
    lines = [line for line in content.splitlines() if line and not line.startswith('#')]
    required = {'listening-port=3478', 'min-port=49160', 'max-port=49200',
                'realm=polyp-staging-turn', 'lt-cred-mech', 'use-auth-secret',
                'fingerprint', 'no-cli', 'no-multicast-peers',
                'denied-peer-ip=127.0.0.0-127.255.255.255', 'denied-peer-ip=::1',
                'denied-peer-ip=169.254.0.0-169.254.255.255',
                'no-tls', 'dtls=0', 'no-tcp-relay', 'log-file=/dev/null',
                'simple-log', 'no-stdout-log', 'pidfile=/tmp/turnserver.pid', 'user-quota=4', 'total-quota=40'}
    dynamic = {}
    for line in lines:
        key, _, value = line.partition('=')
        if key in {'static-auth-secret', 'external-ip', 'listening-ip', 'relay-ip'}:
            if key in dynamic:
                raise ValueError('Duplicate configuration key')
            dynamic[key] = value
        elif line not in required:
            raise ValueError('Unexpected configuration directive')
    if not required.issubset(lines) or len(lines) != len(required) + 4:
        raise ValueError('Incomplete TURN configuration')
    if not re.fullmatch(r'[a-zA-Z0-9]{64}', dynamic.get('static-auth-secret', '')):
        raise ValueError('Invalid secret format')
    expected = render_proxy(dynamic['static-auth-secret'], *dynamic['external-ip'].split('/'))
    if content != expected:
        raise ValueError('Inconsistent TURN configuration')


def atomic_write(path, content):
    """0600 even during creation; retain inode and mtime when unchanged."""
    path = Path(path)
    if path.exists() and path.read_text() == content:
        os.chmod(path, 0o600)
        return False
    descriptor, temporary = tempfile.mkstemp(prefix='.turn-', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'w') as output:
            os.fchmod(output.fileno(), 0o600)
            output.write(content)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('kind', choices=['backend', 'proxy'])
    parser.add_argument('--parameter', required=True)
    parser.add_argument('--region', required=True)
    parser.add_argument('--dest', required=True)
    parser.add_argument('--url')
    parser.add_argument('--public-ip')
    parser.add_argument('--private-ip')
    args = parser.parse_args()
    os.umask(0o077)
    secret = read_secret(args.parameter, args.region)
    if args.kind == 'proxy':
        content = render_proxy(secret, args.public_ip, args.private_ip)
        validate_proxy(content)
    else:
        if not args.url or not re.fullmatch(r'turn:[a-zA-Z0-9.-]+:3478\?transport=(udp|tcp)', args.url):
            raise ValueError('Invalid TURN URL')
        content = f'TURN_URL={args.url}\nTURN_SHARED_SECRET={secret}\n'
    print('changed' if atomic_write(args.dest, content) else 'unchanged')


if __name__ == '__main__':
    try:
        main()
    except Exception:
        # Suppress subprocess output, JSON and any exception containing a value.
        raise SystemExit('TURN configuration failed; check parameter access and configuration')
