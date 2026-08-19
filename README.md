# C2S-Scale-Gemma-2-27B on AnyCloud

Run the van Dijk Lab's public C2S-Scale 27B cell-type prediction path as a
finite, portable GPU job:

```bash
anycloud job ghcr.io/anycloud-sh/c2s-scale-27b:0.1.0-44c2ff7-r1 \
  --credentials lambda --gpu-type h100 --gpus all --disk-size 150
```

This is an AnyCloud-maintained container and is not an official van Dijk Lab
image. It implements the public model-card example with pinned model, source,
base-image, and Python dependency revisions.

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

Then override the container arguments after `--` and mount or bake the file
into an image derived from this one:

```bash
anycloud job ghcr.io/anycloud-sh/c2s-scale-27b:0.1.0-44c2ff7-r1 \
  --credentials lambda --gpu-type h100 --gpus all --disk-size 150 -- \
  --input /path/to/cell.json
```

For a short command-line test, `--genes` accepts a space-separated ranked gene
list; the same 200-gene minimum is enforced.

## Reproduce the image

```bash
docker buildx build \
  --platform linux/amd64 \
  --build-arg IMAGE_REVISION="$(git rev-parse HEAD)" \
  --provenance=false \
  -t ghcr.io/anycloud-sh/c2s-scale-27b:0.1.0-44c2ff7-r1 \
  .
```

## Pinned upstream inputs

- Cell2Sentence source:
  [`a6efaf0`](https://github.com/vandijklab/cell2sentence/tree/a6efaf079f98491d4723ced44b929936b94368aa)
- C2S-Scale-Gemma-2-27B model:
  [`44c2ff7`](https://huggingface.co/vandijklab/C2S-Scale-Gemma-2-27B/tree/44c2ff7dd5edc26daf9c3f4106e18e162a55676a)
- Base image: `ghcr.io/astral-sh/uv:python3.13-bookworm-slim` at
  `sha256:531f855bda2c73cd6ef67d56b733b357cea384185b3022bd09f05e002cd144ca`
- Runtime: `torch==2.8.0`, `transformers==4.57.6`,
  `accelerate==1.14.0`, `sentencepiece==0.2.1`
- Minimum GPU memory enforced by the wrapper: 64 GiB

The wrapper code is Apache-2.0 licensed. The upstream Cell2Sentence code is
Apache-2.0 licensed, while the model weights are CC-BY-4.0. Review the
[model card](https://huggingface.co/vandijklab/C2S-Scale-Gemma-2-27B) for
intended use and limitations.
