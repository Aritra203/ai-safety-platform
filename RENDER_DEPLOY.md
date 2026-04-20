# Render Deployment Guide

This repo now includes a Render Blueprint in render.yaml for:
- Backend: FastAPI (Python runtime)
- Frontend: Next.js (Node)
- Redis: managed Redis service
- Context service: FastAPI endpoint for CONTEXT_LLM_ENDPOINT

## 1. Push your latest code

Use your normal Git workflow to push main branch updates.

## 2. Create Blueprint in Render

1. Open Render dashboard.
2. Click New + -> Blueprint.
3. Connect this GitHub repository.
4. Render detects render.yaml and shows 4 services:
   - safeguard-ai-backend
   - safeguard-ai-frontend
   - safeguard-ai-context-llm
   - safeguard-ai-redis
5. Click Apply.

## 3. Set required secrets before first successful deploy

### Backend service (safeguard-ai-backend)
- MONGODB_URI
- CLOUDINARY_CLOUD_NAME
- CLOUDINARY_API_KEY
- CLOUDINARY_API_SECRET

Optional:
- CONTEXT_LLM_ENDPOINT (auto-populated from context service URL)

### Frontend service (safeguard-ai-frontend)
- NEXTAUTH_SECRET
- GOOGLE_CLIENT_ID
- GOOGLE_CLIENT_SECRET

## 4. Update OAuth callback URLs (Google)

In Google Cloud Console -> OAuth credentials, add authorized redirect URI:
- https://safeguard-ai-frontend.onrender.com/api/auth/callback/google

If Render changes your frontend domain, update:
- Google redirect URI
- NEXTAUTH_URL env var on frontend
- ALLOWED_ORIGINS env var on backend

## 5. Verify deployment

Backend checks:
- GET /health
- GET /docs

Frontend checks:
- Home page loads
- Sign in works
- Dashboard can call backend endpoints

## 6. Notes for model loading

- Backend is configured with full model stack enabled.
- On cold start, first requests may be slower while models are loaded/downloaded.
- Current blueprint sets HF_DEVICE=cpu for Render compatibility.
- Native Python runtime may not include system Tesseract. OCR still works with EasyOCR/PaddleOCR when available.

## 7. Recommended production tuning

- CONTEXT_LLM_ENABLED is enabled by default and points to safeguard-ai-context-llm.
- If you want deterministic local-only behavior, keep CONTEXT_SERVICE_MODE=auto and do not set upstream env vars.
- If memory pressure occurs, lower model load by disabling HF_ENABLE_MULTILABEL_MODEL or move to a higher backend plan.

## 8. Set a stable CONTEXT_LLM_ENDPOINT

This blueprint now creates a dedicated context endpoint service by default:
- safeguard-ai-context-llm
- GET /health
- POST / and POST /v1/chat/completions

Backend env on safeguard-ai-backend is wired automatically:
- CONTEXT_LLM_ENABLED=true
- CONTEXT_LLM_ENDPOINT=<safeguard-ai-context-llm service URL>
- CONTEXT_LLM_MODEL=Qwen/Qwen2.5-7B-Instruct
- CONTEXT_LLM_TIMEOUT_MS=3000
- CONTEXT_ESCALATION_MIN_SCORE=0.55

The context service supports two modes:
- auto (default): tries upstream provider if configured, falls back to local heuristic scoring
- upstream: requires upstream provider and returns 502 if provider is unavailable

Context service env vars on safeguard-ai-context-llm:
- CONTEXT_SERVICE_MODE=auto
- UPSTREAM_CHAT_COMPLETIONS_URL (optional)
- UPSTREAM_API_KEY (optional)
- UPSTREAM_API_KEY_HEADER=Authorization
- UPSTREAM_API_KEY_PREFIX=Bearer
- UPSTREAM_TIMEOUT_MS=6000

Response format should return numeric scores in [0,1] for:
- cyberbullying
- threat
- hate_speech
- sexual_harassment
- grooming

Accepted upstream response styles:
- Top-level object with the keys above
- {"scores": {...}} wrapper
- OpenAI style choices[0].message.content containing JSON

Stability checklist:
- Keep p95 latency below timeout budget
- If using upstream provider, set UPSTREAM_CHAT_COMPLETIONS_URL and UPSTREAM_API_KEY
- Keep CONTEXT_SERVICE_MODE=auto unless you need strict upstream-only behavior
- Monitor context service logs for upstream timeouts or parse warnings

Validation after deploy:
- Deploy all services from blueprint
- Send /analyze-context request with high-risk conversation
- Confirm backend logs do not show "Context LLM escalation unavailable"
