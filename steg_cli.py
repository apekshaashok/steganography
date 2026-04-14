import sys
import os
from steganography import encode, decode, generate_test_image, analyse_diff
import numpy as np
from PIL import Image


def banner():
    print("""
╔══════════════════════════════════════════════════════════╗
║         LSB Image Steganography — CLI Tool               ║
║         Hide secret messages inside image matrices       ║
╚══════════════════════════════════════════════════════════╝
""")


def cmd_encode():
    print("── ENCODE MODE ─────────────────────────────────────────\n")
    carrier = input("  Carrier image path (e.g. photo.png): ").strip()
    if not os.path.exists(carrier):
        print(f"  File not found: {carrier}")
        return

    img = Image.open(carrier).convert("RGB")
    arr = np.array(img)
    capacity = arr.size // 8

    print(f"  Image size    : {img.width} x {img.height} px")
    print(f"  Max capacity  : {capacity:,} characters\n")

    message = input("  Secret message to hide: ").strip()
    if len(message) + 7 > capacity:
        print(f"  Message too long ({len(message)} chars). Max is {capacity - 7}.")
        return

    default_out = "encoded_" + os.path.basename(carrier).replace(".jpg","").replace(".jpeg","") + ".png"
    out = input(f"  Output path [{default_out}]: ").strip() or default_out

    if not out.endswith(".png"):
        out += ".png"

    print("\n  Encoding...")
    stats = encode(carrier, message, out)

    print(f"""
  Message hidden successfully!
  ─────────────────────────────────────────
  Message length  : {stats['message_length']} characters
  Bits embedded   : {stats['bits_used']:,}
  Pixels changed  : {stats['pixels_changed']:,}
  Max pixel diff  : ±{stats['max_pixel_diff']}
  Output saved to : {stats['output_path']}
  ─────────────────────────────────────────
  IMPORTANT: Share the .png file. Never re-save as JPEG.
""")


def cmd_decode():
    print("── DECODE MODE ─────────────────────────────────────────\n")
    path = input("  Path to encoded image: ").strip()

    if not os.path.exists(path):
        print(f"  File not found: {path}")
        return

    print("\n  Scanning image matrix for hidden message...")

    try:
        message = decode(path)
        print(f"""
  Hidden message found!
  ─────────────────────────────────────────
  Message ({len(message)} chars):

    {message}

  ─────────────────────────────────────────
""")
    except ValueError as e:
        print(f"\n  {e}")


def cmd_capacity(image_path: str):
    print(f"── CAPACITY CHECK: {image_path} ─────────────────────\n")

    if not os.path.exists(image_path):
        print(f"  File not found: {image_path}")
        return

    img = Image.open(image_path).convert("RGB")
    arr = np.array(img)

    total_bits = arr.size
    capacity_chars = total_bits // 8 - 7

    print(f"  Image dimensions : {img.width} x {img.height} pixels")
    print(f"  Matrix shape     : {arr.shape}")
    print(f"  Total values     : {arr.size:,}")
    print(f"  Usable LSBs      : {total_bits:,} bits")
    print(f"  Text capacity    : ~{capacity_chars:,} characters")
    print(f"                   : ~{capacity_chars // 1000}K characters\n")


def cmd_demo():
    print("── DEMO MODE ───────────────────────────────────────────\n")
    from steganography import run_demo
    run_demo()


def main():
    banner()

    if len(sys.argv) < 2:
        print("  Commands:")
        print("    python steg_cli.py encode")
        print("    python steg_cli.py decode")
        print("    python steg_cli.py demo")
        print("    python steg_cli.py capacity <img.png>")
        print()

        choice = input("  Enter command [encode / decode / demo]: ").strip().lower()
        sys.argv.append(choice)

    cmd = sys.argv[1].lower()

    if cmd == "encode":
        cmd_encode()
    elif cmd == "decode":
        cmd_decode()
    elif cmd == "demo":
        cmd_demo()
    elif cmd == "capacity" and len(sys.argv) > 2:
        cmd_capacity(sys.argv[2])
    else:
        print(f"  Unknown command: '{cmd}'")
        print("  Use: encode | decode | demo | capacity <path>")


if __name__ == "__main__":
    main()