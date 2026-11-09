FROM python:3.12.14-slim-bookworm@sha256:eb5be8e5b4d0a159c237946bbdd06356dda5d19c30fc4f7843e8046d3a590333
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONHASHSEED=0 \
    OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
    BLIS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
    OMP_DYNAMIC=FALSE MPLCONFIGDIR=/opt/benchmark/results/.matplotlib
WORKDIR /opt/benchmark
COPY requirements.lock ./
RUN python -m pip install --no-cache-dir --only-binary=:all: --require-hashes -r requirements.lock \
    && python -m pip check
COPY . .
# Fail the build if the real pinned IPOPT plugin cannot solve on ARM64.
RUN python benchmark.py --self-check --output results/image-build-check
ENTRYPOINT ["python", "benchmark.py"]
