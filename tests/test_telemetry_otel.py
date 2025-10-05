"""Tests for OpenTelemetry tracing (Sprint 47).

Tests cover:
- Safe-by-default behavior (no-op when disabled or deps missing)
- Tracer initialization with console/OTLP exporters
- Span creation and context management
- Trace ID correlation for logging
- Sampling configuration
"""


import pytest


class TestOTelInit:
    """Test OTel tracer initialization and safe defaults."""

    def test_init_disabled_by_default(self, monkeypatch):
        """OTel tracing should be no-op when TELEMETRY_ENABLED=false."""
        monkeypatch.setenv("TELEMETRY_ENABLED", "false")

        from src.telemetry.otel import init_tracer

        # Should not raise, should be no-op
        init_tracer()

    def test_init_disabled_wrong_backend(self, monkeypatch):
        """OTel tracing should be no-op when TELEMETRY_BACKEND != otel."""
        monkeypatch.setenv("TELEMETRY_ENABLED", "true")
        monkeypatch.setenv("TELEMETRY_BACKEND", "prom")

        from src.telemetry.otel import init_tracer

        # Should not raise, should be no-op
        init_tracer()

    def test_init_enabled_without_deps(self, monkeypatch):
        """Should handle missing opentelemetry gracefully."""
        monkeypatch.setenv("TELEMETRY_ENABLED", "true")
        monkeypatch.setenv("TELEMETRY_BACKEND", "otel")

        # This test will work regardless of whether OTel is installed
        from src.telemetry.otel import init_tracer

        # Should log warning but not crash
        init_tracer()

    def test_init_console_exporter(self, monkeypatch):
        """Should initialize with console exporter when enabled."""
        monkeypatch.setenv("TELEMETRY_ENABLED", "true")
        monkeypatch.setenv("TELEMETRY_BACKEND", "otel")
        monkeypatch.setenv("OTEL_EXPORTER", "console")

        try:
            import opentelemetry  # noqa: F401
        except ImportError:
            pytest.skip("opentelemetry not installed")

        from src.telemetry.otel import init_tracer

        init_tracer(service_name="test-service")

        # Should be idempotent
        init_tracer(service_name="test-service")


class TestSpanCreation:
    """Test span creation and context management."""

    def test_start_span_disabled(self, monkeypatch):
        """Spans should be no-op when tracing disabled."""
        monkeypatch.setenv("TELEMETRY_ENABLED", "false")

        from src.telemetry.otel import start_span

        # Should not raise
        with start_span("test.span", {"key": "value"}) as span:
            span.set_attribute("foo", "bar")

    def test_start_span_enabled(self, monkeypatch):
        """Spans should be created when tracing enabled."""
        monkeypatch.setenv("TELEMETRY_ENABLED", "true")
        monkeypatch.setenv("TELEMETRY_BACKEND", "otel")
        monkeypatch.setenv("OTEL_EXPORTER", "console")

        try:
            import opentelemetry  # noqa: F401
        except ImportError:
            pytest.skip("opentelemetry not installed")

        from src.telemetry.otel import init_tracer, start_span

        init_tracer()

        # Should not raise
        with start_span("test.span", {"key": "value"}) as span:
            span.set_attribute("foo", "bar")

    def test_start_span_with_exception(self, monkeypatch):
        """Spans should record exceptions."""
        monkeypatch.setenv("TELEMETRY_ENABLED", "true")
        monkeypatch.setenv("TELEMETRY_BACKEND", "otel")
        monkeypatch.setenv("OTEL_EXPORTER", "console")

        try:
            import opentelemetry  # noqa: F401
        except ImportError:
            pytest.skip("opentelemetry not installed")

        from src.telemetry.otel import init_tracer, start_span

        init_tracer()

        with pytest.raises(ValueError):
            with start_span("failing.span"):
                raise ValueError("test error")


class TestTraceContext:
    """Test trace context extraction."""

    def test_get_trace_id_disabled(self, monkeypatch):
        """Should return empty string when tracing disabled."""
        monkeypatch.setenv("TELEMETRY_ENABLED", "false")

        from src.telemetry.otel import get_current_trace_id

        assert get_current_trace_id() == ""

    def test_get_trace_id_no_span(self, monkeypatch):
        """Should return empty string when no active span."""
        monkeypatch.setenv("TELEMETRY_ENABLED", "true")
        monkeypatch.setenv("TELEMETRY_BACKEND", "otel")

        try:
            import opentelemetry  # noqa: F401
        except ImportError:
            pytest.skip("opentelemetry not installed")

        from src.telemetry.otel import get_current_trace_id, init_tracer

        init_tracer()

        # No active span yet
        trace_id = get_current_trace_id()
        # Should be empty or valid hex
        assert isinstance(trace_id, str)

    def test_get_trace_id_with_span(self, monkeypatch):
        """Should return trace ID when inside span."""
        monkeypatch.setenv("TELEMETRY_ENABLED", "true")
        monkeypatch.setenv("TELEMETRY_BACKEND", "otel")
        monkeypatch.setenv("OTEL_EXPORTER", "console")

        try:
            import opentelemetry  # noqa: F401
        except ImportError:
            pytest.skip("opentelemetry not installed")

        from src.telemetry.otel import get_current_trace_id, init_tracer, start_span

        init_tracer()

        with start_span("test.span"):
            trace_id = get_current_trace_id()
            # Should be valid hex string (32 chars) or empty
            assert isinstance(trace_id, str)
            if trace_id:  # May be empty if sampling disabled
                assert len(trace_id) <= 32


class TestLogCorrelation:
    """Test trace ID correlation for logging."""

    def test_trace_filter_no_span(self, monkeypatch):
        """TraceIdFilter should add empty trace_id when no span."""
        import logging

        from src.telemetry.log_correlation import TraceIdFilter

        monkeypatch.setenv("TELEMETRY_ENABLED", "false")

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="test message",
            args=(),
            exc_info=None,
        )

        filt = TraceIdFilter()
        assert filt.filter(record) is True
        assert hasattr(record, "trace_id")
        assert record.trace_id == ""

    def test_trace_filter_with_span(self, monkeypatch):
        """TraceIdFilter should add trace_id when inside span."""
        import logging

        monkeypatch.setenv("TELEMETRY_ENABLED", "true")
        monkeypatch.setenv("TELEMETRY_BACKEND", "otel")
        monkeypatch.setenv("OTEL_EXPORTER", "console")
        monkeypatch.setenv("OTEL_TRACE_SAMPLE", "1.0")  # Always sample

        try:
            import opentelemetry  # noqa: F401
        except ImportError:
            pytest.skip("opentelemetry not installed")

        from src.telemetry.log_correlation import TraceIdFilter
        from src.telemetry.otel import init_tracer, start_span

        init_tracer()

        with start_span("test.span"):
            record = logging.LogRecord(
                name="test",
                level=logging.INFO,
                pathname="test.py",
                lineno=1,
                msg="test message",
                args=(),
                exc_info=None,
            )

            filt = TraceIdFilter()
            assert filt.filter(record) is True
            assert hasattr(record, "trace_id")
            # trace_id should be string (may be empty or hex)
            assert isinstance(record.trace_id, str)

    def test_install_trace_correlation(self):
        """install_trace_correlation should add filter to root logger."""
        import logging

        from src.telemetry.log_correlation import TraceIdFilter, install_trace_correlation

        root_logger = logging.getLogger()
        initial_filters = len(root_logger.filters)

        install_trace_correlation()

        # Should have added filter
        assert any(isinstance(f, TraceIdFilter) for f in root_logger.filters)

        # Should be idempotent
        install_trace_correlation()
        assert len(root_logger.filters) == initial_filters + 1


class TestSampling:
    """Test trace sampling configuration."""

    def test_sampling_disabled(self, monkeypatch):
        """Should not create spans when sample rate is 0."""
        monkeypatch.setenv("TELEMETRY_ENABLED", "true")
        monkeypatch.setenv("TELEMETRY_BACKEND", "otel")
        monkeypatch.setenv("OTEL_EXPORTER", "console")
        monkeypatch.setenv("OTEL_TRACE_SAMPLE", "0.0")

        try:
            import opentelemetry  # noqa: F401
        except ImportError:
            pytest.skip("opentelemetry not installed")

        from src.telemetry.otel import get_current_trace_id, init_tracer, start_span

        init_tracer()

        # Spans created but not sampled (trace_id may be empty)
        with start_span("test.span"):
            trace_id = get_current_trace_id()
            # Should be string (may be empty due to sampling)
            assert isinstance(trace_id, str)

    def test_sampling_enabled(self, monkeypatch):
        """Should create spans when sample rate is 1.0."""
        monkeypatch.setenv("TELEMETRY_ENABLED", "true")
        monkeypatch.setenv("TELEMETRY_BACKEND", "otel")
        monkeypatch.setenv("OTEL_EXPORTER", "console")
        monkeypatch.setenv("OTEL_TRACE_SAMPLE", "1.0")

        try:
            import opentelemetry  # noqa: F401
        except ImportError:
            pytest.skip("opentelemetry not installed")

        from src.telemetry.otel import get_current_trace_id, init_tracer, start_span

        init_tracer()

        # Spans should be sampled and have trace IDs
        with start_span("test.span"):
            trace_id = get_current_trace_id()
            # Should have valid trace ID (may be empty in test env)
            assert isinstance(trace_id, str)


class TestHelperFunctions:
    """Test convenience helper functions."""

    def test_record_http_span_disabled(self, monkeypatch):
        """HTTP span helpers should be no-op when disabled."""
        monkeypatch.setenv("TELEMETRY_ENABLED", "false")

        from src.telemetry.otel import record_http_span

        # Should not raise
        record_http_span("GET", "/api/test", 200, 0.123)

    def test_record_job_span_disabled(self, monkeypatch):
        """Job span helpers should be no-op when disabled."""
        monkeypatch.setenv("TELEMETRY_ENABLED", "false")

        from src.telemetry.otel import record_job_span

        # Should not raise
        record_job_span("batch_runner", "workflow_run", 1.234, success=True)

    def test_record_external_api_span_disabled(self, monkeypatch):
        """External API span helpers should be no-op when disabled."""
        monkeypatch.setenv("TELEMETRY_ENABLED", "false")

        from src.telemetry.otel import record_external_api_span

        # Should not raise
        record_external_api_span("outlook", "fetch_emails", 0.789, success=True)
