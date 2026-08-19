# C2S-Scale-Gemma-2-27B on AnyCloud

Run a reproducible functional eval of C2S-Scale-Gemma-2-27B on cloud GPUs.

This AnyCloud-maintained artifact packages the public
[`cell2sentence`](https://github.com/vandijklab/cell2sentence) example and
[`C2S-Scale`](https://huggingface.co/vandijklab/C2S-Scale-Gemma-2-27B) model—not CellType's current [CT-1](https://www.celltype.com/) model.

## Run the eval

```bash
anycloud job ghcr.io/anycloud-sh/c2s-scale-27b:0.2.0-44c2ff7-r3 \
  --credentials lambda --region us-east-3 --vm-type gpu_1x_gh200 \
  --disk-size 150 --gpus all
```

The bundled [input fixture](examples/immune-tissue-natural-killer-cell.json) is a
human immune cell represented by 200 ranked genes (`ACTB` first, `EEF1B2` last).

```json
{
  "raw_prediction": "CD16-positive, CD56-dim natural killer cell, human.<ctrl100>",
  "prediction": "CD16-positive, CD56-dim natural killer cell, human",
  "matches_expected": true
}
```

`prediction` removes trailing control tokens and punctuation from
`raw_prediction`. [GH200 evidence](validation/lambda-gh200.json) records the exact digest, CUDA operation, input, output, and timings.

Every fresh job downloads approximately 54.5 GB of public weights. The validated
run took **TIMING_PENDING** end to end and **SCRIPT_TIMING_PENDING** in the runner.
It uses no checkpoint because it has no resumable state. JSON is printed to logs;
`/mnt/output/c2s-scale-27b.json` is durable only with an output bucket.

## Use another cell

Replace the complete fixture's metadata and 200-or-more ranked genes, then upload it:

```bash
export C2S_INPUT_BUCKET=my-unique-c2s-input
export C2S_OUTPUT_BUCKET=my-unique-c2s-output
export C2S_STORAGE_CREDENTIALS=my-aws
export C2S_STORAGE_REGION=us-east-1

anycloud bucket create "$C2S_INPUT_BUCKET" \
  --credentials "$C2S_STORAGE_CREDENTIALS" --region "$C2S_STORAGE_REGION"
anycloud bucket upload "$C2S_INPUT_BUCKET" \
  examples/immune-tissue-natural-killer-cell.json cells/cell.json \
  --credentials "$C2S_STORAGE_CREDENTIALS" --region "$C2S_STORAGE_REGION"

anycloud job ghcr.io/anycloud-sh/c2s-scale-27b:0.2.0-44c2ff7-r3 \
  --credentials lambda --region us-east-3 --vm-type gpu_1x_gh200 \
  --disk-size 150 --gpus all \
  --input-bucket "$C2S_INPUT_BUCKET" \
  --input-storage-credentials "$C2S_STORAGE_CREDENTIALS" \
  --input-storage-region "$C2S_STORAGE_REGION" \
  --output-bucket "$C2S_OUTPUT_BUCKET" \
  --output-storage-credentials "$C2S_STORAGE_CREDENTIALS" \
  --output-storage-region "$C2S_STORAGE_REGION" -- \
  --input /mnt/input/cells/cell.json
```

The output bucket is created automatically. Download with `anycloud bucket download "$C2S_OUTPUT_BUCKET" c2s-scale-27b.json ./result.json --credentials "$C2S_STORAGE_CREDENTIALS" --region "$C2S_STORAGE_REGION"`.

## Reproducibility and limits

Release `0.2.0-44c2ff7-r3` targets AMD64/ARM64, BF16, and at least 64 GiB VRAM.
H100 80 GB or GH200 96 GB is sufficient; B200 is unnecessary. Source is pinned
to `a6efaf0`, model `44c2ff7`, and the [Dockerfile](Dockerfile)'s exact inputs.

This one-cell deployment eval is not a quality benchmark, training pipeline, or
clinical validation. Code is Apache-2.0; downloaded weights are CC-BY-4.0. This
is not an official van Dijk Lab image.
