# Setup

## What Needs What

Docker is required only to run the agentic evaluation, which executes the model under test inside an isolated sandbox. The instance generator, the unit tests, and the scorer logic all run without Docker. So you can develop and test tasks and scorers with Python alone, and only need Docker when you actually evaluate a model end to end.

## Python Environment

The project uses [uv](https://docs.astral.sh/uv/). Install it, create a virtual environment, and install the project with its dev extras:

```
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv --python 3.12
uv sync
```

`uv sync` installs the exact pinned versions from `uv.lock`. Activate the environment with `source .venv/bin/activate`, or prefix commands with `.venv/bin/`.

Run the tests (no Docker needed):

```
.venv/bin/python -m pytest
```

## Docker (for Sandboxed Evaluation)

The ballistic task runs the agent in a Docker container with a general-purpose modeling toolkit and no network, so the agent cannot recognize the domain and re-simulate it. Inspect drives Docker through the Compose v2 plugin, so both `docker` and the `docker compose` plugin are required.

### Debian / Ubuntu

Verified on Ubuntu 24.04 (a plain KVM VM works fine; no dedicated host is needed):

```
sudo apt-get update
sudo apt-get install -y docker.io docker-compose-v2
sudo systemctl enable --now docker
```

Grant your user non-root access to the daemon, then start a new shell so the group membership takes effect (or run `newgrp docker`):

```
sudo usermod -aG docker "$USER"
```

Verify the daemon runs containers and that network isolation works:

```
docker run --rm hello-world
docker run --rm --network none python:3.12-slim python -c "print('sandbox OK')"
```

### Other Platforms

On macOS or Windows, install Docker Desktop, which bundles the Compose v2 plugin. On other Linux distributions, follow the official Docker Engine install for your distribution and ensure the `docker compose` plugin is present. In all cases the check is that `docker run --rm hello-world` and `docker compose version` both succeed.

## Model Access

Provide credentials for whatever provider you evaluate. This project has been exercised through the [OpenCode Zen](https://opencode.ai/docs/zen/) gateway, which is OpenAI-compatible. Put the credentials in a `.env` file in the repository root (it is gitignored, so keys never enter version control):

```
ZEN_BASE_URL=https://opencode.ai/zen/v1
ZEN_API_KEY=<your key>
```

Inspect loads `.env` automatically. Models are then addressed as `openai-api/zen/<model-id>`, for example `openai-api/zen/deepseek-v4-flash-free`. Any other Inspect-supported provider works too; set the corresponding provider environment variable instead.

## Running an Evaluation

Generate a single task instance to inspect it directly (no Docker):

```
python -m pereval.tasks.ballistic.generator --out-dir runs/demo --seed 1
```

Run the evaluation (needs Docker and model credentials):

```
inspect eval pereval/tasks/ballistic/task.py --model openai-api/zen/deepseek-v4-flash-free -T n_instances=1
```

A free model is enough for a first plumbing run: what you are checking is that the agent reads the data, builds a model, writes `predictions.csv`, and that the scorer picks it up. Calibrating difficulty against frontier models is a separate, paid step.
