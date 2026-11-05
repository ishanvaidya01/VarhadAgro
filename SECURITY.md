# Security Policy

## Supported Versions

| Version | Supported |
| --- | --- |
| `main` (latest commit) | Yes |
| Older commits / tags | No |

VarhadAgro is maintained on a best-effort basis. Security fixes are applied to the latest `main` branch.

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Use one of the following private channels:

1. **GitHub Security Advisories** — open a private report from the repository's *Security* tab.
2. **Email** — [ishan.vaidya01@gmail.com](mailto:ishan.vaidya01@gmail.com) with the subject `[VarhadAgro Security]`.

Please include a description, reproduction steps or proof of concept, and the affected component (Flask app, model code, Docker setup).

## Scope

In scope:

- Input-validation flaws that allow unsafe payloads to reach the model or template rendering.
- Injection and unsafe handling of untrusted data files (CSV) in the pipeline.
- Exposure of secrets through the application or repository.

Out of scope:

- Model accuracy or data quality (report via a normal issue).
- Denial of service through extreme traffic.
- Issues in third-party dependencies that are already publicly known.

## Disclosure Policy

Once a fix is available, the maintainer will publish a patched version and credit the reporter unless anonymity is requested.
