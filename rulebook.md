# Mixtral-8x22B Serverless API - Development Rulebook

## 📜 Purpose

This rulebook defines the standards, practices, and guidelines for developing and maintaining the Mixtral-8x22B serverless inference API. All contributors must follow these rules to ensure code quality, security, and operational excellence.

---

## 🏛️ Core Principles

### 1. Simplicity First
- Use pre-built templates when available (RunPod worker-vllm)
- Avoid over-engineering solutions
- Prefer configuration over custom code
- Keep the codebase minimal and maintainable

### 2. Cost Consciousness
- Always consider GPU cost implications
- Implement scale-to-zero properly
- Monitor and optimize resource usage
- Document cost impact of changes

### 3. Production Ready
- All code must be production-grade
- No shortcuts or temporary hacks
- Proper error handling required
- Security considerations mandatory

### 4. Documentation Driven
- Update docs before/during code changes
- Keep project-outline.md, rulebook.md, todo.md in sync
- Document all configuration options
- Provide clear examples

---

## 🔧 Development Guidelines

### Code Standards

#### Python Code Style
```python
# Use Black formatter (line length 100)
# Follow PEP 8
# Type hints required for functions

def generate_completion(
    prompt: str,
    max_tokens: int = 512,
    temperature: float = 0.7
) -> dict:
    """
    Generate completion from prompt.

    Args:
        prompt: Input text prompt
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature (0.0-2.0)

    Returns:
        Dictionary with completion results
    """
    pass
```

#### Configuration Files
- Use YAML for complex configs
- Use JSON for RunPod API configs
- Use .env for environment variables
- Never commit secrets

#### File Naming
- Python files: `snake_case.py`
- Config files: `kebab-case.yaml`
- Scripts: `kebab-case.sh`
- Docs: `UPPERCASE.md` or `kebab-case.md`

### Git Workflow

#### Branch Strategy
```
main (prod)
  ↑
  └── PR with review required
       ↑
      dev (staging)
       ↑
       └── feature branches
```

#### Branch Naming
- Feature: `feature/short-description`
- Bugfix: `fix/issue-description`
- Hotfix: `hotfix/critical-issue`

#### Commit Messages
```
Format: <type>: <description>

Types:
- feat: New feature
- fix: Bug fix
- docs: Documentation changes
- config: Configuration changes
- ci: CI/CD changes
- perf: Performance improvements
- refactor: Code refactoring

Examples:
✅ feat: add streaming support for completions
✅ fix: correct GPU memory calculation
✅ docs: update deployment guide with network volume setup
✅ config: increase max_num_seqs to 8 for better throughput

❌ updated stuff
❌ changes
❌ WIP
```

#### Pull Request Rules
1. **All PRs must**:
   - Have descriptive title and description
   - Pass all CI checks
   - Update relevant documentation
   - Include test updates if needed

2. **Production PRs** (dev → main):
   - Require 1 approval (can be self-approved for solo projects)
   - All tests must pass
   - Must include deployment checklist
   - Must update version numbers

---

## 🐳 Docker Best Practices

### Dockerfile Rules
1. Use official NVIDIA CUDA base images
2. Pin specific versions (no `latest` tags)
3. Multi-stage builds when beneficial
4. Minimize layer count
5. Clean up in same RUN command
6. Use .dockerignore properly

### Image Naming Convention
```
docker.io/vjrana/mixtral-8x22b-serverless:<tag>

Tags:
- dev                    # Latest dev build
- dev-<git-sha>         # Specific dev commit
- latest                # Latest prod build
- prod-<git-sha>        # Specific prod commit
- v1.0.0               # Semantic version releases
```

### Container Security
- Run as non-root user when possible
- No secrets in image layers
- Scan for vulnerabilities
- Keep base images updated

---

## ⚙️ Configuration Management

### Environment Variables

#### Naming Convention
```bash
# Category prefixes
MODEL_*          # Model configuration
VLLM_*          # vLLM engine settings
RUNPOD_*        # RunPod platform settings
API_*           # API server settings

# Examples
MODEL_NAME=mistralai/Mixtral-8x22B-Instruct-v0.1
VLLM_TENSOR_PARALLEL_SIZE=4
RUNPOD_ENDPOINT_ID=abc123
API_KEY=secret-key-here
```

#### Required Variables (All Environments)
```bash
MODEL_NAME                    # Model to load
HF_TOKEN                      # HuggingFace token
VLLM_TENSOR_PARALLEL_SIZE    # Number of GPUs
VLLM_GPU_MEMORY_UTILIZATION  # GPU memory % (0.0-1.0)
VLLM_MAX_NUM_SEQS           # Max concurrent requests
```

#### Environment-Specific Variables
```bash
# Development
ENV=dev
LOG_LEVEL=DEBUG
VLLM_MAX_MODEL_LEN=16384     # Shorter for faster testing

# Production
ENV=prod
LOG_LEVEL=INFO
VLLM_MAX_MODEL_LEN=32768     # Full context window
OPENROUTER_API_KEY=...       # Only in prod
```

### Configuration File Hierarchy
1. Defaults in code
2. Config files (configs/dev/*.yaml)
3. Environment variables (override configs)
4. Runtime parameters (override everything)

---

## 🧪 Testing Requirements

### Test Coverage Rules
- All API endpoints must have tests
- Critical paths require integration tests
- Performance tests for throughput/latency
- OpenAI compatibility tests required

### Test Naming Convention
```python
# Unit tests
def test_<function_name>_<scenario>():
    """Test that <function> does <expected behavior> when <scenario>"""
    pass

# Examples
def test_format_prompt_handles_empty_messages():
def test_generate_completion_respects_max_tokens():
def test_api_returns_400_on_invalid_temperature():
```

### Test Organization
```
tests/
├── unit/              # Fast, isolated tests
│   ├── test_config.py
│   └── test_utils.py
├── integration/       # API endpoint tests
│   ├── test_completions.py
│   └── test_openai_compat.py
└── performance/       # Benchmarks
    └── test_throughput.py
```

### Running Tests
```bash
# Run all tests
pytest tests/ -v

# Run specific category
pytest tests/unit/ -v
pytest tests/integration/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Performance tests (manual, not in CI)
pytest tests/performance/ -v --runpod-endpoint=$ENDPOINT_URL
```

---

## 🚀 Deployment Rules

### Pre-Deployment Checklist

#### Development Deployments
- [ ] All tests passing locally
- [ ] Configuration reviewed
- [ ] Cost impact estimated
- [ ] Rollback plan identified

#### Production Deployments
- [ ] All dev tests passing
- [ ] Code reviewed and approved
- [ ] Documentation updated
- [ ] Version number bumped
- [ ] Changelog updated
- [ ] Cost impact approved
- [ ] Monitoring configured
- [ ] Rollback tested in dev

### Deployment Safety Rules

1. **Never deploy directly to prod**
   - Always go through dev first
   - Test in dev for at least 24 hours
   - Verify performance metrics

2. **Always use CI/CD pipelines**
   - No manual deployments (except emergencies)
   - Let GitHub Actions handle deployment
   - Review deployment logs

3. **Monitor after deployment**
   - Watch for errors in first 15 minutes
   - Check performance metrics
   - Verify scale-to-zero works
   - Monitor costs

4. **Have rollback ready**
   - Keep previous image tagged
   - Document rollback procedure
   - Test rollback in dev environment

### Emergency Procedures

#### If Production is Down
1. Check RunPod dashboard for errors
2. Review recent deployments
3. Roll back to last known good image
4. Notify stakeholders
5. Debug in dev environment
6. Document incident

#### If Costs Spike Unexpectedly
1. Check RunPod workers running count
2. Verify scale-to-zero is working
3. Review recent configuration changes
4. Temporarily reduce workers_max
5. Investigate root cause
6. Implement fix and redeploy

---

## 💰 Cost Management Rules

### Cost Control Measures

1. **Always use scale-to-zero**
   ```json
   {
     "workers_min": 0,
     "idle_timeout": 60
   }
   ```

2. **Set maximum worker limits**
   ```json
   {
     "workers_max": 5  // Prevents runaway costs
   }
   ```

3. **Monitor daily costs**
   - Run cost-calculator.py daily
   - Set up alerts for >$20/day
   - Review monthly spending trends

4. **Optimize for cost efficiency**
   - Use FP8 quantization
   - Tune gpu_memory_utilization
   - Adjust max_num_seqs based on traffic
   - Use network volumes for model caching

### Cost Tracking

```bash
# Daily cost check (add to cron)
python scripts/cost-calculator.py --days 1

# Weekly cost report
python scripts/cost-calculator.py --days 7 --detailed

# Monthly budget check
python scripts/cost-calculator.py --days 30 --budget 500
```

---

## 🔐 Security Requirements

### Secrets Management

#### Secrets Storage Policy

**Two-Tier Secrets System:**
1. **Local Development**: `configs/local.env` (repo-scoped, gitignored)
2. **CI/CD**: GitHub Actions Secrets (repository settings)

**NEVER** store secrets in:
- ❌ `~/.bashrc` or other user-level shell configs
- ❌ Committed files (any file tracked by git)
- ❌ System-wide environment variables
- ❌ Docker images

#### Local Development Secrets (configs/local.env)

```bash
# ✅ CORRECT: Store in configs/local.env (gitignored)
GITHUB_PERSONAL_ACCESS_TOKEN=github_pat_YOUR_TOKEN
DOCKERHUB_TOKEN=github_pat_YOUR_TOKEN
GITHUB_USERNAME=vjranagit
RUNPOD_API_KEY_DEV=your_dev_key
HF_TOKEN=hf_your_token

# ❌ NEVER DO THIS: ~/.bashrc or committed files
# DO NOT put secrets in ~/.bashrc
# DO NOT commit configs/local.env to git
```

**How to Use**:
1. Copy template: `cp configs/local.env.example configs/local.env`
2. Fill in your actual values
3. Scripts automatically load it: `./scripts/deploy.sh dev`

**Why Repo-Scoped?**
- ✅ Project-specific (doesn't pollute global environment)
- ✅ Automatically gitignored
- ✅ Easy to manage per project
- ✅ No system-wide config changes

#### CI/CD Secrets (GitHub Actions)

- Configure in: Repository Settings → Secrets and variables → Actions
- Use for: Automated deployments, builds, tests
- Naming convention:
  ```
  RUNPOD_API_KEY_DEV
  RUNPOD_API_KEY_PROD
  OPENROUTER_API_KEY
  HF_TOKEN
  ```

#### Never Commit Secrets
```bash
# ❌ NEVER DO THIS
API_KEY=sk-1234567890abcdef

# ✅ DO THIS
API_KEY=${RUNPOD_API_KEY}  # From configs/local.env or GitHub Secrets
```

#### Secret Rotation
- Rotate personal access tokens every 90 days
- Rotate API keys quarterly
- Update both `configs/local.env` AND GitHub Secrets
- Test after rotation

### API Security

1. **Authentication required**
   - All endpoints require API key
   - Validate on every request
   - Use Bearer token format

2. **Rate limiting**
   - Implement per-key limits
   - Default: 100 requests/minute
   - Configurable per environment

3. **Input validation**
   - Validate all parameters
   - Reject invalid requests early
   - Sanitize inputs
   - Enforce token limits

4. **Logging security**
   - Never log API keys
   - Redact sensitive data
   - Log authentication attempts
   - Monitor for abuse

---

## 📊 Monitoring & Logging

### Logging Standards

#### Log Levels
- **ERROR**: System failures, exceptions
- **WARNING**: Degraded performance, rate limits hit
- **INFO**: Request lifecycle, deployments
- **DEBUG**: Detailed debugging (dev only)

#### Log Format
```python
# Structured JSON logging
{
  "timestamp": "2025-11-13T10:30:00Z",
  "level": "INFO",
  "request_id": "req_abc123",
  "event": "completion_generated",
  "duration_ms": 1234,
  "tokens": {
    "prompt": 100,
    "completion": 50,
    "total": 150
  },
  "cost_usd": 0.002
}
```

#### What to Log
- ✅ Request start/end
- ✅ Errors and exceptions
- ✅ Performance metrics
- ✅ Cost per request
- ❌ API keys or secrets
- ❌ Full request/response bodies (too verbose)

### Performance Monitoring

#### Key Metrics
```yaml
Throughput:
  - tokens_per_second
  - requests_per_second

Latency:
  - time_to_first_token (TTFT)
  - total_generation_time
  - p50, p95, p99 latencies

Resources:
  - gpu_utilization
  - memory_usage
  - active_workers

Costs:
  - cost_per_request
  - cost_per_million_tokens
  - daily_spend
```

#### Alerting Thresholds
- Latency P95 > 2000ms
- Error rate > 5%
- GPU utilization > 95% for >10 min
- Daily costs > $50
- No requests for >1 hour (prod only)

---

## 📚 Documentation Standards

### Documentation Requirements

#### All Code Changes Must Update
1. **Inline comments** - For complex logic
2. **Docstrings** - For all functions/classes
3. **README.md** - If user-facing changes
4. **todo.md** - Mark tasks complete
5. **project-outline.md** - If architecture changes
6. **This rulebook** - If process changes

### Documentation Quality

#### Good Documentation
```markdown
## Deploying to Production

1. **Merge dev to main**:
   ```bash
   git checkout main
   git merge dev
   git push origin main
   ```

2. **Monitor deployment**:
   - Check GitHub Actions logs
   - Verify endpoint health: `curl https://api.../health`
   - Watch for errors in RunPod dashboard

3. **Validate performance**:
   ```bash
   python scripts/benchmark.py --endpoint prod
   ```

Expected: >450 TPS, <1200ms latency
```

#### Bad Documentation
```markdown
## Deploy
Run the deploy script.
```

### Keep Docs Updated

- [ ] Update docs in same PR as code changes
- [ ] Review docs quarterly for accuracy
- [ ] Remove outdated information
- [ ] Add examples for new features

---

## 🔄 Continuous Improvement

### Regular Reviews

#### Weekly
- Review active todos in todo.md
- Check cost trends
- Review error logs
- Update documentation

#### Monthly
- Performance benchmark comparison
- Dependency updates
- Security audit
- Cost optimization review

#### Quarterly
- Architecture review
- Technology updates (vLLM, PyTorch)
- Process improvements
- Rulebook updates

### Metrics-Driven Decisions

Before making changes, measure:
1. Current baseline metrics
2. Expected improvement
3. Cost implications
4. Risk assessment

After changes:
1. Compare to baseline
2. Document results
3. Update targets if needed

---

## 🎯 Definition of Done

### Feature is Done When

- [ ] Code written and tested locally
- [ ] Unit tests added/updated
- [ ] Integration tests passing
- [ ] Documentation updated
- [ ] Code reviewed (if team >1)
- [ ] Deployed to dev
- [ ] Tested in dev environment
- [ ] Performance validated
- [ ] Cost impact verified
- [ ] Merged to dev branch
- [ ] todo.md updated

### Ready for Production When

- [ ] All "Feature Done" criteria met
- [ ] Tested in dev for 24+ hours
- [ ] No critical errors
- [ ] Performance meets targets
- [ ] Cost within budget
- [ ] Monitoring configured
- [ ] Rollback plan tested
- [ ] Changelog updated
- [ ] Deployed to prod
- [ ] Post-deployment validation passed

---

## 🚫 Anti-Patterns to Avoid

### Code Anti-Patterns
- ❌ Hardcoded secrets or API keys
- ❌ Using `time.sleep()` for synchronization
- ❌ Ignoring error handling
- ❌ Global mutable state
- ❌ Magic numbers without constants

### Configuration Anti-Patterns
- ❌ Different configs for same environment
- ❌ Secrets in version control
- ❌ Inconsistent naming conventions
- ❌ Missing default values

### Deployment Anti-Patterns
- ❌ Deploying untested code
- ❌ Skipping staging environment
- ❌ No rollback plan
- ❌ Deploying on Fridays (unless critical)
- ❌ Multiple changes in one deployment

### Cost Anti-Patterns
- ❌ No workers_max limit
- ❌ workers_min > 0 without justification
- ❌ Not using network volumes
- ❌ Running dev 24/7

---

## 📞 Getting Help

### Troubleshooting Order
1. Check docs/TROUBLESHOOTING.md
2. Review recent changes in git log
3. Check RunPod dashboard
4. Review application logs
5. Test in dev environment
6. Create GitHub issue with details

### When Creating Issues

Include:
- Environment (dev/prod)
- Steps to reproduce
- Expected vs actual behavior
- Relevant logs
- Cost impact (if applicable)
- Configuration details

---

## ✅ Compliance Checklist

Use this checklist for every significant change:

### Before Coding
- [ ] Requirement clearly understood
- [ ] Cost impact estimated
- [ ] Approach discussed (if team >1)
- [ ] Todo item created

### During Development
- [ ] Following code style guide
- [ ] Writing tests as you go
- [ ] Documenting as you code
- [ ] Committing regularly

### Before PR
- [ ] All tests passing
