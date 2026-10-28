"""Run the app with Python network access restricted to loopback for verification.

This leaves the user's Windows network settings unchanged. It is a test harness,
not an OS firewall; offline model loading is also enforced by the runtime.
"""
import ipaddress
import socket


def loopback(host):
    if host in ("localhost", b"localhost", None):
        return True
    if isinstance(host, bytes):
        host = host.decode("ascii", errors="replace")
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


original_connect = socket.socket.connect
original_connect_ex = socket.socket.connect_ex
original_getaddrinfo = socket.getaddrinfo


def connect(sock, address):
    if isinstance(address, tuple) and not loopback(address[0]):
        raise OSError("Offline verification blocked external network connection")
    return original_connect(sock, address)


def connect_ex(sock, address):
    if isinstance(address, tuple) and not loopback(address[0]):
        raise OSError("Offline verification blocked external network connection")
    return original_connect_ex(sock, address)


def getaddrinfo(host, *args, **kwargs):
    if not loopback(host):
        raise OSError("Offline verification blocked external DNS lookup")
    return original_getaddrinfo(host, *args, **kwargs)


if __name__ == "__main__":
    socket.socket.connect = connect
    socket.socket.connect_ex = connect_ex
    socket.getaddrinfo = getaddrinfo
    from app import main
    main()
