"""Reject the retired, publicly documented admin password without changing accounts.

The fingerprint identifies the old seeded hash, not a usable password or token.
A normal password reset creates a fresh salt/hash and restores account access.
"""
import hashlib
import hmac

_LEGACY_ADMIN_HASH_FINGERPRINT = "00c19be67097066437cbdd41f02a34e16099c207c7a4d8f0297ecc3a5e165038"


def requires_password_reset(user) -> bool:
    if user["role"] != "admin":
        return False
    fingerprint = hashlib.sha256(str(user["password_hash"]).encode("utf-8")).hexdigest()
    return hmac.compare_digest(fingerprint, _LEGACY_ADMIN_HASH_FINGERPRINT)
