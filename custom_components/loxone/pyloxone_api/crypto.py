"""Pure cryptographic operations for Loxone Miniserver communication.

All functions are stateless — they take inputs and return outputs with no
side effects.  This makes them easy to test independently of the connection
lifecycle.
"""

from __future__ import annotations

import hashlib
import time
import urllib.parse
from base64 import b64decode, b64encode

from Crypto.Cipher import AES, PKCS1_v1_5
from Crypto.Hash import HMAC, SHA1, SHA256
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
from Crypto.Util import Padding

from .const import (
    AES_KEY_SIZE,
    IV_BYTES,
    SALT_BYTES,
    SALT_MAX_AGE_SECONDS,
    SALT_MAX_USE_COUNT,
)

_HASH_MODULES = {"SHA1": SHA1, "SHA256": SHA256}
_HASHLIB_CTORS = {"SHA1": hashlib.sha1, "SHA256": hashlib.sha256}


def time_elapsed_in_seconds() -> int:
    return int(round(time.time()))


# -- Key / IV / salt generation -----------------------------------------------


def generate_aes_key() -> bytes:
    return get_random_bytes(AES_KEY_SIZE)


def generate_iv() -> bytes:
    return get_random_bytes(IV_BYTES)


def generate_salt() -> str:
    return get_random_bytes(SALT_BYTES).hex()


def new_salt_needed(salt_used_count: int, salt_timestamp: int) -> bool:
    return (
        salt_used_count > SALT_MAX_USE_COUNT
        or time_elapsed_in_seconds() - salt_timestamp > SALT_MAX_AGE_SECONDS
    )


# -- AES encrypt / decrypt ----------------------------------------------------


def encrypt_command(
    aes_key: bytes,
    iv: bytes,
    salt: str,
    command: str,
    old_salt: str | None = None,
) -> str:
    """AES-256-CBC encrypt a command for the Miniserver.

    Returns a fully-formed ``jdev/sys/enc/…`` URI.
    """
    if old_salt is not None:
        payload = f"nextSalt/{old_salt}/{salt}/{command}\x00"
    else:
        payload = f"salt/{salt}/{command}\x00"
    padded = Padding.pad(payload.encode("utf-8"), 16)
    cipher = AES.new(aes_key, AES.MODE_CBC, iv)
    encrypted = b64encode(cipher.encrypt(padded))
    return f"jdev/sys/enc/{urllib.parse.quote(encrypted.decode())}"


def decrypt_command(aes_key: bytes, iv: bytes, command: str) -> bytes:
    """AES-256-CBC decrypt a response from the Miniserver."""
    prefix = "jdev/sys/enc/"
    enc_text = command[len(prefix) :] if command.startswith(prefix) else command
    decoded = b64decode(enc_text)
    cipher = AES.new(aes_key, AES.MODE_CBC, iv)
    decrypted = cipher.decrypt(decoded)
    return Padding.unpad(decrypted, 16).rstrip(b"\x00")


# -- RSA session key -----------------------------------------------------------


def make_session_key(public_key_pem: str, aes_key: bytes, iv: bytes) -> bytes:
    """RSA-encrypt the AES session key for the key-exchange handshake."""
    rsa_key = RSA.importKey(public_key_pem)
    rsa_cipher = PKCS1_v1_5.new(rsa_key)
    session_key = f"{aes_key.hex()}:{iv.hex()}".encode("utf-8")
    return b64encode(rsa_cipher.encrypt(session_key))


def parse_public_key(raw_pk: str) -> str:
    """Convert Loxone's certificate-style PK to standard PEM."""
    return raw_pk.replace(
        "-----BEGIN CERTIFICATE-----", "-----BEGIN PUBLIC KEY-----\n"
    ).replace("-----END CERTIFICATE-----", "\n-----END PUBLIC KEY-----\n")


# -- HMAC hashing --------------------------------------------------------------


def hash_credentials(
    username: str,
    password: str,
    user_salt: str,
    key: str,
    hash_alg: str,
) -> str | None:
    """HMAC-hash credentials for token acquisition."""
    ctor = _HASHLIB_CTORS.get(hash_alg)
    module = _HASH_MODULES.get(hash_alg)
    if ctor is None or module is None:
        return None

    m = ctor()
    m.update(f"{password}:{user_salt}".encode("utf-8"))
    pwd_hash = f"{username}:{m.hexdigest().upper()}"

    try:
        digester = HMAC.new(
            bytes.fromhex(key), pwd_hash.encode("utf-8"), module
        )
    except ValueError:
        return None
    return digester.hexdigest()


def hash_token(token: str, key: str, hash_alg: str) -> str | None:
    """HMAC-hash a token for refresh / auth-with-token commands."""
    module = _HASH_MODULES.get(hash_alg)
    if module is None:
        return None
    try:
        key_bytes = bytes.fromhex(key)
    except ValueError:
        return None
    digester = HMAC.new(key_bytes, token.encode("utf-8"), module)
    return digester.hexdigest()


def hash_secure_command(
    code: str,
    visual_hash_key: str,
    visual_hash_salt: str,
    visual_hash_alg: str,
    device_uuid: str,
    value: str,
) -> str | None:
    """Build an encrypted command URI for visual-password-protected controls."""
    ctor = _HASHLIB_CTORS.get(visual_hash_alg)
    module = _HASH_MODULES.get(visual_hash_alg)
    if ctor is None or module is None:
        return None

    m = ctor()
    m.update(f"{code}:{visual_hash_salt}".encode("utf-8"))
    pwd_hash = m.hexdigest().upper()

    digester = HMAC.new(
        bytes.fromhex(visual_hash_key), pwd_hash.encode("utf-8"), module
    )
    new_hash = digester.hexdigest()
    return f"jdev/sps/ios/{new_hash}/{device_uuid}/{value}"
