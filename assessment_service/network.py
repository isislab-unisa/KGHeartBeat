"""Block non-public destinations in Python socket clients, including redirects.

The worker's own loopback SPARQL listener is the only private exception.
Use host/container egress rules as well for native libraries (see README).
"""
import ipaddress
import socket
from urllib.parse import urlsplit


def public_address(host):
    address = ipaddress.ip_address(host.split('%')[0])
    if getattr(address, 'ipv4_mapped', None):
        address = address.ipv4_mapped
    return (address.is_global and not address.is_multicast
            and not getattr(address, 'sixtofour', None) and not getattr(address, 'teredo', None))


def validate_public_url(url):
    parsed = urlsplit(url)
    if parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError('Only public HTTP(S) sources are accepted')
    addresses = socket.getaddrinfo(parsed.hostname, parsed.port or (443 if parsed.scheme == 'https' else 80),
                                   type=socket.SOCK_STREAM)
    if not addresses or any(not public_address(item[4][0]) for item in addresses):
        raise PermissionError('Source resolves to a non-public address')


def install_network_guard():
    original_connect = socket.socket.connect
    original_connect_ex = socket.socket.connect_ex
    original_bind = socket.socket.bind
    original_close = socket.socket.close
    listeners = {}

    def destination(sock, address):
        if sock.family not in (socket.AF_INET, socket.AF_INET6):
            raise PermissionError('Only IP network connections are supported')
        answers = socket.getaddrinfo(address[0], address[1], sock.family, sock.type)
        # Check every resolution, then connect to the checked numeric address.
        # No second hostname lookup may happen between validation and connect.
        for answer in answers:
            host, port = answer[4][:2]
            if not public_address(host) and (host, port) not in listeners.values():
                raise PermissionError('Connections to non-public addresses are blocked')
        if not answers:
            raise PermissionError('No public destination found')
        return answers[0][4]

    def connect(sock, address):
        return original_connect(sock, destination(sock, address))

    def connect_ex(sock, address):
        return original_connect_ex(sock, destination(sock, address))

    def bind(sock, address):
        result = original_bind(sock, address)
        if sock.family in (socket.AF_INET, socket.AF_INET6):
            host, port = sock.getsockname()[:2]
            if ipaddress.ip_address(host).is_loopback:
                listeners[sock.fileno()] = (host, port)
        return result

    def close(sock):
        listeners.pop(sock.fileno(), None)
        return original_close(sock)

    socket.socket.connect = connect
    socket.socket.connect_ex = connect_ex
    socket.socket.bind = bind
    socket.socket.close = close
