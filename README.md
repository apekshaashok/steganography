# LSB Image Steganography
### Hide secret messages inside image pixel matrices

---

## What This Project Does

This project lets you **hide any text message inside a PNG image** using a technique called **Least Significant Bit (LSB) steganography**. The encoded image looks completely identical to the original — the difference between the two is at most **±1 per pixel**, which is far below what the human eye can detect.

```
Original image  ──encode──▶  Encoded image  ──decode──▶  Secret message
   (carrier)      (secret)   (looks same!)    (extract)   recovered ✓
```

---

## How It Works — The Matrix Concept

Every image is stored as a matrix of integers:

```
Greyscale image → H × W matrix         (each value: 0–255)
Colour image    → H × W × 3 matrix     (R, G, B channels)
```

Each value is an 8-bit integer:

```
Pixel value 200  =  binary  1 1 0 0 1 0 0 0
                             ↑               ↑
                       bit 7 (MSB)     bit 0 (LSB)
```

The **Least Significant Bit** contributes only ±1 to the pixel value.
Changing it is completely invisible. We use it to store message bits:

```
Message: "Hi"
H = 72  → 01001000
i = 105 → 01101001
Full bitstream: 0100100001101001...

Pixel 1 = 200 = 11001000  → replace LSB with 0 → 11001000 = 200  (no change)
Pixel 2 = 150 = 10010110  → replace LSB with 1 → 10010111 = 151  (±1 change)
Pixel 3 = 85  = 01010101  → replace LSB with 0 → 01010100 = 84   (±1 change)
...and so on
```

The end of the message is marked with a delimiter `<<END>>` so the decoder knows where to stop.

---

## File Structure

```
steganography/
│
├── steganography.py      ← Core library (encode, decode, helpers)
├── steg_cli.py           ← Interactive command-line interface
├── steg_visualise.py     ← 6-panel visualisation of the matrix changes
├── test_steganography.py ← Full test suite
├── requirements.txt      ← Python dependencies
└── README.md             ← This file
```

---

## Installation

### 1. Make sure Python 3.8+ is installed
```bash
python --version
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```
That installs: **NumPy**, **Pillow** (image I/O), **Matplotlib** (visualisation).

---

## Usage

### ▶ Option A — Quick Demo (recommended first step)
Generates a test image, hides a message, recovers it, and prints statistics:
```bash
python steganography.py
```

You'll see output like:
```
[1] Generating test carrier image...
    Test image saved → test_carrier.png  (600×400 px)

[2] Hiding secret message (102 chars)...
    Bits used     : 872 / 720,000 available
    Pixels changed: 523
    Max pixel diff: ±1 (invisible to human eye)

[3] Extracting hidden message from 'encoded_secret.png'...
    Recovered: "Hello! This secret message is hidden..."
    Match    : ✓ PERFECT
```

---

### ▶ Option B — Interactive CLI

```bash
python steg_cli.py
```
Then type `encode`, `decode`, or `demo`.

**Or directly:**
```bash
# Hide a message
python steg_cli.py encode

# Reveal a message
python steg_cli.py decode

# Check how much text an image can hold
python steg_cli.py capacity photo.png
```

---

### ▶ Option C — Use as a Library in your own script

```python
from steganography import encode, decode

# Hide a message
stats = encode("my_photo.png", "Secret: meet at midnight", "output.png")
print(f"Used {stats['bits_used']} bits, changed {stats['pixels_changed']} pixels")

# Recover it
message = decode("output.png")
print(message)  # → "Secret: meet at midnight"
```

---

### ▶ Option D — Visualise the matrix changes

Run this AFTER encoding to generate a 6-panel analysis figure:
```bash
python steg_visualise.py
# or with custom files:
python steg_visualise.py original.png encoded.png
```

Generates `visualisation.png` showing:
1. Original image
2. Encoded image (looks identical)
3. Pixel difference map (amplified 50×)
4. LSB matrix side-by-side
5. Intensity histogram overlay
6. Bit-plane statistics

---

### ▶ Option E — Run the test suite

```bash
python test_steganography.py
```

---

## API Reference

### `encode(image_path, message, output_path) → dict`
Hides `message` inside the image at `image_path`, saves to `output_path`.
Returns stats dict with keys:
- `message_length` — number of characters hidden
- `bits_used` — total bits embedded
- `total_capacity` — total LSBs available
- `capacity_chars` — max characters this image can hold
- `pixels_changed` — number of matrix values modified
- `max_pixel_diff` — always 0 or 1

### `decode(image_path) → str`
Extracts and returns the hidden message from the image.
Raises `ValueError` if no message is found.

### `generate_test_image(path, size) → None`
Creates a colourful gradient PNG for testing (no external image needed).

### `analyse_diff(original_path, encoded_path) → None`
Prints a matrix comparison report including PSNR quality metric.

---

## Important Rules

| Rule | Why |
|------|-----|
| **Always save output as PNG** | PNG is lossless. JPEG re-compression shuffles pixel values and destroys hidden bits. |
| **Never re-save as JPEG** | Even one JPEG save will corrupt the message. |
| **Image must be same or larger** | The carrier image must have enough pixels to hold your message. |
| **The carrier stays unchanged visually** | Max ±1 per pixel. Undetectable. |

### Capacity guide
| Image size | Max message length |
|---|---|
| 100 × 100 px | ~3,700 characters |
| 500 × 500 px | ~93,700 characters |
| 1920 × 1080 px | ~746,000 characters |

Formula: `capacity = (width × height × 3) / 8` characters

---

## Key Matrix Operations Used

```python
# 1. Load image as numpy matrix
img_array = np.array(Image.open(path))     # shape: (H, W, 3)

# 2. Flatten to 1D for sequential bit access
flat = img_array.flatten()

# 3. Embed: zero out LSB, then set it to message bit
flat[i] = (flat[i] & 0xFE) | int(bit)
#           ──────────────    ─────────
#           0xFE = 11111110   message bit (0 or 1)
#           zeroes the LSB

# 4. Extract: read LSB of every element
lsb_array = flat & 1                       # vectorised! extracts all LSBs at once

# 5. Reshape back to image
encoded = flat.reshape(H, W, 3)
```

---

## Extensions to Try

1. **Multi-image splitting** — split message across 3 images for added security
2. **Encrypted steganography** — XOR the message bits with a key before embedding
3. **Audio steganography** — same LSB technique applied to WAV file sample arrays
4. **Adaptive LSB** — use 2 or 3 LSBs in smooth (low-detail) regions for higher capacity
5. **Statistical steganalysis** — try to *detect* whether an image has a hidden message

---

## Dependencies
- `numpy` — matrix operations
- `Pillow` — image loading and saving
- `matplotlib` — visualisation only (not needed for encode/decode)
