"""Local-only tests: AWS CLI and Docker calls are mocked; no Ansible execution."""
import importlib.util
import json
from pathlib import Path
import stat
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'roles/common/files' / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


config = load('turn_config')
containers = load('polyp_container')
probe = load('turn_probe')


class RemoteTurnTests(unittest.TestCase):
    def test_fetch_is_decrypted_on_instance_and_not_printed(self):
        result = SimpleNamespace(stdout=json.dumps({'Parameter': {'Value': 'a' * 64}}))
        with patch.object(config.subprocess, 'run', return_value=result) as run:
            self.assertEqual(config.read_secret('/test/turn', 'us-east-2'), 'a' * 64)
        self.assertIn('--with-decryption', run.call_args.args[0])
        self.assertTrue(run.call_args.kwargs['capture_output'])
        self.assertTrue(run.call_args.kwargs['check'])

    def test_rejects_secret_config_injection(self):
        result = SimpleNamespace(stdout=json.dumps({'Parameter': {'Value': 'a\nno-auth'}}))
        with patch.object(config.subprocess, 'run', return_value=result):
            with self.assertRaises(ValueError):
                config.read_secret('/test/turn', 'us-east-2')

    def test_render_and_reject_unsafe_config_before_replacement(self):
        rendered = config.render_proxy('a' * 64, '8.8.8.8', '10.0.1.10')
        config.validate_proxy(rendered)
        for unsafe in [rendered + 'no-auth\n', rendered.replace('no-cli\n', ''),
                       rendered.replace('relay-ip=10.0.1.10', 'relay-ip=10.0.1.11'),
                       rendered.replace('max-port=49200', 'max-port=65535')]:
            with self.subTest(config=unsafe.replace('a' * 64, '[redacted]')):
                with self.assertRaises(ValueError):
                    config.validate_proxy(unsafe)
        self.assertIn('external-ip=8.8.8.8/10.0.1.10\n', rendered)
        self.assertNotIn('allow-loopback-peers', rendered)

    def test_atomic_file_permissions_and_idempotence(self):
        with tempfile.TemporaryDirectory() as directory:
            dest = Path(directory) / 'turnserver.conf'
            self.assertTrue(config.atomic_write(dest, 'first-secret'))
            inode = dest.stat().st_ino
            self.assertEqual(stat.S_IMODE(dest.stat().st_mode), 0o600)
            self.assertFalse(config.atomic_write(dest, 'first-secret'))
            self.assertEqual(dest.stat().st_ino, inode)
            self.assertTrue(config.atomic_write(dest, 'rotated-secret'))
            self.assertEqual(dest.read_text(), 'rotated-secret')
            self.assertEqual([p.name for p in Path(directory).iterdir()], ['turnserver.conf'])

    def existing_container(self, running=True):
        return {'Image': 'sha256:test', 'Config': {
            'Labels': {'polyp.config': '["--env-file","/private/turn.env"]'},
            'Env': ['TURN_SHARED_SECRET=test-secret']},
            'HostConfig': {'RestartPolicy': {'Name': 'unless-stopped'}},
            'State': {'Running': running}}

    def test_unchanged_container_is_retained(self):
        responses = [SimpleNamespace(stdout='[{"Id":"sha256:test"}]'),
                     SimpleNamespace(returncode=0, stdout=json.dumps([self.existing_container()]))]
        with patch.object(containers, 'docker', side_effect=responses) as docker:
            self.assertFalse(containers.reconcile('polyp-backend', 'image:tag', ['--env-file', '/private/turn.env'], {'TURN_SHARED_SECRET': 'test-secret'}))
        self.assertEqual(docker.call_count, 2)

    def test_rotated_secret_replaces_container_without_secret_in_argv(self):
        responses = [SimpleNamespace(stdout='[{"Id":"sha256:test"}]'),
                     SimpleNamespace(returncode=0, stdout=json.dumps([self.existing_container()])),
                     SimpleNamespace(stdout=''), SimpleNamespace(stdout='')]
        with patch.object(containers, 'docker', side_effect=responses) as docker:
            self.assertTrue(containers.reconcile('polyp-backend', 'image:tag', ['--env-file', '/private/turn.env'], {'TURN_SHARED_SECRET': 'rotated-secret'}))
        self.assertEqual(docker.call_args_list[2].args[:3], ('container', 'rm', '--force'))
        self.assertNotIn('rotated-secret', str(docker.call_args_list))

    def test_probe_requires_authentication_on_both_transports(self):
        challenge = bytes.fromhex('0009000400000401')
        with patch.object(probe, 'exchange', side_effect=[(0x0101, b''), (0x0113, challenge)] * 2) as exchange:
            probe.probe('10.0.1.10')
        self.assertEqual([call.args[2] for call in exchange.call_args_list], ['udp', 'udp', 'tcp', 'tcp'])
        with patch.object(probe, 'exchange', side_effect=[(0x0101, b''), (0x0103, b'')]):
            with self.assertRaises(ValueError):
                probe.probe('10.0.1.10')


if __name__ == '__main__':
    unittest.main()
