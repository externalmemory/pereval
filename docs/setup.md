# Setup

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

**The Zen example above is no longer reproducible as written.** As of 2026-11-01 the credential this project used against `https://opencode.ai/zen/v1` returns HTTP 401, so the worked example is kept for the record rather than as a working recipe: a reader following it with a current key should expect it to fail. Many of the free model endpoints the archived rows were measured on have also been retired, which is a separate problem recorded in [limitations.md](limitations.md#serving-provenance-is-not-controlled).

The surface that currently works for this project is the OpenCode Go subscription, which is a different endpoint from Zen and from the pay-as-you-go inference path, with its own model catalogue:

```
OPENCODE_GO_BASE_URL=https://opencode.ai/inference/go/openai/v1
OPENCODE_GO_API_KEY=<your key>
```

Models are then addressed as `openai-api/opencode-go/<model-id>`, for example `openai-api/opencode-go/gpt-6-luna`. Two request headers are mandatory for direct callers and Inspect does not send either by default, so pass them with `--model-config <file>`:

```yaml
default_headers:
  user-agent: "pereval/0.1 (+https://github.com/externalmemory/pereval)"
  x-opencode-session: "<any stable uuid per conversation>"
```

A generic SDK or HTTP-library `user-agent` is rejected. Note that `https://opencode.ai/inference/...` without the `go/` segment is a different billing surface entirely, the pay-as-you-go wallet and the anonymous free pool, and a Go subscription key sent there returns 402 or 429 rather than an authentication error, which makes a working key look broken. Remaining quota is readable from `GET https://opencode.ai/inference/go/v1/usage`, which returns integer percentages and reset timestamps for a rolling five-hour, weekly and monthly window.

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
