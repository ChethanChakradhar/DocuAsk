from __future__ import annotations

from app.core.security import (
    is_valid_passcode_shape,
    make_auth_token,
    verify_auth_token,
)


def test_passcode_must_be_four_digits():
    assert is_valid_passcode_shape("1234")
    assert not is_valid_passcode_shape("123")
    assert not is_valid_passcode_shape("abcd")


def test_auth_token_verification():
    token = make_auth_token("1234")

    assert verify_auth_token(token, "1234")
    assert not verify_auth_token(token, "0000")
