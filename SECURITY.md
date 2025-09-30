# Security Policy

## Supported Versions

We release patches for security vulnerabilities. Currently supported versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take the security of djp-workflow seriously. If you believe you have found a security vulnerability, please report it to us as described below.

### Where to Report

**Please do NOT report security vulnerabilities through public GitHub issues.**

Instead, please report them via email to:

- **Email**: kbmabb@gmail.com
- **Subject**: [SECURITY] djp-workflow vulnerability

### What to Include

Please include the following information in your report:

1. **Description**: A clear description of the vulnerability
2. **Impact**: What could an attacker accomplish by exploiting this?
3. **Reproduction**: Step-by-step instructions to reproduce the issue
4. **Version**: The version of djp-workflow affected
5. **Environment**: OS, Python version, and any relevant configuration
6. **Proof of Concept**: Code or commands that demonstrate the vulnerability (if applicable)
7. **Suggested Fix**: If you have ideas for fixing the issue (optional)

### Example Report

```
Subject: [SECURITY] djp-workflow vulnerability - API key exposure

Description:
API keys may be logged in plaintext when debug logging is enabled.

Impact:
Attackers with access to log files could extract API keys and use them
to make unauthorized API calls.

Reproduction:
1. Enable debug logging: export DEBUG=1
2. Run workflow with API key set
3. Check logs in runs/ directory
4. API key appears in plaintext

Version: 1.0.0
Environment: Windows 11, Python 3.13

Proof of Concept:
[Attached log excerpt showing exposed key]

Suggested Fix:
Redact API keys in log output using the existing redaction module.
```

### Response Timeline

- **Initial Response**: Within 48 hours
- **Status Update**: Within 7 days
- **Fix Timeline**: Varies by severity
  - **Critical**: 1-7 days
  - **High**: 7-14 days
  - **Medium**: 14-30 days
  - **Low**: 30-90 days

### What Happens Next

1. We will acknowledge receipt of your vulnerability report
2. We will investigate and validate the vulnerability
3. We will work on a fix and keep you updated on progress
4. Once a fix is ready, we will:
   - Release a patched version
   - Publish a security advisory (if appropriate)
   - Credit you in the advisory (unless you prefer to remain anonymous)

## Security Best Practices

When using djp-workflow, follow these security best practices:

### API Key Management

- **Never commit API keys** to version control
- **Use environment variables** for API keys (`.env` file)
- **Rotate keys regularly**: Change API keys every 90 days
- **Use separate keys** for development and production
- **Apply least privilege**: Use API keys with minimal required permissions

### Redaction

- **Enable redaction by default**: Don't use `--redact off` in production
- **Review redaction rules**: Ensure `config/redaction_rules.json` covers your use case
- **Test redaction**: Verify sensitive data is properly redacted in output
- **Custom rules**: Add organization-specific patterns if needed

### Corpus Security

- **Validate corpus sources**: Only load trusted documents
- **Sanitize inputs**: Be cautious with user-provided corpus directories
- **Access control**: Restrict access to corpus directories
- **Review corpus content**: Ensure no sensitive data in corpus files

### Network Security

- **Use HTTPS**: All API calls use HTTPS by default
- **Firewall rules**: Restrict outbound connections if needed
- **Proxy support**: Configure proxy settings if required
- **Certificate validation**: Don't disable SSL verification

### Artifact Security

- **Secure storage**: Store artifacts in secure locations with appropriate permissions
- **Access logs**: Monitor access to artifact directories
- **Retention policy**: Delete old artifacts regularly
- **Backup security**: Encrypt backups of sensitive artifacts

### Configuration

- **Review policies**: Audit `policies/` directory for security settings
- **Validate schemas**: Use `scripts/validate_artifacts.py` regularly
- **Monitor alerts**: Set up `scripts/alerts.py` for security thresholds
- **Update dependencies**: Keep dependencies up to date

## Known Security Considerations

### Current Limitations

1. **In-Memory Drafts**: Draft content is unredacted in memory during processing
   - **Mitigation**: Redaction is applied before persistence
   - **Risk**: Memory dumps could expose unredacted content

2. **API Key Logging**: API keys could appear in error messages if exceptions occur
   - **Mitigation**: Use structured logging and filter sensitive fields
   - **Risk**: Debug logs may contain API keys

3. **File System Access**: The application can read arbitrary files specified by users
   - **Mitigation**: Validate file paths and use allowlists
   - **Risk**: Path traversal attacks if inputs are not sanitized

4. **Corpus Loading**: Loading untrusted corpus files could execute arbitrary code (if using malicious PDFs)
   - **Mitigation**: Only load corpus from trusted sources
   - **Risk**: PDF parsing vulnerabilities

### Planned Improvements

- [ ] Add API key masking in error messages
- [ ] Implement memory-safe redaction
- [ ] Add file path validation and sanitization
- [ ] Add corpus content scanning for malicious patterns

## Security Updates

Subscribe to security advisories:
- GitHub Security Advisories: [Watch this repository]
- Email notifications: [Enable GitHub notifications]

## Additional Resources

- [OWASP Secure Coding Practices](https://owasp.org/www-project-secure-coding-practices-quick-reference-guide/)
- [Python Security Best Practices](https://python.readthedocs.io/en/latest/library/security_warnings.html)
- [OpenAI API Security](https://platform.openai.com/docs/guides/safety-best-practices)

## Contact

For non-security questions, please use:
- GitHub Issues: Report bugs and request features
- GitHub Discussions: Ask questions and share ideas

For security issues only:
- Email: kbmabb@gmail.com
- Subject: [SECURITY] djp-workflow vulnerability

---

Thank you for helping keep djp-workflow and its users safe!
