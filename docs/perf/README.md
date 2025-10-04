# Performance Optimization & Budget

## Overview

This directory tracks performance optimization efforts across Sprints 42-44 and provides tooling for CI-based performance budgets.

## Performance Budget & Trend

### Baseline Management

- **Baseline location**: `dashboards/ci/baseline.json`
- **Contents**: Total test duration and top-25 sum (in seconds)
- **Refresh**: Nightly workflow emits candidate baseline as artifact; manually curated and committed

### PR Performance Checks

PR CI runs `scripts/ci_perf_budget.py` to compare current test durations vs baseline:

- **Soft thresholds**:
  - ⚠️ **Warn**: >10% slower than baseline
  - 🚨 **Attention**: >25% slower than baseline
- **Artifacts**: `perf-report.md` attaches to PR and is posted as a comment
- **Gate**: Soft only - does not block PR merge, just visibility

### Refreshing Baseline Locally

To generate a new baseline locally:

```bash
make perf-baseline
```

This will:
1. Run fast tests with `--durations=25`
2. Generate `perf-report.md` with current vs baseline comparison
3. Output JSON metrics for manual review

If the numbers look good and represent an intentional improvement:
1. Review `perf-report.md`
2. Update `dashboards/ci/baseline.json` with the new total/top25 values
3. Commit the updated baseline

### Environment Variables

- `PERF_WARN_PCT`: Warning threshold percentage (default: 10)
- `PERF_FAIL_PCT`: Attention threshold percentage (default: 25)
- `TEST_OFFLINE`: Controls network blocking in tests (default: 1 in CI)

## Sprint History

### Sprint 42: Perf & Telemetry Groundwork

- Perf timing infrastructure (`dashboards/ci/slowest-tests.md`)
- Telemetry stub (no-op placeholder)
- Nightly duration tracking workflow
- Baseline for Sprint 43 improvements

### Sprint 43: Test Performance Optimization

**Goal**: 20% reduction in full e2e test suite duration

Three issues addressed to achieve ≥20% e2e suite speedup (tests/CI/docs only - no runtime changes):

1. **Issue #15 - Network/External Call Mocking** ✅
   - Socket-level outbound blocking (`tests/utils/netblock.py`)
   - HTTP mocking utilities (`tests/utils/http_fakes.py`)
   - TEST_OFFLINE environment variable control
   - Expected impact: ≥20% reduction by eliminating real API calls

2. **Issue #14 - Batch Operations & Parametrization** ✅
   - Session-scoped corpus fixtures with LRU caching
   - Memoized corpus loading
   - Consolidated parametrization patterns
   - Reduced redundant setup/teardown

3. **Issue #13 - Fixture Scope & I/O Reduction** ✅
   - Session-scoped shared workspace (`shared_tmpdir`)
   - Polling utility (`wait_until`) to replace time.sleep()
   - Reduced I/O and temporal dependencies
   - Faster iteration cycles

**Baseline (pre-Sprint 43)**:
- Total measured duration: 35.94s across top 25 tests
- Slowest test: `test_full_inbox_drive_sweep_workflow` - 3.45s
- Target: Reduce to ~29s (20% improvement)

### Sprint 44: Performance Budget & Trend

- CI performance budget script (`scripts/ci_perf_budget.py`)
- Baseline tracking in `dashboards/ci/baseline.json`
- Automated PR performance reports with soft gates
- Makefile target for local baseline refresh (`make perf-baseline`)
- Self-updating performance monitoring

## Best Practices

### Test Performance

1. **Use appropriate fixture scopes**: `session` or `module` for expensive resources
2. **Mock external calls**: Use provided utilities in `tests/utils/`
3. **Avoid time.sleep()**: Use `wait_until()` for time-dependent tests
4. **Minimize I/O**: Use `shared_tmpdir` or in-memory alternatives
5. **Cache expensive computations**: Use `@lru_cache` for test data generation
6. **Batch operations**: Consolidate setup/teardown with parametrization

### Performance Budget

1. **Monitor PR reports**: Check `perf-report.md` artifact on your PRs
2. **Investigate slowdowns**: If >10% slower, review what changed
3. **Update baseline intentionally**: After merging optimizations, update baseline
4. **Don't game the metrics**: Baseline should reflect actual test suite health
5. **Run local checks**: Use `make perf-baseline` before pushing perf-sensitive changes

### Non-Goals

❌ **Not in scope for perf work**:
- Changing test assertions or reducing coverage
- Skipping flaky tests without investigation
- Introducing new test infrastructure dependencies
- Modifying application runtime behavior

## References

- [OPERATIONS.md](../OPERATIONS.md) - Operational guidance
- [CONTRIBUTING.md](../../CONTRIBUTING.md) - Development setup and testing
- [dashboards/ci/slowest-tests.md](../../dashboards/ci/slowest-tests.md) - Historical slow test tracking
- [scripts/ci_perf_budget.py](../../scripts/ci_perf_budget.py) - Performance budget script
