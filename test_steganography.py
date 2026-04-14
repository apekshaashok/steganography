"""
=============================================================
  test_steganography.py — Test Suite
=============================================================
  Run with:  python test_steganography.py
=============================================================
"""

import numpy as np
from PIL import Image
import os
import sys
from steganography import encode, decode, text_to_bits, bits_to_text, generate_test_image

PASS = "  ✓ PASS"
FAIL = "  ✗ FAIL"


def test_text_conversion():
    """Test that text → bits → text round-trips correctly."""
    samples = ["Hello", "Secret 123!", "🔐 Unicode", "A" * 100]
    for s in samples:
        bits = text_to_bits(s)
        recovered = bits_to_text(bits)
        status = PASS if recovered == s else FAIL
        print(f"{status}  text_to_bits round-trip: '{s[:20]}'")


def test_encode_decode_short():
    """Short message in a medium image."""
    generate_test_image("_test_img.png", size=(200, 200))
    msg = "Hello, World!"
    encode("_test_img.png", msg, "_test_enc.png")
    recovered = decode("_test_enc.png")
    status = PASS if recovered == msg else FAIL
    print(f"{status}  Short message encode/decode: '{msg}'")
    os.remove("_test_img.png"); os.remove("_test_enc.png")


def test_encode_decode_long():
    """Long message — fills most of the image."""
    generate_test_image("_test_img2.png", size=(100, 100))
    img = np.array(Image.open("_test_img2.png"))
    max_chars = img.size // 8 - 7
    msg = "X" * (max_chars - 10)
    encode("_test_img2.png", msg, "_test_enc2.png")
    recovered = decode("_test_enc2.png")
    status = PASS if recovered == msg else FAIL
    print(f"{status}  Long message ({len(msg)} chars) encode/decode")
    os.remove("_test_img2.png"); os.remove("_test_enc2.png")


def test_pixel_diff_is_0_or_1():
    """Verify max pixel change is exactly 0 or 1."""
    generate_test_image("_test_img3.png", size=(200, 200))
    orig = np.array(Image.open("_test_img3.png"), dtype=int)
    encode("_test_img3.png", "Test message for diff check", "_test_enc3.png")
    enc = np.array(Image.open("_test_enc3.png"), dtype=int)
    diff = np.abs(orig - enc)
    max_d = diff.max()
    status = PASS if max_d <= 1 else FAIL
    print(f"{status}  Max pixel difference is {max_d} (must be ≤ 1)")
    os.remove("_test_img3.png"); os.remove("_test_enc3.png")


def test_capacity_error():
    """Encoding a message that's too long should raise ValueError."""
    generate_test_image("_test_small.png", size=(10, 10))
    huge_msg = "A" * 10000
    try:
        encode("_test_small.png", huge_msg, "_test_over.png")
        print(f"{FAIL}  Overflow error should have been raised")
    except ValueError:
        print(f"{PASS}  Overflow correctly raises ValueError")
    finally:
        os.remove("_test_small.png")
        if os.path.exists("_test_over.png"):
            os.remove("_test_over.png")


def test_no_message_raises():
    """Decoding an image with no message should raise ValueError."""
    generate_test_image("_test_no_msg.png", size=(100, 100))
    try:
        decode("_test_no_msg.png")
        print(f"{FAIL}  Should have raised ValueError for missing message")
    except ValueError:
        print(f"{PASS}  Missing message correctly raises ValueError")
    finally:
        os.remove("_test_no_msg.png")


def test_special_characters():
    """Messages with special characters, spaces, newlines."""
    generate_test_image("_test_special.png", size=(300, 200))
    msg = "Line 1\nLine 2\tTabbed\n!@#$%^&*()_+-=[]{}|;':\",./<>?"
    encode("_test_special.png", msg, "_test_special_enc.png")
    recovered = decode("_test_special_enc.png")
    status = PASS if recovered == msg else FAIL
    print(f"{status}  Special characters (newline, tab, symbols)")
    os.remove("_test_special.png"); os.remove("_test_special_enc.png")


def run_all():
    print("\n" + "=" * 55)
    print("  LSB Steganography — Test Suite")
    print("=" * 55 + "\n")

    tests = [
        ("Text conversion round-trip",  test_text_conversion),
        ("Short message encode/decode", test_encode_decode_short),
        ("Long message encode/decode",  test_encode_decode_long),
        ("Pixel diff ≤ 1",              test_pixel_diff_is_0_or_1),
        ("Overflow error handling",     test_capacity_error),
        ("No-message error handling",   test_no_message_raises),
        ("Special characters",          test_special_characters),
    ]

    for name, fn in tests:
        try:
            fn()
        except Exception as e:
            print(f"  ✗ FAIL  {name} — Exception: {e}")

    print("\n" + "=" * 55)
    print("  All tests complete.")
    print("=" * 55 + "\n")


if __name__ == "__main__":
    run_all()
