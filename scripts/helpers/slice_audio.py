#!/usr/bin/env python3
"""
Slice an audio file into a low-res gestalt for the parent and N full-quality
chunks for workers. Uses ffmpeg.

Chapter 12 principle: boss gets low-fidelity gestalt of the WHOLE input,
workers get high-fidelity slices of pieces.
"""
import argparse
import os
import subprocess
import sys


def get_duration(path: str) -> float:
    """Get audio duration in seconds via ffprobe."""
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True
    )
    return float(result.stdout.strip())


def make_gestalt(input_path: str, output_path: str, sample_rate: int = 8000):
    """Downsample audio to low-res gestalt for the parent tier."""
    subprocess.run(
        ["ffmpeg", "-y", "-i", input_path,
         "-ar", str(sample_rate), "-ac", "1",
         output_path],
        check=True, capture_output=True
    )


def slice_chunks(input_path: str, output_dir: str, chunk_seconds: float = 10.0,
                 sample_rate: int = 16000):
    """Slice audio into N full-quality chunks at 16kHz mono WAV for STT."""
    duration = get_duration(input_path)
    os.makedirs(output_dir, exist_ok=True)
    chunks = []
    start = 0.0
    idx = 0
    while start < duration:
        end = min(start + chunk_seconds, duration)
        out_path = os.path.join(output_dir, f"chunk_{idx:04d}.wav")
        subprocess.run(
            ["ffmpeg", "-y", "-i", input_path,
             "-ss", str(start), "-to", str(end),
             "-ar", str(sample_rate), "-ac", "1",
             out_path],
            check=True, capture_output=True
        )
        chunks.append(out_path)
        start = end
        idx += 1
    return chunks


def main():
    parser = argparse.ArgumentParser(description="Slice audio for hive processing")
    parser.add_argument("--input", required=True, help="Input audio file")
    parser.add_argument("--output-dir", required=True, help="Output directory")
    parser.add_argument("--chunk-seconds", type=float, default=10.0,
                        help="Chunk duration in seconds (default: 10)")
    parser.add_argument("--gestalt-rate", type=int, default=8000,
                        help="Gestalt sample rate in Hz (default: 8000)")
    parser.add_argument("--chunk-rate", type=int, default=16000,
                        help="Chunk sample rate in Hz (default: 16000)")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    gestalt_path = os.path.join(args.output_dir, "gestalt.wav")
    chunks_dir = os.path.join(args.output_dir, "chunks")

    print(f"Input: {args.input}")
    duration = get_duration(args.input)
    print(f"Duration: {duration:.1f}s")

    print(f"Creating gestalt at {args.gestalt_rate}Hz...")
    make_gestalt(args.input, gestalt_path, args.gestalt_rate)

    print(f"Slicing into {args.chunk_seconds}s chunks at {args.chunk_rate}Hz...")
    chunks = slice_chunks(args.input, chunks_dir, args.chunk_seconds, args.chunk_rate)
    print(f"Created {len(chunks)} chunks")

    print(f"Output: {args.output_dir}/")
    print(f"  gestalt.wav  ({os.path.getsize(gestalt_path)} bytes)")
    print(f"  chunks/      ({len(chunks)} files)")


if __name__ == "__main__":
    main()
