import secrets
import string

# Base62 alphabet: a-z, A-Z, 0-9  (62 characters, all URL-safe)
ALPHABET = string.ascii_letters + string.digits


def generate_short_code(length: int = 7) -> str:
    """Return a random base62 code, e.g. 'aZ3k9Qx'.

    62^7 ≈ 3.5 trillion possible codes, so collisions are very rare.
    """
    return "".join(secrets.choice(ALPHABET) for _ in range(length))