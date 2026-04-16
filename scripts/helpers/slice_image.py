#!/usr/bin/env python3
"""
Slice an image into a low-res gestalt for the parent and N full-res tiles
for workers, with optional offset-grid second-cut tiles (Chapter 12 boundary
trick). Uses Pillow.

Chapter 12 principle:
- Boss gets a downsampled view of the WHOLE image (gestalt)
- Workers get high-res tiles of pieces
- Offset grid ensures nothing important is lost at tile boundaries
"""
import argparse
import os
from PIL import Image


def make_gestalt(img: Image.Image, scale: float = 0.25) -> Image.Image:
    """Downsample image to low-res gestalt for the parent tier."""
    new_w = max(1, int(img.width * scale))
    new_h = max(1, int(img.height * scale))
    return img.resize((new_w, new_h), Image.LANCZOS)


def cut_grid(img: Image.Image, cols: int, rows: int,
             offset_x: int = 0, offset_y: int = 0) -> list:
    """Cut image into a grid of tiles.

    Returns list of (tile_image, label) tuples.
    offset_x/offset_y shift the grid origin for the offset-grid trick.
    """
    w, h = img.width, img.height
    tile_w = w // cols
    tile_h = h // rows
    tiles = []
    for r in range(rows):
        for c in range(cols):
            x0 = offset_x + c * tile_w
            y0 = offset_y + r * tile_h
            x1 = min(x0 + tile_w, w)
            y1 = min(y0 + tile_h, h)
            if x1 <= x0 or y1 <= y0:
                continue
            tile = img.crop((x0, y0, x1, y1))
            label = f"r{r}_c{c}"
            tiles.append((tile, label))
    return tiles


def main():
    parser = argparse.ArgumentParser(description="Slice image for hive processing")
    parser.add_argument("--input", required=True, help="Input image file")
    parser.add_argument("--output-dir", required=True, help="Output directory")
    parser.add_argument("--cols", type=int, default=2, help="Grid columns (default: 2)")
    parser.add_argument("--rows", type=int, default=2, help="Grid rows (default: 2)")
    parser.add_argument("--gestalt-scale", type=float, default=0.25,
                        help="Gestalt downscale factor (default: 0.25)")
    parser.add_argument("--offset-grid", action="store_true",
                        help="Also produce offset-grid tiles (Ch12 boundary trick)")
    args = parser.parse_args()

    img = Image.open(args.input)
    os.makedirs(args.output_dir, exist_ok=True)
    tiles_dir = os.path.join(args.output_dir, "tiles")
    os.makedirs(tiles_dir, exist_ok=True)

    print(f"Input: {args.input} ({img.width}x{img.height})")

    # Gestalt
    gestalt = make_gestalt(img, args.gestalt_scale)
    gestalt_path = os.path.join(args.output_dir, "gestalt.jpg")
    gestalt.save(gestalt_path, quality=85)
    print(f"Gestalt: {gestalt.width}x{gestalt.height} -> {gestalt_path}")

    # Primary grid
    primary = cut_grid(img, args.cols, args.rows)
    for tile, label in primary:
        path = os.path.join(tiles_dir, f"primary_{label}.jpg")
        tile.save(path, quality=95)
    print(f"Primary tiles: {len(primary)} ({args.cols}x{args.rows} grid)")

    # Offset grid (half-tile shifted)
    if args.offset_grid:
        offset_dir = os.path.join(args.output_dir, "tiles_offset")
        os.makedirs(offset_dir, exist_ok=True)
        tile_w = img.width // args.cols
        tile_h = img.height // args.rows
        offset_x = tile_w // 2
        offset_y = tile_h // 2
        offset = cut_grid(img, args.cols, args.rows, offset_x, offset_y)
        for tile, label in offset:
            path = os.path.join(offset_dir, f"offset_{label}.jpg")
            tile.save(path, quality=95)
        print(f"Offset tiles: {len(offset)} (shifted by {offset_x}x{offset_y}px)")

    print(f"Output: {args.output_dir}/")


if __name__ == "__main__":
    main()
