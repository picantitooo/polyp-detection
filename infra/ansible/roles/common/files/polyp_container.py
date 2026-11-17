"""Remote-only idempotent container reconciliation. Never emit Docker inspect."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess


TURN_IMAGE = 'coturn/coturn:4.18.0-r0'


def docker(*args, check=True):
    return subprocess.run(['docker', *args], capture_output=True, check=check, text=True)


def reconcile(name, image, options, desired_env=None, force=False):
    image_id = json.loads(docker('image', 'inspect', image).stdout)[0]['Id']
    previous = docker('container', 'inspect', name, check=False)
    if previous.returncode == 0:
        container = json.loads(previous.stdout)[0]
        config = container['Config']
        previous_env = dict(item.split('=', 1) for item in config.get('Env', []) if '=' in item)
        matches = (container['Image'] == image_id
                   and config.get('Labels', {}).get('polyp.config') == json.dumps(options, separators=(',', ':'))
                   and all(previous_env.get(key) == value for key, value in (desired_env or {}).items())
                   and container['HostConfig']['RestartPolicy']['Name'] == 'unless-stopped')
        if matches and not force:
            if not container['State']['Running']:
                docker('start', name)
                return True
            return False
        docker('container', 'rm', '--force', name)
    elif 'No such' not in previous.stderr:
        raise RuntimeError('Cannot inspect existing container')
    docker('run', '--detach', '--restart', 'unless-stopped', '--name', name,
           '--label', 'polyp.config=' + json.dumps(options, separators=(',', ':')),
           *options, image, *(['-c', '/etc/coturn/turnserver.conf'] if name == 'polyp-turn' else []))
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('kind', choices=['backend', 'proxy'])
    parser.add_argument('--image')
    parser.add_argument('--origin')
    parser.add_argument('--env-file')
    parser.add_argument('--force', choices=['true', 'false'], default='false')
    args = parser.parse_args()
    if args.kind == 'backend':
        env = dict(line.split('=', 1) for line in Path(args.env_file).read_text().splitlines())
        env.update(POLYP_MODEL_DIR='/models', CORS_ALLOWED_ORIGINS=args.origin)
        options = ['-p', '8000:8000', '-v', '/opt/polyp/models:/models:ro',
                   '--env-file', args.env_file, '-e', 'POLYP_MODEL_DIR=/models',
                   '-e', f'CORS_ALLOWED_ORIGINS={args.origin}']
        changed = reconcile('polyp-backend', args.image, options, env)
    else:
        # Host networking is essential for EIP/private-IP NAT correspondence.
        # 3478 TCP/UDP and 49160-49200 UDP bind directly on the proxy interface.
        revision = hashlib.sha256(Path('/opt/polyp/turn/turnserver.conf').read_bytes()).hexdigest()
        options = ['--label', f'polyp.turn-revision={revision}', '--network', 'host', '--user', '0:0', '--log-driver', 'none',
                   '-v', '/opt/polyp/turn/turnserver.conf:/etc/coturn/turnserver.conf:ro']
        changed = reconcile('polyp-turn', TURN_IMAGE, options, force=args.force == 'true')
    print('changed' if changed else 'unchanged')


if __name__ == '__main__':
    try:
        main()
    except Exception:
        raise SystemExit('Container reconciliation failed; inspect host configuration without dumping secrets')
