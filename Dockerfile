FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim@sha256:531f855bda2c73cd6ef67d56b733b357cea384185b3022bd09f05e002cd144ca

ARG IMAGE_REVISION=unknown

LABEL org.opencontainers.image.title="C2S-Scale-Gemma-2-27B portable inference job" \
      org.opencontainers.image.description="AnyCloud-maintained packaging of the van Dijk Lab C2S-Scale 27B cell-type prediction path" \
      org.opencontainers.image.source="https://github.com/anycloud-sh/c2s-scale-27b" \
      org.opencontainers.image.url="https://github.com/anycloud-sh/c2s-scale-27b" \
      org.opencontainers.image.licenses="Apache-2.0" \
      org.opencontainers.image.created="2026-08-19T00:00:00Z" \
      org.opencontainers.image.revision="${IMAGE_REVISION}" \
      org.opencontainers.image.version="0.2.0-44c2ff7-r2" \
      sh.anycloud.upstream.source="https://github.com/vandijklab/cell2sentence" \
      sh.anycloud.upstream.source-revision="a6efaf079f98491d4723ced44b929936b94368aa" \
      sh.anycloud.upstream.model="https://huggingface.co/vandijklab/C2S-Scale-Gemma-2-27B" \
      sh.anycloud.upstream.model-revision="44c2ff7dd5edc26daf9c3f4106e18e162a55676a"

RUN uv pip install --system --no-cache \
      --index https://download.pytorch.org/whl/cu128 \
      --index-strategy unsafe-best-match \
      "accelerate==1.14.0" \
      "protobuf==7.35.1" \
      "sentencepiece==0.2.1" \
      "torch==2.8.0" \
      "transformers==4.57.6"

RUN python -c 'import accelerate, google.protobuf, sentencepiece, torch, transformers; assert torch.version.cuda == "12.8"'
RUN uv pip check --system

ENV HF_HOME=/root/.cache/huggingface \
    HF_HUB_DISABLE_TELEMETRY=1 \
    HF_XET_HIGH_PERFORMANCE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /opt/c2s
COPY predict.py /opt/c2s/predict.py
COPY examples /opt/c2s/examples

ENTRYPOINT ["python", "/opt/c2s/predict.py"]
