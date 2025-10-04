# Performance Optimization Notes

## Sprint 43: e2e Performance Cuts

**Goal**: 20% reduction in full e2e test suite duration

### Current Baseline

From `dashboards/ci/slowest-tests.md`:
- Total measured duration: 35.94s across top 25 tests
- Slowest test: `test_full_inbox_drive_sweep_workflow` - 3.45s
- Target: Reduce to ~29s (20% improvement)

### Optimization Techniques

**1. Fixture Scope Optimization**
- Use `session` or `module` scope for expensive fixtures
- Avoid per-function setup for database connections, API clients
- Cache computed test data across parametrized runs

**2. Network/External Call Mocking** ✅ **Issue #15 - Implemented**
- **Socket-level blocking**: `tests/utils/netblock.py` blocks outbound network at socket layer
- **HTTP mocking**: `tests/utils/http_fakes.py` provides httpx/requests stubs for connector APIs
- **TEST_OFFLINE control**: CI blocks by default; local allows override
- **Expected impact**: ≥20% reduction in e2e suite time by eliminating real API calls
- Replace real API calls with mocks or VCR cassettes
- Use in-memory databases instead of Redis/PostgreSQL where feasible
- Mock file system operations with tmpdir or in-memory structures

**3. Batch Operations & Parametrization**
- Chunk large batch operations for better memory usage
- Use pytest-xdist for parallel test execution
- Share expensive setup across parametrized test cases

**4. Temporal Dependencies**
- Replace `time.sleep()` with event polling (shorter timeouts)
- Use asyncio for concurrent I/O operations
- Mock time-dependent operations where possible

### Tracking

Performance improvements tracked in:
- `dashboards/ci/slowest-tests.md` - Updated after each nightly run
- GitHub Issues #13, #14, #15 - Specific optimization tickets
- Nightly workflow artifacts - Historical comparison

### Non-Goals

❌ **Not in scope for Sprint 43**:
- Changing test assertions or reducing coverage
- Skipping flaky tests without investigation
- Introducing new test infrastructure (pytest plugins, etc.)
- Modifying application runtime behavior

### Acceptance Criteria

- [ ] At least 2 of 3 performance issues (#13-#15) resolved
- [ ] Nightly `slowest-tests.md` shows 20%+ improvement in targeted tests
- [ ] CI PR suite remains under 90s
- [ ] All tests still pass with same assertions
- [ ] No new flaky tests introduced

---

**Reference**: See Sprint 42 (Perf & Telemetry Groundwork) for tooling infrastructure.
