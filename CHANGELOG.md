# Changelog

All notable changes to djp-workflow will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - 2025-10-01

### Added
- (placeholder for new features)

### Changed
- (placeholder for changes)

### Fixed
- (placeholder for fixes)

## [1.0.2] - 2025-09-30
### Fixed
- Correct repository URLs in pyproject metadata.
- Align author email to GitHub noreply for privacy.

## [1.0.1] - 2025-09-30

### Fixed
- Updated remaining SECURITY.md email placeholder
- Fixed repository URLs in CHANGELOG.md
- Added comprehensive release documentation logs

## [1.0.0] - 2025-09-30

### Added

#### Core Workflow
- **Debate Engine**: Multi-agent debate system with 4 concurrent agents (OpenAI GPT-4, GPT-4o-mini, Claude, Gemini)
- **Judge System**: Strict 0-10 scoring rubric with task fit, factual support, and clarity evaluation
- **Publisher**: Verbatim publishing with provider allowlist and legal-safe fallback logic
- **Guardrails**: Content validation with long quote detection (>75 words) and safety flag analysis
- **CLI Interface**: Full command-line interface with argument parsing and environment validation

#### Grounded Mode (Full)
- **Corpus Loading**: Support for .txt, .md, and .pdf documents with TF-IDF search
- **Citation Extraction**: `[Source Title]` format with validation and snippet extraction
- **Citation Requirements**: Configurable minimum citations with judge disqualification
- **Search Fallback**: Keyword-based search when sklearn unavailable
- **Context Injection**: Automatic corpus context insertion for debate agents

#### Redaction Layer
- **12 Redaction Rules**: API keys, AWS credentials, emails, phone numbers, SSN, credit cards, IP addresses, URLs, JWT tokens, private keys
- **Luhn Validation**: Credit card validation to reduce false positives
- **Redaction Strategies**: Label (default), mask, and partial strategies
- **Configurable Rules**: JSON-based rule configuration with custom patterns
- **Citation-Safe**: Preserves `[Source Title]` format during redaction

#### Observability & Metrics
- **Streamlit Dashboard**: Real-time observability with filters and KPIs
- **Metrics Export**: CSV/JSON export with 30+ metrics including grounding and redaction
- **Alert System**: Configurable thresholds for error rates, latency, costs, grounding, and redaction
- **Cost Tracking**: Token usage and cost estimation per run
- **Retry Monitoring**: Exponential backoff tracking and retry statistics

#### Schema & Validation
- **Artifact Schema v1.1**: Backward-compatible schema with grounding and redaction metadata
- **Policy Schema**: Configurable workflow policies with debate, judge, and publish settings
- **JSON Schema Validation**: Runtime validation with `scripts/validate_artifacts.py`
- **Schema Versioning**: Documentation for schema evolution and backward compatibility

#### Testing & Quality
- **57 Test Cases**: Comprehensive test coverage across corpus, redaction, integration, and workflow
- **Unit Tests**: 15 corpus tests, 22 redaction tests, 8 grounded publish tests
- **Integration Tests**: 12 end-to-end grounded workflow tests
- **CI Scripts**: Automated testing scripts for PowerShell and Bash

#### Documentation
- **Operations Guide**: 350+ line comprehensive guide (docs/OPERATIONS.md)
- **API Documentation**: Inline docstrings for all public functions
- **Sprint Logs**: 8 detailed sprint completion logs with implementation details
- **Setup Guides**: Night shift setup and project setup documentation

### Changed
- Updated artifact schema from v1.0 to v1.1 with grounding/redaction fields
- Enhanced metrics export with 6 new columns for grounded and redaction data
- Improved dashboard with grounded-only and redacted-only filters
- Extended alert thresholds with grounded and redacted monitoring

### Fixed
- Citation validation now handles fuzzy title matching
- Redaction preserves citation format during content sanitization
- Corpus search falls back gracefully when sklearn unavailable
- Judge scoring handles missing or malformed draft fields

### Security
- Redaction layer prevents PII/secrets exposure in artifacts
- API key masking in error messages
- Credit card validation with Luhn algorithm
- Private key detection in content

## [Unreleased]

### Planned
- Semantic embeddings for improved corpus search (OpenAI embeddings API)
- Multi-language redaction rules
- Custom citation formats beyond `[Title]`
- Real-time redaction monitoring dashboard
- Corpus versioning and change tracking
- Advanced NER for entity-based citations

---

## Version History

- **1.0.0** (2025-09-30): Initial release with complete DJP workflow, grounded mode, and redaction
- Pre-releases documented in sprint logs (2025.09.28 - 2025.09.30)

## Links

- [Repository](https://github.com/kmabbott81/djp-workflow)
- [Documentation](https://github.com/kmabbott81/djp-workflow/blob/main/docs/OPERATIONS.md)
- [Issues](https://github.com/kmabbott81/djp-workflow/issues)
- [Releases](https://github.com/kmabbott81/djp-workflow/releases)
