"""Remote STUN binding and unauthenticated TURN challenge over TCP and UDP."""
import argparse
import secrets
import socket
import struct

COOKIE = 0x2112A442


def read_exact(sock, size):
    result = b''
    while len(result) < size:
        part = sock.recv(size - len(result))
        if not part:
            raise ValueError('Incomplete STUN response')
        result += part
    return result


def exchange(host, port, transport, message_type, attributes=b''):
    transaction = secrets.token_bytes(12)
    request = struct.pack('!HHI12s', message_type, len(attributes), COOKIE, transaction) + attributes
    kind = socket.SOCK_DGRAM if transport == 'udp' else socket.SOCK_STREAM
    with socket.socket(socket.AF_INET, kind) as sock:
        sock.settimeout(3)
        sock.connect((host, port))
        sock.sendall(request)
        if transport == 'udp':
            response = sock.recv(65535)
        else:
            header = read_exact(sock, 20)
            response = header + read_exact(sock, struct.unpack('!H', header[2:4])[0])
    response_type, length, cookie, response_transaction = struct.unpack('!HHI12s', response[:20])
    if cookie != COOKIE or response_transaction != transaction or len(response) != 20 + length:
        raise ValueError('Invalid STUN response')
    return response_type, response[20:]


def probe(host, port=3478):
    for transport in ('udp', 'tcp'):
        response_type, _ = exchange(host, port, transport, 0x0001)
        if response_type != 0x0101:
            raise ValueError('STUN binding failed')
        # REQUESTED-TRANSPORT: UDP. Anonymous allocations must be rejected.
        response_type, attributes = exchange(host, port, transport, 0x0003, struct.pack('!HHBBBB', 0x0019, 4, 17, 0, 0, 0))
        error_code = None
        while attributes:
            attribute_type, size = struct.unpack('!HH', attributes[:4])
            value = attributes[4:4 + size]
            if attribute_type == 0x0009 and len(value) >= 4:
                error_code = (value[2] & 7) * 100 + value[3]
            attributes = attributes[4 + ((size + 3) // 4) * 4:]
        if response_type != 0x0113 or error_code != 401:
            raise ValueError('TURN must require authentication')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('host')
    parser.add_argument('--port', type=int, default=3478)
    args = parser.parse_args()
    try:
        probe(args.host, args.port)
    except Exception:
        raise SystemExit('TURN TCP/UDP health or authentication check failed')
