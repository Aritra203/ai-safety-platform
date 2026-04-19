# 🚀 DEPLOYMENT CHECKLIST

Quick reference for deploying the optimized SafeGuard AI system.

## Pre-Deployment

- [ ] **Code Review**
  - Review all changes in `ai_services/toxicity.py`
  - Review cache logic in `backend/services/analysis_service.py`
  - Review OCR parallelization in `backend/utils/ocr.py`
  - Review explainability changes in `backend/utils/explainability.py`

- [ ] **Environment Setup**
  - [ ] Python 3.9+ installed
  - [ ] GPU drivers updated (if using CUDA)
  - [ ] Redis server running (`redis-cli ping` returns PONG)
  - [ ] MongoDB running (for data persistence)

- [ ] **Dependencies**
  ```bash
  pip install -r requirements.txt
  # Verify installations
  python -c "import torch, transformers, redis; print('✅ All imports OK')"
  ```

## Configuration

- [ ] **Update `.env.production`**
  ```bash
  # AI Model Configuration
  HF_MODEL_NAME=microsoft/deberta-v3-base
  HF_DEVICE=cuda           # or cpu
  HF_USE_QUANTIZATION=true
  HF_CACHE_DIR=/models/huggingface
  
  # Redis Cache
  REDIS_URL=redis://localhost:6379/0
  
  # Logging
  LOG_LEVEL=INFO
  DEBUG=false
  ```

- [ ] **Download Model (one-time)**
  ```bash
  python -c "from transformers import AutoModel; \
    AutoModel.from_pretrained('microsoft/deberta-v3-base', \
    cache_dir='./models')"
  # Or set HF_CACHE_DIR environment variable
  ```

- [ ] **Verify Settings**
  ```bash
  python -c "from backend.config.settings import settings; \
    print(f'Model: {settings.HF_MODEL_NAME}'); \
    print(f'Quantization: {settings.HF_USE_QUANTIZATION}'); \
    print(f'Device: {settings.HF_DEVICE}')"
  ```

## Testing

- [ ] **Run Performance Benchmark**
  ```bash
  cd scripts
  python benchmark.py
  # Should show:
  # ✅ Total estimate: ~270ms
  # ✅ Accuracy: 100% or higher
  # ✅ Throughput: >100 req/sec
  ```

- [ ] **Test Core Functionality**
  ```bash
  # Start backend
  cd backend
  uvicorn main:app --reload --port 8000
  
  # In another terminal, test endpoints
  curl -X POST http://localhost:8000/analyze-text \
    -H "Content-Type: application/json" \
    -d '{"text": "You are stupid"}'
  
  # Expected: { "risk_level": "HIGH", "overall_score": 0.75+ }
  ```

- [ ] **Test Cache Functionality**
  ```python
  import requests
  import time
  
  # First call (miss)
  start = time.time()
  r1 = requests.post("http://localhost:8000/analyze-text",
                     json={"text": "Same message here"})
  first = time.time() - start
  
  # Second call (hit)
  start = time.time()
  r2 = requests.post("http://localhost:8000/analyze-text",
                     json={"text": "Same message here"})
  second = time.time() - start
  
  print(f"First: {first*1000:.1f}ms, Second: {second*1000:.1f}ms")
  # Expected: Second should be ~10ms (cache hit)
  ```

- [ ] **Validate Model Quantization** (optional)
  ```bash
  python -c "from ai_services.toxicity import ToxicityClassifier; \
    clf = ToxicityClassifier(); \
    print(f'Quantized: {clf._is_quantized}')"
  # Expected: Quantized: True
  ```

## Staging Deployment

- [ ] **Docker Build** (if using Docker)
  ```bash
  docker build -f Dockerfile.backend -t safeguard-ai:v2 .
  
  # Test in container
  docker run --rm -p 8000:8000 \
    -e HF_MODEL_NAME=microsoft/deberta-v3-base \
    -e HF_USE_QUANTIZATION=true \
    safeguard-ai:v2
  ```

- [ ] **Redis Testing**
  ```bash
  # Check Redis connection
  redis-cli ping  # Should return PONG
  
  # Check memory
  redis-cli info memory | grep used_memory_human
  
  # Run caching test
  python -c "from backend.services.analysis_service import AnalysisService; \
    svc = AnalysisService(None); \
    print(f'Cache available: {svc.cache is not None}')"
  ```

- [ ] **Load Testing** (optional, with concurrent requests)
  ```bash
  # Using Apache Bench
  ab -n 100 -c 10 -p test_payload.json -T application/json \
    http://localhost:8000/analyze-text
  
  # Expected: ~15-20 req/sec with sequential baseline
  # Should be faster with cache hits
  ```

## Production Deployment

### Option A: Single Server (Small Scale)
```bash
# 1. Pull latest code
git pull origin main

# 2. Install dependencies
pip install -r requirements.txt

# 3. Update env
cp .env.production .env

# 4. Start server
uvicorn backend.main:app \
  --host 0.0.0.0 --port 8000 \
  --workers 4
```

### Option B: Docker Compose (Medium Scale)
```bash
# 1. Update docker-compose.yml with new image
# 2. Pull/build
docker-compose pull
docker-compose build

# 3. Deploy
docker-compose down
docker-compose up -d

# 4. Verify
docker-compose logs -f backend
```

### Option C: Kubernetes (Large Scale)
```bash
# 1. Update deployment manifests
kubectl set image deployment/safeguard-backend \
  safeguard=safeguard-ai:v2 \
  -n production

# 2. Monitor rollout
kubectl rollout status deployment/safeguard-backend -n production

# 3. Verify services
kubectl get pods -n production
kubectl logs -n production deployment/safeguard-backend
```

## Post-Deployment Validation

- [ ] **Smoke Tests**
  ```bash
  # Test all endpoints
  TEST_URL="https://api.safeguard.ai"
  
  # Text analysis
  curl -X POST $TEST_URL/analyze-text \
    -H "Content-Type: application/json" \
    -d '{"text": "This is a test message"}'
  
  # Health check
  curl $TEST_URL/health
  # Expected: {"status": "ok", "version": "3.1.0"}
  ```

- [ ] **Latency Verification**
  ```bash
  # Check latency in logs
  tail -f /var/log/safeguard/api.log | grep "latency_ms"
  # Expected: ~250-300ms average
  ```

- [ ] **Error Rate Monitoring**
  ```bash
  # Check for errors
  grep "ERROR\|EXCEPTION" /var/log/safeguard/api.log
  # Expected: <0.1% error rate
  ```

- [ ] **Cache Hit Rate**
  ```bash
  redis-cli info stats | grep keyspace_hits
  # Expected: >25% hit rate after 1 hour
  ```

- [ ] **Model Performance**
  ```bash
  # Check accuracy metrics in monitoring dashboard
  # F1 score should be >0.85
  # False positive rate should be <3%
  ```

## Rollback Plan

If issues occur:

```bash
# 1. Identify issue
tail -f /var/log/safeguard/api.log

# 2. Check common problems
docker logs safeguard-backend 2>&1 | grep ERROR

# 3. Rollback to previous version
docker-compose down
git checkout HEAD~1
docker-compose up -d

# OR with Kubernetes
kubectl rollout undo deployment/safeguard-backend -n production
```

## Common Issues & Solutions

### Issue: Model Loading Fails
```
ERROR: HuggingFace model unavailable — using rule-only mode
```
**Solution**:
```bash
# Download model
python -c "from transformers import AutoModel; \
  AutoModel.from_pretrained('microsoft/deberta-v3-base')"

# Or set HF_CACHE_DIR to persistent location
export HF_CACHE_DIR=/mnt/models
```

### Issue: Slow Inference (>500ms)
**Causes**: GPU not available, quantization disabled, large batch size

**Solution**:
```bash
# Check GPU
nvidia-smi

# Verify settings
HF_DEVICE=cuda  # Set to cuda if GPU available
HF_USE_QUANTIZATION=true  # Enable quantization
```

### Issue: Cache Not Working
**Causes**: Redis not running, REDIS_URL wrong

**Solution**:
```bash
# Check Redis
redis-cli ping  # Should return PONG

# Verify URL
echo $REDIS_URL  # Should be redis://localhost:6379/0
```

### Issue: High False Positive Rate
**Cause**: Model threshold too low

**Solution**:
```python
# In backend/utils/risk_engine.py
# Increase thresholds:
THREAT_THRESHOLD = 0.65  # was 0.55
SEXUAL_HARASSMENT_THRESHOLD = 0.55  # was 0.50
```

## Monitoring & Alerts

- [ ] **Set up dashboards** (Grafana/DataDog)
  - Inference latency (target: 250-300ms)
  - Cache hit rate (target: >25%)
  - Error rate (target: <0.1%)
  - Model F1 score (target: >0.85)

- [ ] **Configure alerts**
  - Latency > 500ms
  - Error rate > 1%
  - Cache hit rate < 10%
  - GPU memory > 90%

- [ ] **Daily checks**
  ```bash
  # Morning check script
  #!/bin/bash
  echo "=== SafeGuard Health Check ==="
  echo "API status: $(curl -s http://localhost:8000/health | jq '.status')"
  echo "Cache hits: $(redis-cli info stats | grep keyspace_hits)"
  echo "Model accuracy: $(python scripts/check_model_accuracy.py)"
  ```

## Sign-Off

- [ ] **Performance Verified**
  - [ ] Latency: 270±30ms ✓
  - [ ] Throughput: >100 req/sec ✓
  - [ ] Cache hit rate: >20% ✓
  - [ ] Accuracy: F1 > 0.85 ✓

- [ ] **Safety Verified**
  - [ ] False positives: <3% ✓
  - [ ] Grooming detection: Recall > 90% ✓
  - [ ] No regressions vs baseline ✓

- [ ] **Deployment Approved**
  - [ ] Team lead approval: _______________
  - [ ] Date: _______________
  - [ ] Time: _______________
  - [ ] Rollback authority: _______________

---

## Quick Reference Commands

```bash
# Show current model
grep HF_MODEL_NAME .env.production

# Test latency
time python -c "from ai_services.toxicity import ToxicityClassifier; \
  c = ToxicityClassifier(); c.classify('test')"

# Check cache
redis-cli DBSIZE
redis-cli INFO stats

# View logs
docker logs -f safeguard-backend
tail -f /var/log/safeguard/api.log | grep "latency"

# Restart service
systemctl restart safeguard-backend
# or
docker-compose restart backend
# or
kubectl rollout restart deployment/safeguard-backend -n production

# Emergency rollback
git reset --hard HEAD~1
docker-compose up -d

# Check GPU
nvidia-smi
```

---

**Last Updated**: April 2026
**Version**: 3.1.0 (DeBERTa-base + Quantization + Caching + Parallel OCR)
**Status**: Production Ready ✅
