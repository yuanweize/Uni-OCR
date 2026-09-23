# Security Policy

## Supported Versions

| Version | Supported          | Notes |
| ------- | ------------------ | ----- |
| 0.2.x   | :white_check_mark: | Current active release line |
| < 0.2   | :x:                | Deprecated |

## Security Architecture & Local Privacy

Uni-OCR is engineered for privacy-conscious, local-first document extraction:

1. **Air-Gapped & Offline Execution**: The OCR engine runs completely offline without transmitting scanned document data, images, or extracted text to third-party endpoints.
2. **Input Sanitization**: File uploads and image streams are strictly validated against supported image formats (PNG, JPEG, TIFF, WebP, PDF) to prevent memory corruption or decompression bomb attacks.
3. **Temporary File Isolation**: Ephemeral processing buffers are isolated in dedicated temporary directories and securely unlinked immediately after recognition.

## Reporting a Vulnerability

If you discover a security vulnerability or potential exploit in Uni-OCR:

1. **Do NOT open a public issue.**
2. Report the vulnerability privately via [GitHub Security Advisories](https://github.com/yuanweize/Uni-OCR/security/advisories/new) or contact `yuanweize@users.noreply.github.com`.
3. Provide reproduction steps, sample image/payload files if relevant, and the Uni-OCR version.
4. We will acknowledge receipt within 48 hours and work on a coordinated fix.
