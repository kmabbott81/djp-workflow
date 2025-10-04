# Support

This document outlines support policies and resources for the DJP Workflow project.

## Support Policy

###Version Support

- **Current minor version** (1.0.x): Full support for bugs, security issues, and feature requests
- **Previous minor version** (0.34.x): Security patches only for 90 days after new minor release
- **Older versions**: No active support; users encouraged to upgrade

### Support Windows

| Version | Release Date | Support Ends | Security Patches Until |
|---------|--------------|--------------|------------------------|
| 1.0.x   | 2025-10-04   | Active       | TBD                    |
| 0.34.x  | 2025-10-03   | 2026-01-04   | 2026-01-04             |

## Getting Help

### Documentation

Start with our comprehensive documentation:

1. **[README.md](README.md)** - Project overview and quick start
2. **[DEVELOPMENT.md](DEVELOPMENT.md)** - Local development setup
3. **[docs/INSTALL.md](docs/INSTALL.md)** - Installation guide
4. **[docs/OPERATIONS.md](docs/OPERATIONS.md)** - Operations runbook
5. **[docs/SECURITY.md](docs/SECURITY.md)** - Security policies
6. **[CONTRIBUTING.md](CONTRIBUTING.md)** - Contribution guidelines

### Common Issues

Check our [Common Issues section](DEVELOPMENT.md#common-issues) in DEVELOPMENT.md for solutions to frequent problems.

### GitHub Issues

For bugs, feature requests, or technical questions:

1. **Search existing issues** to avoid duplicates
2. **Use issue templates** when creating new issues
3. **Provide complete information**:
   - DJP Workflow version
   - Python version
   - Operating system
   - Steps to reproduce
   - Expected vs actual behavior
   - Relevant logs/error messages

**Create an issue**: https://github.com/kmabbott81/djp-workflow/issues/new

### GitHub Discussions

For general questions, ideas, or community discussion:

- **Q&A**: Ask questions and get help from the community
- **Ideas**: Propose and discuss new features
- **Show and Tell**: Share your workflows and use cases

**Start a discussion**: https://github.com/kmabbott81/djp-workflow/discussions

## Security Issues

**Do not open public issues for security vulnerabilities.**

See [SECURITY.md](docs/SECURITY.md) for our security policy and responsible disclosure process.

Send security reports to: [security contact as configured in SECURITY.md]

## Feature Requests

We welcome feature requests! Please:

1. Check existing issues/discussions for similar requests
2. Describe the use case and expected behavior
3. Explain why this would be valuable to others
4. Consider contributing an implementation (see [CONTRIBUTING.md](CONTRIBUTING.md))

## Contributing

We appreciate contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on:

- Setting up development environment
- Branching strategy
- Commit conventions
- Testing requirements
- Pull request process

## Commercial Support

For enterprise users requiring:
- Priority support
- Custom feature development
- Training and consultation
- SLA-backed support contracts

Contact: [commercial contact - TBD if applicable]

## Community Resources

- **GitHub Repository**: https://github.com/kmabbott81/djp-workflow
- **Issue Tracker**: https://github.com/kmabbott81/djp-workflow/issues
- **Discussions**: https://github.com/kmabbott81/djp-workflow/discussions
- **Changelog**: [CHANGELOG.md](CHANGELOG.md)
- **Release Notes**: See GitHub Releases

## Response Times

### Community Support (GitHub Issues/Discussions)

- **Bug reports**: Best-effort response within 7 days
- **Feature requests**: Best-effort review within 14 days
- **Security issues**: See [SECURITY.md](docs/SECURITY.md) for specific timelines

_Note: Response times are not guaranteed for community support. For SLA-backed support, contact us about commercial support options._

## Upgrade Assistance

See [docs/UPGRADE.md](docs/UPGRADE.md) for version-specific upgrade guides.

For complex upgrade scenarios, consider:
1. Testing upgrades in a staging environment first
2. Reviewing the [CHANGELOG.md](CHANGELOG.md) for breaking changes
3. Running the config validator: `python -m src.config.validate`
4. Opening a discussion if you encounter issues

## Feedback

We value your feedback! Help us improve:

- Report bugs via GitHub Issues
- Suggest features via GitHub Discussions
- Share your experience in Show and Tell
- Contribute improvements via Pull Requests

---

**Thank you for using DJP Workflow!** 🙏
