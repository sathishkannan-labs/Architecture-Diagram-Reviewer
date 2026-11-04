# syntax=docker/dockerfile:1
FROM python:3.12-slim-bookworm
ARG TF_VERSION=1.9.8
ARG TARGETARCH=amd64
RUN apt-get update && apt-get install -y --no-install-recommends curl unzip ca-certificates libseccomp2 && rm -rf /var/lib/apt/lists/*
# HTTPS checksums verified before installing the pinned binary.
RUN test "$TF_VERSION" = 1.9.8 && test "$TARGETARCH" = amd64 && \
    curl -fsSLo /tmp/terraform.zip https://releases.hashicorp.com/terraform/${TF_VERSION}/terraform_${TF_VERSION}_linux_${TARGETARCH}.zip && \
    curl -fsSLo /tmp/SHA256SUMS https://releases.hashicorp.com/terraform/${TF_VERSION}/terraform_${TF_VERSION}_SHA256SUMS && \
    cd /tmp && sed -n "s@  terraform_${TF_VERSION}_linux_${TARGETARCH}.zip@  terraform.zip@p" SHA256SUMS | sha256sum -c - && \
    unzip -j terraform.zip terraform -d /usr/local/bin && rm terraform.zip SHA256SUMS
WORKDIR /app
COPY pyproject.toml ./
COPY archreview ./archreview
RUN pip install --no-cache-dir .
COPY scripts ./scripts
RUN python scripts/build_mirror.py
ENV TERRAFORM_MIRROR=/opt/terraform-mirror TERRAFORM_LOCK_FILE=/opt/terraform-lock/.terraform.lock.hcl
RUN useradd --uid 10001 --create-home app
COPY streamlit_app.py ./
COPY examples ./examples
USER 10001:10001
# Same non-root, seccomp-filtered, credential-free runtime validator; fails build if mirror is unusable.
RUN python scripts/offline_smoke.py
EXPOSE 8501
CMD ["streamlit", "run", "streamlit_app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.maxUploadSize=5", "--server.fileWatcherType=none", "--browser.gatherUsageStats=false"]
