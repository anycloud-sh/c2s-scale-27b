#!/usr/bin/env python3
"""Run the pinned C2S-Scale-Gemma-2-27B cell-type prediction example."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any


MODEL_ID = "vandijklab/C2S-Scale-Gemma-2-27B"
MODEL_REVISION = "44c2ff7dd5edc26daf9c3f4106e18e162a55676a"
SOURCE_REVISION = "a6efaf079f98491d4723ced44b929936b94368aa"
DEFAULT_INPUT = Path("/opt/c2s/examples/immune-tissue-natural-killer-cell.json")
MINIMUM_GENES = 200
MINIMUM_VRAM_BYTES = 64 * 1024**3


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Predict a cell type with the pinned C2S-Scale-Gemma-2-27B model. "
            "Input genes must be ranked from highest to lowest expression."
        )
    )
    parser.add_argument(
        "--input",
        type=Path,
        help=(
            "JSON file with genes, organism, and optional cell_id and "
            "expected_cell_type. Defaults to the bundled upstream test cell."
        ),
    )
    parser.add_argument(
        "--genes",
        help="Space-separated ranked gene names; takes precedence over --input.",
    )
    parser.add_argument(
        "--organism",
        help="Organism name used in the prompt (default: value in JSON or Homo sapiens).",
    )
    parser.add_argument("--expected-cell-type")
    parser.add_argument("--max-new-tokens", type=int, default=20)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("/mnt/output/c2s-scale-27b.json"),
        help="JSON result path; /mnt/output is persisted with an output bucket.",
    )
    return parser.parse_args()


def load_input(args: argparse.Namespace) -> dict[str, Any]:
    input_path = args.input or DEFAULT_INPUT
    payload: dict[str, Any] = {}
    if args.genes is None:
        payload = json.loads(input_path.read_text(encoding="utf-8"))
        genes = payload.get("genes")
        if not isinstance(genes, list) or not all(
            isinstance(gene, str) and gene.strip() for gene in genes
        ):
            raise ValueError(f"{input_path} must contain a non-empty string list named 'genes'")
    else:
        genes = args.genes.split()

    if len(genes) < MINIMUM_GENES:
        raise ValueError(
            f"C2S-Scale recommends at least {MINIMUM_GENES} ranked genes; got {len(genes)}"
        )

    return {
        "cell_id": payload.get("cell_id"),
        "organism": args.organism or payload.get("organism") or "Homo sapiens",
        "expected_cell_type": (
            args.expected_cell_type or payload.get("expected_cell_type")
        ),
        "genes": genes,
        "input_path": None if args.genes is not None else str(input_path),
        "provenance": payload.get("provenance"),
    }


def normalize_label(label: str | None) -> str | None:
    if label is None:
        return None
    return label.strip().rstrip(".").casefold()


def main() -> None:
    args = parse_args()
    started_at = time.monotonic()
    cell = load_input(args)

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    if not torch.cuda.is_available():
        raise RuntimeError(
            "C2S-Scale-Gemma-2-27B requires a CUDA GPU with at least 64 GiB VRAM"
        )

    device = torch.cuda.current_device()
    properties = torch.cuda.get_device_properties(device)
    if properties.total_memory < MINIMUM_VRAM_BYTES:
        available_gib = properties.total_memory / 1024**3
        raise RuntimeError(
            f"C2S-Scale-Gemma-2-27B requires at least 64 GiB VRAM; "
            f"found {available_gib:.1f} GiB"
        )

    torch.manual_seed(args.seed)
    torch.cuda.manual_seed_all(args.seed)

    model_load_started_at = time.monotonic()
    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_ID,
        revision=MODEL_REVISION,
    )
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        revision=MODEL_REVISION,
        dtype=torch.bfloat16,
        device_map="cuda",
        low_cpu_mem_usage=True,
    )
    model.eval()
    model_load_seconds = time.monotonic() - model_load_started_at

    cell_sentence = " ".join(cell["genes"])
    prompt = (
        f"The following is a list of {len(cell['genes'])} gene names ordered by "
        f"descending expression level in a {cell['organism']} cell. Your task is to "
        "give the cell type which this cell belongs to based on its gene expression.\n"
        f"Cell sentence: {cell_sentence}.\n"
        "The cell type corresponding to these genes is:"
    )
    tokenized = tokenizer(prompt, return_tensors="pt").to("cuda")

    generation_started_at = time.monotonic()
    with torch.inference_mode():
        outputs = model.generate(
            **tokenized,
            max_new_tokens=args.max_new_tokens,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
        )
    generation_seconds = time.monotonic() - generation_started_at

    generated_tokens = outputs[0, tokenized["input_ids"].shape[-1] :]
    predicted_cell_type = tokenizer.decode(
        generated_tokens,
        skip_special_tokens=True,
    ).strip()
    expected_cell_type = cell["expected_cell_type"]

    result = {
        "model": MODEL_ID,
        "model_revision": MODEL_REVISION,
        "source_revision": SOURCE_REVISION,
        "gpu": {
            "name": properties.name,
            "vram_gib": round(properties.total_memory / 1024**3, 1),
        },
        "input": {
            "cell_id": cell["cell_id"],
            "organism": cell["organism"],
            "gene_count": len(cell["genes"]),
            "expected_cell_type": expected_cell_type,
            "path": cell["input_path"],
            "provenance": cell["provenance"],
        },
        "prediction": predicted_cell_type,
        "matches_expected": (
            None
            if expected_cell_type is None
            else normalize_label(predicted_cell_type)
            == normalize_label(expected_cell_type)
        ),
        "generation": {
            "max_new_tokens": args.max_new_tokens,
            "seed": args.seed,
            "input_tokens": int(tokenized["input_ids"].shape[-1]),
            "output_tokens": int(generated_tokens.shape[-1]),
        },
        "timing_seconds": {
            "model_load": round(model_load_seconds, 3),
            "generation": round(generation_seconds, 3),
            "total": round(time.monotonic() - started_at, 3),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
