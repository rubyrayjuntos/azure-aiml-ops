FROM python:3.11.11-slim
WORKDIR /workspace
COPY constraints.txt pyproject.toml ./
RUN python -m pip install --no-cache-dir -c constraints.txt .
COPY . .
ENTRYPOINT ["python", "scripts/run_local_lifecycle.py"]
