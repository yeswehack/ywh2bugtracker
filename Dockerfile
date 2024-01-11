FROM python:3.12.1-slim-bookworm AS builder
RUN apt-get update && apt-get install -yq curl
RUN curl -sSL https://install.python-poetry.org | python -
WORKDIR /ywh2bt
COPY / ./
RUN /root/.local/bin/poetry build

FROM python:3.12.1-slim-bookworm
RUN apt-get update && \
    apt-get install -y \
    gcc \
    libffi-dev \
    musl-dev \
    libssl-dev && \
    rm -rf /var/lib/apt/lists/*
ARG user=ywh2bt-user
ARG group=ywh2bt
ARG uid=1000
ARG gid=1000
RUN groupadd -g ${gid} ${group}
RUN useradd -u ${uid} -g ${group} -s /bin/sh -m ${user}
WORKDIR /ywh2bt
COPY --from=builder /ywh2bt/dist/*.whl /ywh2bt/
RUN pip install --no-cache-dir *.whl
USER ${uid}:${gid}
ENTRYPOINT ["ywh2bt"]
