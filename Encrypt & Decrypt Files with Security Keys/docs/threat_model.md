# Threat model and requirements

Overview

This document provides a concise threat model and a set of functional and non-functional requirements for the `01-EncDecript_File_with_SecurityKeys` project.

Assets
- Confidential file contents (data at rest).
- Data encryption keys (DEKs) — generated per-file or per-session.
- Key-encryption keys (KEKs) — hardware-backed private keys on a security token.
- Wrapped keys and metadata stored on disk.

Actors
- Authorized user with access to laptop and hardware token.
- Adversary with one or more of: physical access to laptop, remote OS compromise, theft of hardware token.

Assumptions
- The hardware security key implements operations that keep private key material non-exportable.
- Host OS may be untrusted in some scenarios; we mitigate but cannot fully prevent OS-level compromise.

Threats
- Theft or loss of laptop containing encrypted files.
- Compromise of host OS leading to exfiltration of wrapped keys or plaintext.
- Theft of hardware token (attacker could use token if they also know user passphrase/credentials).

Security Goals
- Ensure files are encrypted with authenticated encryption (AEAD).
- Limit exposure of plaintext keys: keep in memory for minimal time, zero memory where practical.
- Use hardware-backed KEKs to wrap DEKs so an attacker without the token cannot recover DEKs.
- Secure on-disk storage of wrapped keys and metadata with strict file permissions.

Functional Requirements
- CLI to encrypt and decrypt files locally.
- Software-only mode for development/testing (no hardware key required).
- Hardware key adapter interface to wrap/unwrap data keys.
- Keystore for wrapped keys and metadata with import/export capabilities.

Non-Functional Requirements
- Work on Python 3.11+.
- Small dependency set; clear tests and documentation.
- Clear separation between core crypto logic and hardware adapter.

Mitigations
- Use AES-GCM or ChaCha20-Poly1305 for file encryption.
- Use per-file DEKs and wrap with KEK stored on a hardware token.
- Protect keystore with file permissions and optional passphrase.
- Provide user guidance in README for secure usage (e.g., removing tokens when not in use).

