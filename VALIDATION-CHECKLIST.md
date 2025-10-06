# 24-Hour Staging Validation Checklist

Sprint 48 operational validation for Railway staging deployment.

## Pre-Validation Setup

- [x] Prometheus config created (`prometheus.yml`)
- [x] Alert rules defined (`alerts.yml`)
- [x] Traffic generator script ready (`scripts/generate-traffic.ps1`)
- [x] Grafana queries documented (`grafana-queries.md`)

## Hour 0: Initial Setup

### 1. Start Prometheus + Grafana
```powershell
cd C:\Users\kylem\openai-agents-workflows-2025.09.28-v1

# Start Prometheus
docker run -d --name prom -p 9090:9090 `
  -v ${PWD}\prometheus.yml:/etc/prometheus/prometheus.yml `
  -v ${PWD}\alerts.yml:/etc/prometheus/alerts.yml `
  prom/prometheus --config.file=/etc/prometheus/prometheus.yml

# Start Grafana
docker run -d --name grafana -p 3000:3000 grafana/grafana
```

### 2. Configure Grafana
- [ ] Access http://localhost:3000 (admin/admin)
- [ ] Add Prometheus data source: http://host.docker.internal:9090
- [ ] Create Golden Signals dashboard using queries from `grafana-queries.md`
- [ ] Verify panels populate within 1-2 minutes

### 3. Generate Initial Traffic
```powershell
.\scripts\generate-traffic.ps1 -Count 50 -Interval 2
```

### 4. Verify Prometheus Targets
- [ ] Visit http://localhost:9090/targets
- [ ] Confirm `djp-workflow-staging` target is UP
- [ ] Check scrape duration < 1s

---

## Continuous Monitoring (Every 4 Hours)

### Hour 0, 4, 8, 12, 16, 20, 24

**Generate Traffic:**
```powershell
.\scripts\generate-traffic.ps1 -Count 30 -Interval 3
```

**Check Metrics:**
- [ ] Request rate stable (no unexpected spikes)
- [ ] Error rate < 1%
- [ ] P95 latency < 500ms for `/api/templates`
- [ ] P99 latency < 1s for `/api/templates`
- [ ] Memory not growing unbounded
- [ ] CPU usage reasonable (< 50% average)

**Check Logs:**
```powershell
railway logs --lines 50
```
- [ ] No errors or exceptions
- [ ] Uvicorn healthy (regular request logs)
- [ ] No memory warnings

---

## Hour 24: Final Validation

### 1. Review Dashboard Metrics
- [ ] Calculate average P50/P95/P99 latency over 24h
- [ ] Confirm < 0.5% error rate overall
- [ ] Verify no alert rule triggered (check Prometheus /alerts)
- [ ] Memory/CPU stable (no leaks)

### 2. Performance Baseline
```powershell
# If make target exists
make perf-baseline

# Or manually document baseline
$baseline = @{
    p50_ms = 10
    p95_ms = 250
    p99_ms = 500
    error_rate_pct = 0.1
    requests_per_min = 15
}
$baseline | ConvertTo-Json | Out-File dashboards/ci/baseline.json
```

### 3. Export Grafana Dashboard
- [ ] Export dashboard JSON from Grafana
- [ ] Save to `dashboards/golden-signals-staging.json`
- [ ] Commit to repository

### 4. Document Findings
```markdown
## 24-Hour Staging Validation Results

**Date:** YYYY-MM-DD
**Environment:** Railway Staging (relay-production-f2a6.up.railway.app)

### Metrics Summary
- Total requests: ~XXXX
- Average P50 latency: XXms
- Average P95 latency: XXms
- Average P99 latency: XXms
- Error rate: X.XX%
- Uptime: XX.X%

### Issues Encountered
- None / [List any issues]

### Action Items
- [ ] Enable hybrid backend (Prometheus + OTel)
- [ ] Set up Tempo for distributed tracing
- [ ] Configure alert notifications (Slack/Email)
```

---

## Success Criteria

**All must pass:**
- [x] Prometheus scraping working (target UP for 24h)
- [ ] Grafana dashboards showing data
- [ ] P95 latency < 500ms
- [ ] P99 latency < 1s
- [ ] Error rate < 1%
- [ ] No memory leaks (stable over 24h)
- [ ] Alert rules working (can trigger test alert)
- [ ] Traffic generator runs without errors

**If all pass:** Sprint 48 staging deployment validated ✅

**Next Steps:**
1. Enable OTel tracing (hybrid backend)
2. Sprint 49: Invite-only Beta with API keys
3. Production deployment planning

---

## Quick Commands Reference

**Generate traffic:**
```powershell
.\scripts\generate-traffic.ps1 -Count 50 -Interval 2
```

**Check Railway status:**
```powershell
railway status
railway logs --lines 100
```

**Query Prometheus:**
```powershell
# Request rate
curl "http://localhost:9090/api/v1/query?query=sum(rate(http_requests_total[5m]))"

# P95 latency
curl "http://localhost:9090/api/v1/query?query=histogram_quantile(0.95,%20sum(rate(http_request_duration_seconds_bucket[5m]))%20by%20(le))"
```

**Test endpoints:**
```powershell
curl https://relay-production-f2a6.up.railway.app/_stcore/health
curl https://relay-production-f2a6.up.railway.app/metrics | Select-Object -First 20
```

---

## Troubleshooting

**Prometheus not scraping:**
- Check `prometheus.yml` target URL
- Verify `/metrics` endpoint accessible: `curl https://relay-production-f2a6.up.railway.app/metrics`
- Check Prometheus logs: `docker logs prom`

**No data in Grafana:**
- Verify Prometheus data source connected
- Check query syntax in panel editor
- Wait 30-60s for first scrape

**High latency:**
- Check Railway logs for errors
- Verify no cold starts (keep-alive requests)
- Review resource limits in Railway dashboard

**Memory growth:**
- Check for Python memory leaks
- Review Prometheus metrics retention
- Consider adding memory limits in Dockerfile
