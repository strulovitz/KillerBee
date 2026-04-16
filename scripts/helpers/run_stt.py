#!/usr/bin/env python3
"""
Run speech-to-text on one audio file using the tier's STT model.
Handles load/unload discipline — only one model resident at a time.

Tiers:
  worker_tiny   -> Moonshine Tiny (27M) via moonshine-onnx
  worker_small  -> Moonshine Base (61M) via moonshine-onnx
  dwarfqueen_small  -> Whisper small via whisper.cpp
  dwarfqueen_medium -> Whisper medium via whisper.cpp
  giantqueen    -> Whisper Large v3 Turbo via whisper.cpp
  rajabee       -> Cohere Transcribe via HF Transformers
"""
import argparse
import os
import subprocess
import sys


def run_moonshine(audio_path: str, model_name: str) -> str:
    """Run Moonshine STT (worker tiers)."""
    try:
        from moonshine_onnx import MoonshineOnnxModel, load_audio
        model = MoonshineOnnxModel(model_name=model_name)
        audio = load_audio(audio_path)
        tokens = model.generate(audio)
        text = model.tokenizer.decode(tokens[0])
        del model  # unload
        return text
    except ImportError:
        return f"ERROR: moonshine_onnx not installed"


def run_whisper_cpp(audio_path: str, model_size: str) -> str:
    """Run whisper.cpp STT (DwarfQueen and GiantQueen tiers)."""
    whisper_dir = "/opt/killerbee/src/whisper.cpp"
    main_bin = os.path.join(whisper_dir, "main")
    if not os.path.exists(main_bin):
        # Try the build directory
        main_bin = os.path.join(whisper_dir, "build", "bin", "whisper-cli")
    if not os.path.exists(main_bin):
        return f"ERROR: whisper.cpp binary not found"

    model_path = os.path.join(whisper_dir, "models", f"ggml-{model_size}.bin")
    if not os.path.exists(model_path):
        return f"ERROR: model not found at {model_path}"

    result = subprocess.run(
        [main_bin, "-m", model_path, "-f", audio_path,
         "--no-timestamps", "--print-colors", "false", "-l", "en"],
        capture_output=True, text=True, timeout=300
    )
    if result.returncode != 0:
        return f"ERROR: whisper.cpp failed: {result.stderr[:200]}"
    return result.stdout.strip()


def run_cohere_transcribe(audio_path: str) -> str:
    """Run Cohere Transcribe STT (RajaBee tier)."""
    try:
        import torch
        from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor
        import soundfile as sf

        model_dir = "/opt/killerbee/models/cohere-transcribe"
        processor = AutoProcessor.from_pretrained(model_dir)
        model = AutoModelForSpeechSeq2Seq.from_pretrained(model_dir, torch_dtype=torch.float32)

        audio, sr = sf.read(audio_path)
        inputs = processor(audio, sampling_rate=sr, return_tensors="pt")
        generated_ids = model.generate(**inputs)
        text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]

        del model, processor  # unload
        return text
    except ImportError as e:
        return f"ERROR: missing dependency: {e}"


def main():
    parser = argparse.ArgumentParser(description="Run STT on one audio file")
    parser.add_argument("--tier", required=True,
                        choices=["worker_tiny", "worker_small",
                                 "dwarfqueen_small", "dwarfqueen_medium",
                                 "giantqueen", "rajabee"])
    parser.add_argument("--input", required=True, help="Input WAV file (16kHz mono)")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"ERROR: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    tier_map = {
        # Workers use Whisper tiny via whisper.cpp (SILVER fallback).
        # Moonshine ONNX (GOLD) was dropped because the PyPI package
        # (useful-moonshine) requires tensorflow, too heavy for 4GB workers.
        "worker_tiny": ("whisper", "tiny"),
        "worker_small": ("whisper", "base"),
        "dwarfqueen_small": ("whisper", "small"),
        "dwarfqueen_medium": ("whisper", "medium"),
        "giantqueen": ("whisper", "large-v3-turbo"),
        "rajabee": ("cohere", None),
    }

    runtime, model_id = tier_map[args.tier]

    if runtime == "moonshine":
        text = run_moonshine(args.input, model_id)
    elif runtime == "whisper":
        text = run_whisper_cpp(args.input, model_id)
    elif runtime == "cohere":
        text = run_cohere_transcribe(args.input)

    print(text)


if __name__ == "__main__":
    main()
