# C2S-Scale-Gemma-2-27B on AnyCloud

This repository packages the van Dijk Lab's public C2S-Scale 27B cell-type
prediction path as a finite GPU job. Release `0.2.0-44c2ff7-r2` remains pending
until its candidate digest passes Lambda CUDA execution and real model
inference.

This is an AnyCloud-maintained container and is not an official van Dijk Lab
image. It implements the public model-card example with pinned model, source,
base-image, and Python dependency revisions.

The image targets `linux/amd64` and `linux/arm64` and a single BF16-capable
NVIDIA GPU with at least 64 GiB VRAM. An H100 80 GB or GH200 96 GB is an
intended target; B200 is not required.

The image does not contain or redistribute model weights. At runtime it
downloads approximately 54.5 GB of creator-owned public weights from Hugging
Face, predicts a cell type, prints the result and run metadata as JSON, and
writes the same result to `/mnt/output/c2s-scale-27b.json`.

The default input is a real human immune cell from the Cell2Sentence upstream
test fixture, represented as its 200 highest-expression genes. The checked-in
example records the upstream path, commit, fixture SHA-256, cell index, and tie
shuffle seed used to derive it.

## Use another cell sentence

Provide a JSON file with at least 200 ranked genes:

```json
{
  "cell_id": "my-cell",
  "organism": "Homo sapiens",
  "genes": ["MALAT1", "ACTB", "B2M"]
}
```

After the validated release is promoted, override the container arguments
after `--` and mount or bake the file into an image derived from it:

```bash
anycloud job ghcr.io/anycloud-sh/c2s-scale-27b:0.2.0-44c2ff7-r2 \
  --credentials lambda --gpu-type h100 --gpus all --disk-size 150 -- \
  --input /path/to/cell.json
```

For a short command-line test, `--genes` accepts a space-separated ranked gene
list; the same 200-gene minimum is enforced.

## Build, validate, and promote

The repository's `Build candidate` workflow assembles AMD64 and ARM64 images on
native hosted Linux CPU runners, combines them under one manifest, and publishes
only `candidate-<source-commit>`. The exact registry digest is then run on a
Lambda GPU through AnyCloud. The inference wrapper first executes and
synchronizes a BF16 CUDA matrix multiplication, then runs the official
model-card prediction path. Only a digest with committed Lambda evidence can
pass the separate `Promote validated image` workflow, which adds the release tag
without rebuilding.

The local Mac is an authoring environment only. It is not used to build images,
install or test CUDA, download weights, or reproduce the model.

## Pinned upstream inputs

- Cell2Sentence source:
  [`a6efaf0`](https://github.com/vandijklab/cell2sentence/tree/a6efaf079f98491d4723ced44b929936b94368aa)
- C2S-Scale-Gemma-2-27B model:
  [`44c2ff7`](https://huggingface.co/vandijklab/C2S-Scale-Gemma-2-27B/tree/44c2ff7dd5edc26daf9c3f4106e18e162a55676a)
- Base image: `ghcr.io/astral-sh/uv:python3.13-bookworm-slim` at
  `sha256:531f855bda2c73cd6ef67d56b733b357cea384185b3022bd09f05e002cd144ca`
- Runtime: `torch==2.9.1`, `transformers==4.57.6`,
  `accelerate==1.14.0`, `sentencepiece==0.2.1`
- Minimum GPU memory enforced by the wrapper: 64 GiB

The wrapper code is Apache-2.0 licensed. The upstream Cell2Sentence code is
Apache-2.0 licensed, while the model weights are CC-BY-4.0. Review the
[model card](https://huggingface.co/vandijklab/C2S-Scale-Gemma-2-27B) for
intended use and limitations.
