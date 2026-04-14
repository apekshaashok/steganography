"""
=============================================================
  steg_visualise.py — Matrix Visualisation Suite
=============================================================
  Generates a 6-panel figure showing:
    1. Original image
    2. Encoded image (looks identical)
    3. Pixel difference map (amplified 50×)
    4. LSB matrix visualisation
    5. Pixel intensity histograms (overlay)
    6. Bit-plane analysis

  Run AFTER running the demo or encoding an image:
    python steg_visualise.py
    python steg_visualise.py original.png encoded.png
=============================================================
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from PIL import Image
import sys
import os


def load_pair(orig_path: str, enc_path: str):
    orig = np.array(Image.open(orig_path).convert("RGB"), dtype=np.uint8)
    enc  = np.array(Image.open(enc_path).convert("RGB"),  dtype=np.uint8)
    return orig, enc


def plot_all(orig_path: str, enc_path: str, save_path: str = "visualisation.png"):
    orig, enc = load_pair(orig_path, enc_path)
    diff = np.abs(orig.astype(int) - enc.astype(int)).astype(np.uint8)

    fig = plt.figure(figsize=(16, 10))
    fig.patch.set_facecolor('#0f1117')
    gs = gridspec.GridSpec(2, 3, figure=fig, hspace=0.38, wspace=0.28)

    title_kw  = dict(color='white', fontsize=11, fontweight='bold', pad=8)
    label_kw  = dict(color='#aaaaaa', fontsize=8)

    # ── Panel 1: Original ──────────────────────────────────────────
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.imshow(orig)
    ax1.set_title("1 · Original (carrier) image", **title_kw)
    ax1.axis('off')
    ax1.text(0.01, -0.04, f"Shape: {orig.shape}", transform=ax1.transAxes, **label_kw)

    # ── Panel 2: Encoded ───────────────────────────────────────────
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.imshow(enc)
    ax2.set_title("2 · Encoded image (looks identical)", **title_kw)
    ax2.axis('off')
    ax2.text(0.01, -0.04, "Secret message hidden inside pixel matrix", transform=ax2.transAxes, **label_kw)

    # ── Panel 3: Difference (amplified) ───────────────────────────
    ax3 = fig.add_subplot(gs[0, 2])
    diff_amp = np.clip(diff.astype(int) * 50, 0, 255).astype(np.uint8)
    ax3.imshow(diff_amp)
    ax3.set_title("3 · Pixel difference (50× amplified)", **title_kw)
    ax3.axis('off')
    pct = diff.astype(bool).sum() / diff.size * 100
    ax3.text(0.01, -0.04, f"Changed: {diff.astype(bool).sum():,} values ({pct:.1f}%)", transform=ax3.transAxes, **label_kw)

    # ── Panel 4: LSB matrix (greyscale) ───────────────────────────
    ax4 = fig.add_subplot(gs[1, 0])
    lsb_enc  = (enc[:, :, 0] & 1) * 255     # show LSB of Red channel only
    lsb_orig = (orig[:, :, 0] & 1) * 255
    combined = np.hstack([lsb_orig, lsb_enc])
    ax4.imshow(combined, cmap='plasma', vmin=0, vmax=255)
    ax4.set_title("4 · LSB matrix — Original | Encoded (R channel)", **title_kw)
    ax4.axis('off')
    ax4.text(0.01, -0.04, "Each dot = 1 bit. Left: random noise. Right: message bits.", transform=ax4.transAxes, **label_kw)

    # ── Panel 5: Intensity histograms ─────────────────────────────
    ax5 = fig.add_subplot(gs[1, 1])
    ax5.set_facecolor('#1a1d27')
    colors_orig = ['#ff6b6b', '#51cf66', '#74c0fc']
    colors_enc  = ['#c0392b', '#27ae60', '#2980b9']
    labels = ['Red', 'Green', 'Blue']
    for ch in range(3):
        ax5.hist(orig[:,:,ch].flatten(), bins=64, alpha=0.5,
                 color=colors_orig[ch], label=f'{labels[ch]} (orig)', density=True)
        ax5.hist(enc[:,:,ch].flatten(),  bins=64, alpha=0.3,
                 color=colors_enc[ch],  label=f'{labels[ch]} (enc)',  density=True, linestyle='--')
    ax5.set_title("5 · Pixel intensity histogram overlay", **title_kw)
    ax5.legend(fontsize=7, ncol=2, facecolor='#1a1d27', labelcolor='white', framealpha=0.5)
    ax5.tick_params(colors='#aaaaaa', labelsize=7)
    for spine in ax5.spines.values(): spine.set_color('#333')
    ax5.text(0.01, -0.08, "Histograms almost perfectly overlap — visually undetectable", transform=ax5.transAxes, **label_kw)

    # ── Panel 6: Bit-plane analysis ───────────────────────────────
    ax6 = fig.add_subplot(gs[1, 2])
    ax6.set_facecolor('#1a1d27')
    channel = enc[:, :, 0]   # Red channel
    planes = []
    for bit in range(8):
        plane = (channel >> bit) & 1
        planes.append(plane.mean())   # fraction of 1s in each bit plane

    bars = ax6.bar(range(8), planes, color=['#e74c3c' if b == 0 else '#3498db' for b in range(8)],
                   edgecolor='#555', linewidth=0.5)
    bars[0].set_color('#e74c3c')
    ax6.set_title("6 · Bit-plane statistics (Red channel)", **title_kw)
    ax6.set_xlabel("Bit plane (0 = LSB, 7 = MSB)", color='#aaaaaa', fontsize=8)
    ax6.set_ylabel("Fraction of 1s", color='#aaaaaa', fontsize=8)
    ax6.tick_params(colors='#aaaaaa', labelsize=7)
    for spine in ax6.spines.values(): spine.set_color('#333')
    ax6.set_ylim(0, 1)
    ax6.axhline(0.5, color='#ffffff', linestyle='--', linewidth=0.5, alpha=0.4)
    ax6.text(0.1, planes[0] + 0.04, 'message\nhere', color='#e74c3c', fontsize=7, ha='center')
    ax6.text(0.01, -0.12, "Bit 0 carries message. Higher bits hold true image data.", transform=ax6.transAxes, **label_kw)

    # ── Main title ─────────────────────────────────────────────────
    fig.suptitle("LSB Steganography — Matrix Visualisation Suite",
                 color='white', fontsize=14, fontweight='bold', y=0.98)

    # ── Footer ─────────────────────────────────────────────────────
    fig.text(0.5, 0.005,
             f"Original: {orig_path}   |   Encoded: {enc_path}   |   "
             f"Matrix shape: {orig.shape}   |   Max pixel diff: ±{diff.max()}",
             ha='center', color='#555555', fontsize=7)

    plt.savefig(save_path, dpi=150, bbox_inches='tight', facecolor='#0f1117')
    print(f"  Visualisation saved → {save_path}")
    plt.show()


if __name__ == "__main__":
    if len(sys.argv) == 3:
        orig_path = sys.argv[1]
        enc_path  = sys.argv[2]
    else:
        orig_path = "test_carrier.png"
        enc_path  = "encoded_secret.png"
        if not os.path.exists(orig_path):
            print(f"  Files not found. Run 'python steganography.py' first to generate demo files.")
            print(f"  Or: python steg_visualise.py <original.png> <encoded.png>")
            sys.exit(1)

    print(f"  Loading: {orig_path}  &  {enc_path}")
    plot_all(orig_path, enc_path, "visualisation.png")
