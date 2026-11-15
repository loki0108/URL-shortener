from app.utils import ALPHABET, generate_short_code


def test_default_length_is_7():
    assert len(generate_short_code()) == 7


def test_custom_length():
    assert len(generate_short_code(10)) == 10


def test_only_base62_characters():
    code = generate_short_code(100)
    assert all(ch in ALPHABET for ch in code)


def test_codes_are_random():
    codes = {generate_short_code() for _ in range(1000)}
    assert len(codes) == 1000  # no duplicates in 1000 tries