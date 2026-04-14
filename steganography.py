"""
=============================================================
  LSB Steganography — Hide & Reveal Secret Messages in Images
=============================================================
  Author  : Matrix Mini-Projects
  Concept : Modifies the Least Significant Bit (LSB) of each
            pixel value in the image matrix to embed text.
            The change per pixel is at most ±1, making it
            visually imperceptible to the human eye.
=============================================================
"""

import numpy as np
from PIL import Image
import os


# ─────────────────────────────────────────────
#  CONSTANTS
# ─────────────────────────────────────────────
DELIMITER = "<<END>>"   # Marks end of hidden message


# ─────────────────────────────────────────────
#  HELPER: Text ↔ Binary
# ─────────────────────────────────────────────

def text_to_bits(text: str) -> str:
    """
    Convert a string to a flat binary string.
    Uses UTF-8 encoding so ALL Unicode characters (including emoji)
    are correctly represented — each byte becomes 8 bits.
    """
    return ''.join(format(byte, '08b') for byte in text.encode('utf-8'))


def bits_to_text(bits: str) -> str:
    """
    Convert a flat binary string back to readable text.
    Decodes UTF-8 bytes so multi-byte characters (emoji, accents) work.
    """
    byte_list = [int(bits[i:i+8], 2) for i in range(0, len(bits) - 7, 8)]
    return bytes(byte_list).decode('utf-8', errors='ignore')


# ─────────────────────────────────────────────
#  CORE: ENCODE
# ─────────────────────────────────────────────

def encode(image_path: str, message: str, output_path: str) -> dict:
    """
    Embed a secret message into an image using LSB steganography.

    Matrix operations used:
      - img_array  : H × W × C  uint8 matrix of pixel values
      - flat       : 1D view of the matrix (all channels flattened)
      - LSB modify : flat[i] = (flat[i] & 0xFE) | bit
                     0xFE = 11111110  →  zeroes the LSB
                     | bit            →  sets it to 0 or 1

    Parameters
    ----------
    image_path  : path to the carrier image (PNG recommended)
    message     : the secret text to hide
    output_path : where to save the encoded image

    Returns a dict with stats about the operation.
    """
    # ── Load image as numpy matrix ──
    img = Image.open(image_path).convert("RGB")
    img_array = np.array(img, dtype=np.uint8)          # H × W × 3 matrix
    original_array = img_array.copy()

    H, W, C = img_array.shape
    total_pixels = H * W * C                            # total values in matrix

    # ── Prepare message bits ──
    full_message = message + DELIMITER                  # attach end marker
    msg_bits = text_to_bits(full_message)
    n_bits = len(msg_bits)

    # ── Capacity check ──
    if n_bits > total_pixels:
        raise ValueError(
            f"Message too long! Need {n_bits} bits but image only holds "
            f"{total_pixels} bits ({total_pixels // 8} characters max)."
        )

    # ── Flatten matrix for sequential bit embedding ──
    flat = img_array.flatten()                          # 1D view of the matrix

    # ── Embed: replace LSB of each matrix element ──
    for i, bit in enumerate(msg_bits):
        flat[i] = (flat[i] & 0xFE) | int(bit)
        #           ^^^^^^^^^^^^^^^^^^  zero out the LSB
        #                              ^^^^^^^^  set it to message bit

    # ── Reshape back to H × W × 3 and save ──
    encoded_array = flat.reshape(H, W, C)
    encoded_img = Image.fromarray(encoded_array, "RGB")
    encoded_img.save(output_path, format="PNG")         # PNG = lossless (crucial!)

    # ── Compute difference statistics ──
    diff = np.abs(original_array.astype(int) - encoded_array.astype(int))
    changed_pixels = np.count_nonzero(diff)
    max_diff = int(diff.max())    # will always be 0 or 1

    capacity_chars = total_pixels // 8

    return {
        "message_length"    : len(message),
        "bits_used"         : n_bits,
        "total_capacity"    : total_pixels,
        "capacity_chars"    : capacity_chars,
        "pixels_changed"    : changed_pixels,
        "max_pixel_diff"    : max_diff,
        "image_size"        : f"{W} × {H}",
        "output_path"       : output_path,
    }


# ─────────────────────────────────────────────
#  CORE: DECODE
# ─────────────────────────────────────────────

def decode(image_path: str) -> str:
    """
    Extract a hidden message from an LSB-encoded image.

    Matrix operations used:
      - img_array : H × W × C  uint8 matrix
      - flat      : 1D view — read LSB of each element
      - LSB read  : flat[i] & 1  →  extracts the last bit

    Parameters
    ----------
    image_path : path to the encoded image

    Returns the hidden message string, or raises if none found.
    """
    # ── Load as matrix ──
    img = Image.open(image_path).convert("RGB")
    img_array = np.array(img, dtype=np.uint8)

    # ── Flatten and extract all LSBs in one vectorised operation ──
    flat = img_array.flatten()
    lsb_array = flat & 1                               # extract LSB: matrix & 00000001

    # ── Convert LSB array to bit string ──
    bits = ''.join(str(b) for b in lsb_array)

    # ── Read 8 bits at a time into bytes, UTF-8 decode, watch for delimiter ──
    byte_list = []
    for i in range(0, len(bits) - 7, 8):
        byte_list.append(int(bits[i:i+8], 2))
        try:
            decoded = bytes(byte_list).decode('utf-8')
            if decoded.endswith(DELIMITER):
                return decoded[: -len(DELIMITER)]       # strip the end marker
        except UnicodeDecodeError:
            pass   # mid-multibyte character, keep accumulating
        if len(byte_list) > 500_000:
            break

    raise ValueError(
        "No hidden message found, or image was re-compressed (use PNG, not JPEG)."
    )


# ─────────────────────────────────────────────
#  UTILITY: Generate a test image
# ─────────────────────────────────────────────

def generate_test_image(path: str = "test_carrier.png",
                        size: tuple = (400, 300)) -> None:
    """
    Create a colourful gradient test image if you don't have one handy.
    The gradient is built entirely from NumPy matrix operations.
    """
    W, H = size
    # Build coordinate matrices
    x = np.linspace(0, 255, W, dtype=np.uint8)
    y = np.linspace(0, 255, H, dtype=np.uint8)
    X, Y = np.meshgrid(x, y)                           # H × W coordinate matrices

    # Combine into an RGB matrix: R=X, G=Y, B=255-X (pure matrix math)
    img_array = np.stack([X, Y, (255 - X).astype(np.uint8)], axis=2)
    Image.fromarray(img_array, "RGB").save(path)
    print(f"  Test image saved → {path}  ({W}×{H} px)")


# ─────────────────────────────────────────────
#  UTILITY: Visual diff analyser
# ─────────────────────────────────────────────

def analyse_diff(original_path: str, encoded_path: str) -> None:
    """
    Load both images as matrices and print a statistical comparison.
    Demonstrates how the pixel values change (spoiler: almost nothing).
    """
    orig = np.array(Image.open(original_path).convert("RGB"), dtype=int)
    enc  = np.array(Image.open(encoded_path).convert("RGB"),  dtype=int)

    diff = np.abs(orig - enc)
    total = orig.size

    print("\n  ┌─────────────────────────────────────────┐")
    print("  │         Matrix Difference Analysis       │")
    print("  ├─────────────────────────────────────────┤")
    print(f"  │  Matrix shape       : {orig.shape}        │")
    print(f"  │  Total matrix cells : {total:,}              │")
    print(f"  │  Cells changed      : {diff.astype(bool).sum():,}               │")
    print(f"  │  Max pixel diff     : {diff.max()} (always 0 or 1)  │")
    print(f"  │  Mean pixel diff    : {diff.mean():.6f}           │")
    print(f"  │  PSNR (quality)     : {'∞ (identical)' if diff.max()==0 else f'{10 * np.log10(255**2 / (diff**2).mean()):.2f} dB':<20} │")
    print("  └─────────────────────────────────────────┘\n")


# ─────────────────────────────────────────────
#  DEMO: Run everything end-to-end
# ─────────────────────────────────────────────

def run_demo():
    print("=" * 60)
    print("   LSB Steganography — Full Demo")
    print("=" * 60)

    carrier   = "test_carrier.png"
    encoded   = "encoded_secret.png"
    secret    = "Hello! This secret message is hidden inside the image matrix using LSB steganography. Nobody can see it! 🔐"

    # Step 1 — Generate test image
    print("\n[1] Generating test carrier image...")
    generate_test_image(carrier, size=(600, 400))

    # Step 2 — Encode
    print(f"\n[2] Hiding secret message ({len(secret)} chars)...")
    stats = encode(carrier, secret, encoded)
    print(f"  Message       : \"{secret[:50]}...\"")
    print(f"  Bits used     : {stats['bits_used']:,} / {stats['total_capacity']:,} available")
    print(f"  Capacity      : {stats['capacity_chars']:,} characters max")
    print(f"  Pixels changed: {stats['pixels_changed']:,}")
    print(f"  Max pixel diff: ±{stats['max_pixel_diff']} (invisible to human eye)")
    print(f"  Saved to      : {stats['output_path']}")

    # Step 3 — Decode
    print(f"\n[3] Extracting hidden message from '{encoded}'...")
    recovered = decode(encoded)
    print(f"  Recovered: \"{recovered}\"")
    print(f"  Match    : {'✓ PERFECT' if recovered == secret else '✗ MISMATCH'}")

    # Step 4 — Matrix diff analysis
    print("\n[4] Analysing matrix differences...")
    analyse_diff(carrier, encoded)

    print("Demo complete! Files created:")
    print(f"  • {carrier}  — original carrier image")
    print(f"  • {encoded}  — image with hidden message")


if __name__ == "__main__":
    run_demo()
