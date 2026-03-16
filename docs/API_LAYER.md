# pyloxone_api — Low-Level API Client

> Technical deep dive into the WebSocket/HTTP client layer at `custom_components/loxone/pyloxone_api/`

## Overview

The `pyloxone_api` package is a self-contained async client for the Loxone Miniserver protocol. It handles:

- UDP discovery of Miniservers on the LAN
- HTTP API calls (structure file, API key, public key)
- WebSocket connection with AES-256-CBC encryption
- Token-based authentication with automatic refresh
- Binary message framing and parsing
- Reconnection logic

The package can run standalone (`python -m custom_components.loxone.pyloxone_api host port user pass`) or as a library consumed by the HA integration layer.

## Module Map

```
pyloxone_api/
├── __init__.py              # Package entry, logger
├── __main__.py              # Standalone CLI (~45 lines)
├── api.py                   # Placeholder — empty (~10 lines)
├── connection.py            # Core: WS lifecycle, crypto, auth (~1420 lines)
├── websocket_protocol.py    # WS framing layer (~105 lines)
├── message.py               # Message types and parsing (~378 lines)
├── loxone_token.py          # Token dataclass (~70 lines)
├── loxone_http_client.py    # HTTP client with Basic Auth (~245 lines)
├── discover.py              # UDP broadcast discovery (~60 lines)
├── helper.py                # HMAC utilities — UNUSED (~45 lines)
├── exceptions.py            # Exception hierarchy (~97 lines)
├── const.py                 # Constants (~67 lines)
└── tests/
    ├── __init__.py
    ├── test_discover.py     # 2 tests (require network)
    └── test_run_alone.py    # Placeholder (no actual tests)
```

## connection.py — The Heart of the Client

This is the largest and most critical file (~1420 lines). It contains two main classes:

### `LoxoneBaseConnection`

Handles low-level concerns:

| Responsibility           | Key Methods                                                   |
|--------------------------|---------------------------------------------------------------|
| URL/host validation      | `__init__`, `_parse_url`, `_detect_scheme`                    |
| Crypto setup             | `_generate_aes_key`, `_generate_iv`, `_generate_salt`         |
| AES encryption/decryption| `_encrypt_command`, `_decrypt_command`                        |
| HMAC/hashing             | `_hash_token`, `_hash_credentials`                            |
| Salt management          | `_generate_salt`, salt rotation by age/use count              |
| Token storage            | `_token: LoxoneToken`                                         |

### `LoxoneConnection(LoxoneBaseConnection)`

Handles the connection lifecycle:

| Phase               | Method                      | What Happens                                     |
|---------------------|-----------------------------|--------------------------------------------------|
| **Open**            | `open()`                    | HTTP: fetch API key, structure file, public key   |
| **Connect**         | `start_listening()`         | WS connect, key exchange, auth                   |
| **Listen**          | `_listen()`                 | Receive loop → `_process_message`                |
| **Process**         | `_process_message()`        | Enqueue to `asyncio.Queue`                       |
| **Dispatch**        | `_message_processing()`     | Dequeue → invoke `message_callback`              |
| **Keep-alive**      | `_keep_alive()`             | Periodic `keepalive` command                     |
| **Token refresh**   | `_check_and_refresh_token()`| Refresh before expiry                            |
| **Reconnect**       | `_reconnect()`              | Retry on disconnect                              |
| **Close**           | `close()`                   | Graceful shutdown                                |

### Connection State Machine

```
         open()
           │
           ▼
    ┌─────────────┐     start_listening()     ┌──────────────────┐
    │   HTTP      │ ──────────────────────►   │   WS Connected   │
    │   Setup     │                           │   Key Exchange    │
    └─────────────┘                           │   Auth + Token    │
                                              └────────┬─────────┘
                                                       │
                                     ┌─────────────────┼──────────────────┐
                                     │                 │                  │
                                     ▼                 ▼                  ▼
                              ┌────────────┐   ┌────────────┐   ┌──────────────┐
                              │  _listen() │   │ _keep_     │   │ _check_and_  │
                              │  recv loop │   │  alive()   │   │ refresh_     │
                              └──────┬─────┘   └────────────┘   │ token()      │
                                     │                          └──────────────┘
                                     │ disconnect
                                     ▼
                              ┌────────────┐
                              │ _reconnect │ ──► back to WS Connected
                              └────────────┘
```

### Key Exchange Protocol

```
Client                              Miniserver
  │                                      │
  │──── RSA(AES_key + ":" + IV) ────────►│   "jdev/sys/keyexchange/{payload}"
  │◄──── 200 OK ────────────────────────│
  │                                      │
  │──── "jdev/sys/getkey2/{user}" ──────►│
  │◄──── {key, salt, hashAlg} ──────────│
  │                                      │
  │──── AES(gettoken/hash/user/...) ────►│   HMAC(user:pass, key) + salt
  │◄──── {token, validUntil, ...} ──────│
  │                                      │
  │──── "enablebinstatusupdate" ────────►│   Subscribe to state updates
  │◄──── Binary state events ───────────│
```

## message.py — Message Types

The Loxone WS protocol uses a binary header (8 bytes) followed by a payload.

### Header Format (8 bytes)

| Byte | Field        | Values                                           |
|------|-------------|--------------------------------------------------|
| 0    | Fixed       | `0x03`                                           |
| 1    | Type        | See MessageType enum                             |
| 2    | Info/flags  | `estimated` flag                                 |
| 3    | Reserved    | —                                                |
| 4–7  | Length      | Payload length (little-endian uint32)            |

### MessageType Enum

| Value | Type               | Payload Format    | Purpose                    |
|-------|--------------------|-------------------|----------------------------|
| 0     | TEXT               | UTF-8 text        | Text responses             |
| 1     | BINARY             | Binary            | Binary file data           |
| 2     | VALUE_STATES       | `[uuid, value]×N` | Analog state updates       |
| 3     | TEXT_STATES         | `[uuid, icon, text]×N` | Text state updates   |
| 4     | DAYTIMER_STATES    | Complex struct    | Daytimer entries           |
| 5     | OUT_OF_SERVICE     | —                 | Miniserver rebooting       |
| 6     | KEEPALIVE          | —                 | Connection alive           |
| 7     | WEATHER_STATES     | Complex struct    | Weather data               |

### Message Class Hierarchy

```
BaseMessage
├── TextMessage          (type 0)
├── LLResponse           (type 0, parsed JSON)
├── ValueStatesTable     (type 2)
├── TextStatesTable      (type 3)
├── DaytimerStatesTable  (type 4)
└── WeatherStatesTable   (type 7)
```

`parse_message()` iterates `BaseMessage.__subclasses__()` and calls each subclass's `can_parse()` → `parse()`.

## loxone_http_client.py — HTTP Layer

Wraps `aiohttp` for Miniserver HTTP API calls:

| Method       | Purpose                                             |
|--------------|-----------------------------------------------------|
| `get(url)`   | GET with Basic Auth, configurable timeout           |
| `_handle_error()` | Maps HTTP status codes to exception types     |

### Error Mapping

| Status Code | Exception                        |
|-------------|----------------------------------|
| 401         | `LoxoneUnauthorisedError`        |
| 503         | `LoxoneServiceUnAvailableError`  |
| 429         | `LoxoneMaxNumOfConnectionsError` |
| 400         | `LoxoneUnrecognizedCommandError` |
| Other       | `LoxoneHTTPStatusError`          |

## loxone_token.py — Token Management

Two dataclasses:

### `LoxoneToken`

| Field              | Type   | Purpose                          |
|--------------------|--------|----------------------------------|
| `token`            | str    | The authentication token         |
| `valid_until`      | int    | Epoch seconds until expiry       |
| `key`              | str    | Key for HMAC validation          |
| `hash_alg`         | str    | Hash algorithm (e.g. SHA256)     |
| `unsecure_password`| bool   | Whether password is weak         |

`seconds_to_expire()` calculates remaining lifetime.

### `LxJsonKeySalt`

| Field       | Type   | Purpose                    |
|-------------|--------|----------------------------|
| `key`       | str    | HMAC key for auth          |
| `salt`      | str    | Server-provided salt       |
| `hash_alg`  | str    | Hash algorithm             |

## discover.py — LAN Discovery

Uses UDP broadcast to find Miniservers:

```
Client                                Network
  │                                      │
  │──── UDP broadcast ──────────────────►│  255.255.255.255:7070
  │     payload: "0x00"                  │
  │                                      │
  │◄──── "LoxLIVE: ... ip:port" ───────│  Response on 0.0.0.0:7071
  │                                      │
  │  regex parse → (ip, port)            │
```

## exceptions.py — Exception Hierarchy

```
LoxoneException (base)
├── LoxoneConnectionClosedOk        # Graceful close
├── LoxoneConnectionError           # Connection failure
├── LoxoneOutOfServiceException     # Miniserver rebooting
├── LoxoneHTTPStatusError           # Generic HTTP error
├── LoxoneRequestError              # Request-level error
├── LoxoneTokenError                # Token issue
├── LoxoneUnauthorisedError         # 401
├── LoxoneCommandError              # Command rejected
├── LoxoneTimeOutError              # Timeout
├── LoxoneServiceUnAvailableError   # 503
├── LoxoneMaxNumOfConnectionsError  # 429
├── LoxoneUnrecognizedCommandError  # 400
├── ConnectionFailure               # Alt connection failure
├── UnauthorizedError               # Alt 401
├── ResponseError                   # Response parse error
├── HttpApiError                    # HTTP API error
└── MessageError                    # Message parse error
```

**Note:** There is significant overlap — `LoxoneConnectionError` vs `ConnectionFailure`, `LoxoneUnauthorisedError` vs `UnauthorizedError`. This suggests organic growth without consolidation.

## const.py — Constants

| Group          | Constants                                                   |
|----------------|-------------------------------------------------------------|
| Reconnect      | `RECONNECT_DELAY=5`, `RECONNECT_TRIES=20`                  |
| WebSocket      | `MAX_WEBSOCKET_MESSAGE_SIZE=5*1024*1024` (5 MB)            |
| Timeouts       | `TIMEOUT=10`, `KEEP_ALIVE_PERIOD=120`                      |
| Crypto         | `IV_BYTES=16`, `AES_KEY_SIZE=32`, `SALT_BYTES=16`          |
| Salt           | `SALT_MAX_AGE_SECONDS=3600`, `SALT_MAX_USE_COUNT=30`       |
| Token          | `TOKEN_PERMISSION=2`, `MAX_REFRESH_DELAY=1800`             |
| Commands       | `CMD_GET_KEY`, `CMD_KEY_EXCHANGE`, `CMD_GET_TOKEN`, etc.    |

## Known Issues

### Bugs

| Severity | Issue | File:Line |
|----------|-------|-----------|
| **High** | `_last_header` can be `None` on first non-header message → `AttributeError` | `websocket_protocol.py:83` |
| **High** | `__main__.py` docstring says `username password host port` but code uses `host port username password` | `__main__.py` |
| **Medium** | Bare `except:` catches everything including `SystemExit`, `KeyboardInterrupt` | `message.py:230` |
| **Medium** | Duplicate exception handling for `ConnectionError`/`TimeoutError` in `open()` | `connection.py:596-623` |
| **Low** | `LoxoneToken.seconds_to_expire()` raises `ValueError` when `valid_until == 0` | `loxone_token.py` |
| **Low** | Typo `reponse` in `read_user_salt_response` | `loxone_token.py:31` |
| **Medium** | `send_websocket_command` doesn't check `is_connected` before enqueueing — commands pile up during disconnects | `connection.py:~1099` |

### Dead Code

| Item | Location | Notes |
|------|----------|-------|
| `helper.py` | Entire file | Never imported; `connection.py` has its own `_hash_token()` |
| `api.py` | Entire file | Empty placeholder; all API surface lives in `connection.py` |
| `hash_algorithms` dict | `helper.py` | Defined but never used |

### Missing Tests

The test suite is essentially non-functional:

- `test_run_alone.py` — loads env vars, does nothing
- `test_discover.py` — requires live network, no mocking

No tests exist for:
- Connection lifecycle
- Authentication and token management
- Message parsing (all types)
- AES encryption/decryption
- HTTP error handling
- Salt rotation
- Reconnection logic

### Security Observations

| Concern | Details |
|---------|---------|
| Credentials in memory | Plain text, never cleared |
| Token storage | Plain string, no secure wipe |
| Basic Auth over HTTP | No TLS enforcement |
| RSA padding | Uses PKCS1_v1_5 (legacy, not OAEP) |
| Hardcoded UUID | `edfc5f9a-df3f-4cad-9dddcdc42c732b82` in token requests |
| `detect_encoding` | Imports `chardet`-like detection but always returns True check |

### Design Concerns

1. **`connection.py` is a god object** — 1420 lines handling HTTP setup, WS lifecycle, encryption, token management, salt rotation, keep-alive, reconnection, and command dispatch. Should be decomposed.

2. **Dual exception hierarchies** — Two sets of overlapping exceptions (`LoxoneConnectionError` / `ConnectionFailure`, `LoxoneUnauthorisedError` / `UnauthorizedError`) suggest a partial refactor that was never completed.

3. **`api.py` is dead** — The intended API abstraction layer was never implemented. `connection.py` serves as both transport and API.

4. **No connection state abstraction** — `is_connected` checks `connection.protocol.state.name == "OPEN"` which depends on `websockets` library internals and can break across versions.

5. **Mixed `aiohttp` / `httpx` references** — Comments reference `httpx` but implementation uses `aiohttp`. `manifest.json` lists `httpx` as a dependency but the API layer doesn't use it.
