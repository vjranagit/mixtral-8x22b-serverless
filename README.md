# Mixtral-8x22B Serverless Inference API

Production-ready deployment of **Mixtral-8x22B-Instruct** on RunPod Serverless with vLLM, featuring automated CI/CD, cost optimization, and OpenAI-compatible API.

[![Build and Push](https://github.com/vjranagit/mixtral-8x22b-serverless/actions/workflows/build-push.yml/badge.svg)](https://github.com/vjranagit/mixtral-8x22b-serverless/actions/workflows/build-push.yml)
[![Deploy to Dev](https://github.com/vjranagit/mixtral-8x22b-serverless/actions/workflows/dev-deploy.yml/badge.svg)](https://github.com/vjranagit/mixtral-8x22b-serverless/actions/workflows/dev-deploy.yml)

**Docker Hub**: [vjrana/mixtral-8x22b-serverless](https://hub.docker.com/r/vjrana/mixtral-8x22b-serverless) | **Tags**: `prod`, `dev`

---

## 🚀 Features

- **High Performance**: 450+ tokens/second throughput on 4x H100 GPUs
- **Cost Effective**: Scale-to-zero when idle, pay only for active compute
- **OpenAI Compatible**: Drop-in replacement for OpenAI API
- **Production Ready**: Full CI/CD with dev/prod environments
- **Optimized**: FP8 quantization for 2x faster inference on H100
- **Monitored**: Built-in cost tracking and performance benchmarking

---

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Deployment](#deployment)
- [API Usage](#api-usage)
- [Cost Analysis](#cost-analysis)
- [Performance](#performance)
- [Development](#development)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

---

## ⚡ Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/vjranagit/mixtral-8x22b-serverless.git
cd mixtral-8x22b-serverless

# Copy environment template
cp .env.example .env

# Edit .env with your credentials
nano .env
```

### 2. Create Network Volume

```bash
# Creates a 200GB volume for model caching
./scripts/setup-volume.sh
```

### 3. Deploy

```bash
# Development
git checkout dev
git push origin dev

# Production
git checkout main
git push origin main
```

Deployments are automated via GitHub Actions!

---

## 📦 Requirements

### Infrastructure
- **RunPod Account** with payment method
- **4x H100 80GB GPUs** (required for Mixtral-8x22B)
- **200GB Network Volume** for model storage
- **GitHub Account** with GHCR access

### Software
- Docker 20.10+
- Python 3.10+
- Git
- Bash shell

### API Keys
- **RunPod API Key** (dev and prod)
- **HuggingFace Token** (for model downloads)
- **GitHub Personal Access Token** (for GHCR)
- **OpenRouter API Key** (optional, for monetization)

---

## 🔧 Installation

### Local Development Setup

```bash
# Clone repository
git clone https://github.com/vjranagit/mixtral-8x22b-serverless.git
cd mixtral-8x22b-serverless

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install httpx pytest black ruff mypy

# Set up local environment file (IMPORTANT!)
cp configs/local.env.example configs/local.env
# Edit configs/local.env and add your GitHub PAT and other secrets
```

### Local Environment Setup (Required)

**IMPORTANT**: Before running any deployment scripts, set up your local environment file:

```bash
# 1. Copy the example file
cp configs/local.env.example configs/local.env

# 2. Edit configs/local.env and add your secrets:
#    - GITHUB_PERSONAL_ACCESS_TOKEN (fine-grained PAT)
#    - DOCKERHUB_TOKEN (same as above)
#    - GITHUB_USERNAME (vjranagit)
#    - Other optional secrets (RunPod API keys, HF token, etc.)

# 3. Verify it's gitignored (should not show in git status)
git status configs/local.env  # Should say: "not tracked"
```

**See [GITHUB_SETUP.md](GITHUB_SETUP.md#-local-github-pat-setup-repo-scoped) for detailed instructions on creating a GitHub PAT.**

### GitHub Secrets Configuration (for CI/CD)

Configure these secrets in your GitHub repository (Settings → Secrets):

**Development:**
```
RUNPOD_API_KEY_DEV         # RunPod API key for dev
RUNPOD_ENDPOINT_ID_DEV     # Endpoint ID (after first deployment)
RUNPOD_ENDPOINT_URL_DEV    # Endpoint URL (optional, for testing)
```

**Production:**
```
RUNPOD_API_KEY_PROD        # RunPod API key for prod
RUNPOD_ENDPOINT_ID_PROD    # Endpoint ID (after first deployment)
RUNPOD_ENDPOINT_URL_PROD   # Endpoint URL (optional, for testing)
OPENROUTER_API_KEY         # OpenRouter key (optional)
```

**Shared:**
```
HF_TOKEN                   # HuggingFace token
```

---

## ⚙️ Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Model Configuration
MODEL_NAME=mistralai/Mixtral-8x22B-Instruct-v0.1
HF_TOKEN=your_huggingface_token

# GPU Settings (4x H100 80GB)
TENSOR_PARALLEL_SIZE=4
GPU_MEMORY_UTILIZATION=0.92
MAX_NUM_SEQS=8
MAX_MODEL_LEN=32768

# vLLM Optimization
QUANTIZATION=fp8
TRUST_REMOTE_CODE=true

# RunPod
RUNPOD_API_KEY_DEV=your_dev_key
RUNPOD_API_KEY_PROD=your_prod_key
```

### Environment-Specific Configs

**Development** (`configs/dev/`):
- Lower GPU memory usage (90%)
- Shorter context (16K tokens)
- Verbose logging
- Max 2 workers

**Production** (`configs/prod/`):
- Maximum GPU usage (92%)
- Full context (32K tokens)
- Minimal logging
- Max 5 workers

---

## 🚀 Deployment

### Automated Deployment (Recommended)

**Development:**
```bash
git checkout dev
git add .
git commit -m "feat: your changes"
git push origin dev
```

**Production:**
```bash
# Create PR from dev to main
gh pr create --base main --head dev --title "Release vX.Y.Z"

# After approval, merge triggers auto-deployment
```

### Manual Deployment

```bash
# Deploy to development
./scripts/deploy.sh dev

# Deploy to production
./scripts/deploy.sh prod
```

### Initial Setup (First Time Only)

1. **Create Network Volume:**
```bash
./scripts/setup-volume.sh
```

2. **Update RunPod Config:**
Edit `configs/dev/runpod.json` and `configs/prod/runpod.json` with the volume ID.

3. **Build and Push Image:**
```bash
# Login to GHCR
echo $DOCKERHUB_TOKEN | docker login docker.io -u vjranagit --password-stdin

# Build
docker build -f docker/Dockerfile -t vjrana/mixtral-8x22b-serverless:latest .

# Push
docker push vjrana/mixtral-8x22b-serverless:latest
```

4. **Create Endpoint in RunPod:**
- Go to RunPod dashboard
- Create serverless endpoint
- Select 4x H100 80GB
- Attach network volume
- Use your GHCR image
- Save endpoint ID to GitHub Secrets

---

## 🔌 API Usage

### OpenAI Python Client

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/openai/v1",
    api_key="YOUR_API_KEY"
)

response = client.chat.completions.create(
    model="mistralai/Mixtral-8x22B-Instruct-v0.1",
    messages=[
        {"role": "user", "content": "Explain quantum computing"}
    ],
    max_tokens=500,
    temperature=0.7
)

print(response.choices[0].message.content)
```

### Direct HTTP

```bash
curl -X POST https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/run \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "messages": [
        {"role": "user", "content": "Hello!"}
      ],
      "max_tokens": 100,
      "temperature": 0.7
    }
  }'
```

### Streaming Responses

```python
stream = client.chat.completions.create(
    model="mistralai/Mixtral-8x22B-Instruct-v0.1",
    messages=[{"role": "user", "content": "Write a story"}],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

---

## 💰 Cost Analysis

### GPU Costs

**4x H100 80GB:**
- **Hourly**: $2.40/hour when active
- **Idle**: $0/hour (scale-to-zero)
- **Per Second**: $0.000667/second

**Network Volume:**
- **Storage**: $40/month (200GB @ $0.20/GB/month)

### Usage Scenarios

Run cost analysis:
```bash
# Daily costs
python scripts/cost-calculator.py --days 1

# Monthly projection
python scripts/cost-calculator.py --days 30

# Budget check
python scripts/cost-calculator.py --days 30 --budget 500

# Detailed breakdown
