# Sprint 45 Plan: Micro-Cuts & Observability Design

## Goal

Continue performance momentum with small, surgical improvements and plan observability backend integration (tests/docs only - zero runtime changes unless explicitly scoped).

## Micro-Cuts (Test Performance)

### Remaining Low-Hanging Fruit
- [ ] Remove lingering `time.sleep()` calls in favor of `wait_until()` polling
- [ ] Shrink last large session fixtures (investigate lazy loading)
- [ ] Audit parametrized tests for redundant setup patterns
- [ ] Review e2e tests for unnecessary full-stack initialization

### Monitoring
- [ ] Keep CI PR suite <= 90s (soft target)
- [ ] Monitor trend in `dashboards/ci/slowest-tests.md` after nightly runs
- [ ] Update baseline.json when improvements stabilize

## Observability Design (Docs Only)

### Telemetry Backend Decision
Current state: Telemetry stub (no-op) in `src/telemetry/noop.py`

Options to evaluate (design doc only - no implementation):
1. **OpenTelemetry (OTel)**
   - Industry standard, vendor-neutral
   - Rich SDK for traces, metrics, logs
   - Flexible exporters (Jaeger, Tempo, Datadog, etc.)

2. **Prometheus + Grafana**
   - Battle-tested for metrics
   - Requires Prometheus server + scraping
   - Good for operational dashboards

3. **Hybrid Approach**
   - OTel for traces and structured logs
   - Prometheus for metrics
   - Best of both worlds, more complexity

### Design Doc Deliverables
- [ ] Create `docs/observability/BACKEND-EVALUATION.md`
- [ ] Document pros/cons of each option
- [ ] Recommend approach for next sprint implementation
- [ ] Outline integration points (no code changes yet)

## References

- [docs/perf/README.md](README.md) - Sprint 42-44 history
- [dashboards/ci/slowest-tests.md](../../dashboards/ci/slowest-tests.md) - Performance tracking
- [scripts/ci_perf_budget.py](../../scripts/ci_perf_budget.py) - Budget script
- [src/telemetry/noop.py](../../src/telemetry/noop.py) - Current telemetry stub

## Success Criteria

- [ ] At least 2 micro-cuts identified and documented (no implementation required yet)
- [ ] Observability backend evaluation doc complete
- [ ] No runtime behavior changes
- [ ] CI PR suite remains under 90s
