# Mixtral-8x22B Serverless Inference API - Project Outline

## 📌 Project Overview

**Name**: Mixtral-8x22B Serverless Inference API
**Version**: 1.0.0
**Status**: ✅ Deployed to GitHub
**Started**: 2025-11-13
**Repository**: https://github.com/vjranagit/mixtral-8x22b-serverless
**Visibility**: Private

### Mission
Deploy a production-ready, cost-effective Mixtral-8x22B-Instruct inference API on RunPod Serverless with automated CI/CD, OpenAI compatibility, and optional OpenRouter integration for monetization.

### Key Objectives
1. ✅ Deploy Mixtral-8x22B on RunPod Serverless with 4x H100 GPUs
2. ✅ Achieve 450+ tokens/second throughput
3. ✅ Maintain <$0.50 cost per million input tokens
4. ✅ Provide OpenAI-compatible REST API
5. ✅ Implement automated CI/CD for dev/prod environments
6. ✅ Enable scale-to-zero for cost optimization
7. ✅ Optional: Register as OpenRouter provider for revenue

---

## 🏗️ Architecture

### Technology Stack

**Infrastructure**:
- Platform: RunPod Serverless
- GPUs: 4x NVIDIA H100 80GB
- Storage: 200GB Network Volume
- Deployment: Docker containers via Docker Hub

**Inference Engine**:
- Engine: vLLM v0.6.6+
- Quantization: FP8 (H100 optimized)
- Tensor Parallelism: 4 (across 4 GPUs)
- GPU Memory Utilization: 92%
- Max Concurrent Sequences: 8

**API Layer**:
- Framework: RunPod worker-vllm template
- Protocol: OpenAI-compatible REST API
- Endpoints: `/v1/chat/completions`, `/v1/completions`
- Authentication: API key via headers

**CI/CD**:
- Platform: GitHub Actions ✅ Live
- Container Registry: Docker Hub (docker.io/vjrana/mixtral-8x22b-serverless)
- Branches: `dev` (staging), `main` (production)
- Automation: Auto-deploy on push
- Workflows: [Live on GitHub](https://github.com/vjranagit/mixtral-8x22b-serverless/tree/main/.github/workflows)

### Model Configuration

**Model**: mistralai/Mixtral-8x22B-Instruct-v0.1
- Parameters: 141B total (8 experts × 22B each, 2 active per token)
- Context Window: 32,768 tokens
- Architecture: Mixture of Experts (MoE)
- Tokenizer: Mistral
- License: Apache 2.0

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Developer Workflow                       │
│  ┌─────────┐           ┌──────────┐         ┌─────────┐     │
│  │   Dev   │──push───▶ │   Dev    │──test──▶│  Main   │     │
│  │ Branch  │           │  Branch  │         │ Branch  │     │
│  └─────────┘           └──────────┘         └─────────┘     │
│       │                      │                     │         │
└───────┼──────────────────────┼─────────────────────┼─────────┘
        │                      │                     │
        ▼                      ▼                     ▼
   ┌─────────────────────────────────────────────────────┐
   │           GitHub Actions (CI/CD)                     │
   │  ┌───────────┐  ┌──────────┐  ┌──────────────────┐ │
   │  │   Build   │─▶│   Test   │─▶│ Push to Docker   │ │
   │  │  Docker   │  │  & Lint  │  │   Hub Registry   │ │
   │  └───────────┘  └──────────┘  └──────────────────┘ │
   └──────────────────────┬──────────────────────────────┘
                          │
                          ▼
   ┌────────────────────────────────────────────────────────┐
   │              RunPod Serverless                         │
   │  ┌───────────────────────┐  ┌──────────────────────┐  │
   │  │    Dev Endpoint       │  │   Prod Endpoint      │  │
   │  │  ┌────────────────┐   │  │  ┌────────────────┐  │  │
   │  │  │ 4x H100 80GB   │   │  │  │ 4x H100 80GB   │  │  │
   │  │  │ ┌───────────┐  │   │  │  │ ┌───────────┐  │  │  │
   │  │  │ │vLLM Engine│  │   │  │  │ │vLLM Engine│  │  │  │
   │  │  │ │ (FP8,TP=4)│  │   │  │  │ │ (FP8,TP=4)│  │  │  │
   │  │  │ └───────────┘  │   │  │  │ └───────────┘  │  │  │
   │  │  │ ┌───────────┐  │   │  │  │ ┌───────────┐  │  │  │
   │  │  │ │ FastAPI   │  │   │  │  │ │ FastAPI   │  │  │  │
   │  │  │ │  Server   │  │   │  │  │ │  Server   │  │  │  │
   │  │  │ └───────────┘  │   │  │  │ └───────────┘  │  │  │
   │  │  └────────────────┘   │  │  └────────────────┘  │  │
   │  │  Network Volume        │  │  Network Volume      │  │
   │  │  (Model Cache)         │  │  (Model Cache)       │  │
   │  └───────────────────────┘  └──────────────────────┘  │
   └────────────────────┬─────────────────────┬─────────────┘
                        │                     │
                        ▼                     ▼
   ┌──────────────────────────────────────────────────────┐
   │                    Clients                           │
   │  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │
   │  │ OpenAI   │  │  Direct  │  │   OpenRouter     │   │
   │  │ Client   │  │  HTTP    │  │   (Prod Only)    │   │
   │  └──────────┘  └──────────┘  └──────────────────┘   │
   └──────────────────────────────────────────────────────┘
```

---

## 📂 Repository Structure

```
mixtral-8x22b-serverless/
├── project-outline.md          # This file - project overview
├── rulebook.md                 # Development guidelines
├── todo.md                     # Task tracking
├── README.md                   # User-facing documentation
├── .env.example                # Environment variables template
├── .gitignore                  # Git ignore rules
│
├── src/                        # Source code (from worker-vllm)
│   ├── handler.py              # RunPod serverless handler
│   ├── config.py               # vLLM configuration
│   └── utils/                  # Utility functions
│
├── docker/                     # Docker configuration
│   ├── Dockerfile              # Container definition
