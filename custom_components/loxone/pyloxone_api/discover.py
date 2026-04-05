"""Component to create an interface to the Loxone Miniserver.

For more details about this component, please refer to the documentation at
https://github.com/JoDehli/pyloxone-api
"""

from __future__ import annotations

import asyncio
from asyncio.tasks import wait_for
import contextlib
import re
import socket


async def discover(*, discovery_timeout: int = 5, host: str = "255.255.255.255") -> tuple[str, int, str] | None:
    """Attempt to discover a miniserver on the local network.

    Returns a tuple of (IPv4_address:string, port:int, response:string) if a
    miniserver is found on the local network within ``discovery_timeout`` seconds (default 5).
    If no miniserver is found, returns `None`. Response is the response from the
    miniserver, which contains other useful information, such as the serial number,
    firmware version etc.

    Pass a specific IP as `host` for directed (unicast) discovery instead of
    broadcast — useful when the Miniserver is on a different subnet or broadcast
    is blocked.
    """
    # A miniserver will respond on port 7071 to a UDP packet broadcast to port 7070
    # For details, see https://github.com/sarnau/Inside-The-Loxone-Miniserver/blob/
    #   master/LoxoneMiniserverNetworking.md
    #
    # This regex is good enough to find an IPv4 address and port in the response string
    r = re.compile(r"^LoxLIVE:.* ((?:[0-9]{1,3}\.){3}[0-9]{1,3}):(\d+) ")

    is_broadcast = host == "255.255.255.255"
    loop = asyncio.get_running_loop()

    if is_broadcast:
        # Broadcast: separate write socket (any ephemeral port) sends to
        # 255.255.255.255:7070; Miniserver broadcasts the response back to
        # port 7071 where our read socket is listening.
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as read_sock:
            read_sock.setblocking(False)
            read_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            read_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            read_sock.bind(("0.0.0.0", 7071))
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as write_sock:
                write_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

                # broadcast 3 packets of 0x00 byte to UDP port 7070 (UDP is unreliable)
                for _ in range(3):
                    write_sock.sendto(b"\x00", ("255.255.255.255", 7070))
                with contextlib.suppress(asyncio.TimeoutError):
                    response = (await wait_for(loop.sock_recv(read_sock, 1024), discovery_timeout)).decode()
                    # Look for a Loxone Response.
                    if (found := re.match(r, response)) is not None:
                        (ip, port) = found.groups()
                        return ip, int(port), response
                return None
    else:
        # Directed (unicast): single socket bound to port 7071. The Miniserver
        # replies to the sender address+port, so we must send FROM 7071.
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
            sock.setblocking(False)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            sock.bind(("0.0.0.0", 7071))

            # send 3 packets of 0x00 byte to UDP port 7070 (UDP is unreliable)
            for _ in range(3):
                sock.sendto(b"\x00", (host, 7070))
            with contextlib.suppress(asyncio.TimeoutError):
                response = (await wait_for(loop.sock_recv(sock, 1024), discovery_timeout)).decode()
                # Look for a Loxone Response.
                if (found := re.match(r, response)) is not None:
                    (ip, port) = found.groups()
                    return ip, int(port), response
            return None
