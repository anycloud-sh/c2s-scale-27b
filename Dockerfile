FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim@sha256:531f855bda2c73cd6ef67d56b733b357cea384185b3022bd09f05e002cd144ca

ARG IMAGE_REVISION=unknown
ARG TARGETARCH

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

RUN case "${TARGETARCH}" in \
      amd64) CUSPARSELT_WHEEL="https://pypi.nvidia.com/nvidia-cusparselt-cu12/nvidia_cusparselt_cu12-0.7.1-py3-none-manylinux2014_x86_64.whl#sha256=f1bb701d6b930d5a7cea44c19ceb973311500847f81b634d802b7b539dc55623" ;; \
      arm64) CUSPARSELT_WHEEL="https://pypi.nvidia.com/nvidia-cusparselt-cu12/nvidia_cusparselt_cu12-0.7.1-py3-none-manylinux2014_aarch64.whl#sha256=8878dce784d0fac90131b6817b607e803c36e629ba34dc5b433471382196b6a5" ;; \
      *) echo "Unsupported target architecture: ${TARGETARCH}" >&2; exit 1 ;; \
    esac && \
    uv pip install --system --no-cache \
      --index https://download.pytorch.org/whl/cu128 \
      --index-strategy unsafe-best-match \
      "${CUSPARSELT_WHEEL}" \
      "accelerate==1.14.0" \
      "protobuf==7.35.1" \
      "sentencepiece==0.2.1" \
      "torch==2.9.1" \
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
