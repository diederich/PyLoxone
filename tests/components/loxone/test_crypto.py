"""Tests for the pyloxone_api.crypto module — pure cryptographic functions."""

from custom_components.loxone.pyloxone_api.crypto import (
    decrypt_command,
    encrypt_command,
    generate_aes_key,
    generate_iv,
    generate_salt,
    hash_credentials,
    hash_secure_command,
    hash_token,
    new_salt_needed,
    parse_public_key,
    time_elapsed_in_seconds,
)


class TestKeyGeneration:
    def test_aes_key_is_32_bytes(self):
        key = generate_aes_key()
        assert len(key) == 32
        assert isinstance(key, bytes)

    def test_iv_is_16_bytes(self):
        iv = generate_iv()
        assert len(iv) == 16
        assert isinstance(iv, bytes)

    def test_salt_is_hex_string(self):
        salt = generate_salt()
        assert len(salt) == 32  # 16 bytes = 32 hex chars
        bytes.fromhex(salt)  # should not raise

    def test_generated_values_are_random(self):
        assert generate_aes_key() != generate_aes_key()
        assert generate_iv() != generate_iv()
        assert generate_salt() != generate_salt()


class TestSaltExpiry:
    def test_fresh_salt_not_expired(self):
        assert not new_salt_needed(0, time_elapsed_in_seconds())

    def test_salt_expires_by_count(self):
        assert new_salt_needed(101, time_elapsed_in_seconds())

    def test_salt_expires_by_age(self):
        old_timestamp = time_elapsed_in_seconds() - 3601
        assert new_salt_needed(0, old_timestamp)

    def test_salt_within_limits(self):
        recent = time_elapsed_in_seconds() - 100
        assert not new_salt_needed(5, recent)


class TestAesRoundtrip:
    def test_encrypt_then_decrypt(self):
        key = generate_aes_key()
        iv = generate_iv()
        salt = generate_salt()
        original = "jdev/sps/io/abc123/1"

        encrypted = encrypt_command(key, iv, salt, original)
        assert encrypted.startswith("jdev/sys/enc/")

        # Extract the encrypted part and decrypt
        enc_part = encrypted[len("jdev/sys/enc/") :]
        from urllib.parse import unquote

        full_enc = f"jdev/sys/enc/{unquote(enc_part)}"
        decrypted = decrypt_command(key, iv, full_enc).decode("utf-8")

        assert f"salt/{salt}/{original}" == decrypted

    def test_encrypt_with_salt_rotation(self):
        key = generate_aes_key()
        iv = generate_iv()
        old_salt = generate_salt()
        new_salt = generate_salt()

        encrypted = encrypt_command(key, iv, new_salt, "test_cmd", old_salt=old_salt)
        assert encrypted.startswith("jdev/sys/enc/")

        from urllib.parse import unquote

        enc_part = encrypted[len("jdev/sys/enc/") :]
        full_enc = f"jdev/sys/enc/{unquote(enc_part)}"
        decrypted = decrypt_command(key, iv, full_enc).decode("utf-8")

        assert decrypted.startswith(f"nextSalt/{old_salt}/{new_salt}/")


class TestHashFunctions:
    def test_hash_credentials_sha256(self):
        result = hash_credentials(
            username="admin",
            password="secret",
            user_salt="aabbccdd",
            key="0011223344556677",
            hash_alg="SHA256",
        )
        assert result is not None
        assert isinstance(result, str)
        assert len(result) == 64  # SHA256 hex digest

    def test_hash_credentials_sha1(self):
        result = hash_credentials(
            username="admin",
            password="secret",
            user_salt="aabbccdd",
            key="0011223344556677",
            hash_alg="SHA1",
        )
        assert result is not None
        assert len(result) == 40  # SHA1 hex digest

    def test_hash_credentials_unknown_alg(self):
        result = hash_credentials("a", "b", "c", "0011", "MD5")
        assert result is None

    def test_hash_credentials_invalid_key(self):
        result = hash_credentials("a", "b", "c", "not-hex!", "SHA256")
        assert result is None

    def test_hash_token_sha256(self):
        result = hash_token("mytoken", "0011223344556677", "SHA256")
        assert result is not None
        assert len(result) == 64

    def test_hash_token_unknown_alg(self):
        assert hash_token("tok", "0011", "MD5") is None

    def test_hash_token_invalid_key(self):
        assert hash_token("tok", "zzzz", "SHA256") is None

    def test_hash_secure_command(self):
        result = hash_secure_command(
            code="1234",
            visual_hash_key="0011223344556677",
            visual_hash_salt="aabbccdd",
            visual_hash_alg="SHA256",
            device_uuid="abc-123",
            value="1",
        )
        assert result is not None
        assert result.startswith("jdev/sps/ios/")
        assert "abc-123" in result

    def test_hash_secure_command_bad_alg(self):
        result = hash_secure_command("1234", "00", "aa", "UNKNOWN", "u", "v")
        assert result is None


class TestParsePublicKey:
    def test_converts_certificate_markers(self):
        raw = "-----BEGIN CERTIFICATE-----KEYDATA-----END CERTIFICATE-----"
        result = parse_public_key(raw)
        assert "-----BEGIN PUBLIC KEY-----" in result
        assert "-----END PUBLIC KEY-----" in result
        assert "CERTIFICATE" not in result

    def test_preserves_already_correct_format(self):
        raw = "-----BEGIN PUBLIC KEY-----\nKEYDATA\n-----END PUBLIC KEY-----\n"
        result = parse_public_key(raw)
        assert result == raw
