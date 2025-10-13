# OpenAI Integration

## What this integrates

OpenAI GPT-4 API for natural language to structured action planning. Used by the `/ai/plan` endpoint to convert user prompts into executable action sequences.

## Where it's configured

- Railway Dashboard → Relay service → Variables → `OPENAI_API_KEY`
- `src/ai/planner.py` - Main planning logic with GPT-4 calls
- `requirements.txt` - `openai==1.61.0` package
- `src/webapi.py` - `/ai/plan` endpoint

## Env vars / secrets

| Name | Scope | Where set | Notes |
|------|-------|-----------|-------|
| `OPENAI_API_KEY` | Runtime | Railway Variables | Format: `sk-proj-...` (never commit to Git) |

## How to verify (60 seconds)

```bash
# 1. Test /ai/plan endpoint (requires API key + auth)
curl -X POST https://relay-production-f2a6.up.railway.app/ai/plan \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer relay_sk_demo_preview_key" \
  -d '{"prompt": "Send an email to test@example.com"}'
# Should return: {"intent":"send_email", "steps":[...], "confidence":0.9}

# 2. Check for OpenAI errors in logs
railway logs | grep "openai"
# Should not show "No module named 'openai'" or "Invalid API key"

# 3. Verify mock mode disabled (production)
curl https://relay-production-f2a6.up.railway.app/ai/plan \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer relay_sk_demo_preview_key" \
  -d '{"prompt":"test"}' | grep "mock mode"
# Should return empty (no mock mode message)

# 4. Test local with OpenAI key
export OPENAI_API_KEY="sk-proj-..."
python -c "from src.ai import ActionPlanner; import asyncio; print(asyncio.run(ActionPlanner().plan('test')))"
# Should return action plan (not mock response)
```

## Common failure → quick fix

### "No module named 'openai'"
**Cause:** openai package not installed in deployment
**Fix:**
```bash
# Add to requirements.in
echo "openai>=1.0.0" >> requirements.in
# Regenerate requirements.txt
pip-compile requirements.in
# Commit and push
git add requirements.in requirements.txt
git commit -m "fix: add openai dependency"
git push origin main
```

### "Invalid API key" or 401 Unauthorized
**Cause:** OPENAI_API_KEY not set or expired/invalid
**Fix:**
1. Get fresh API key from https://platform.openai.com/api-keys
2. Update Railway → Relay service → Variables → OPENAI_API_KEY
3. Wait for automatic redeployment (~2 min)

### "Rate limit exceeded"
**Cause:** Too many requests or quota exceeded
**Fix:**
- Check OpenAI dashboard for rate limits and usage
- Implement caching for common prompts (future enhancement)
- Add retry logic with exponential backoff (already in planner.py)

### Mock mode in production (returns low confidence)
**Cause:** OPENAI_API_KEY not set, so planner falls back to mock
**Fix:**
1. Verify Railway → Variables → OPENAI_API_KEY is set
2. Check for typo in variable name (must be exact: `OPENAI_API_KEY`)
3. Restart service: Railway → Service → Restart

## Cost note

- Model: `gpt-4o` (optimized, cheaper than gpt-4)
- Typical cost: ~$0.01-0.05 per planning request
- Set usage limits in OpenAI dashboard to prevent runaway costs
- Monitor: https://platform.openai.com/usage

## References

- src/ai/planner.py:137-193 - `_call_llm` method with OpenAI client
- src/ai/planner.py:46-48 - Mock mode fallback if OPENAI_API_KEY not set
- src/webapi.py - `/ai/plan` endpoint (requires `actions:preview` scope)
- requirements.txt:94 - openai==1.61.0 dependency
