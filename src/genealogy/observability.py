"""Sentry observability wiring for genealogy.

Genealogy runs as a single-user local MCP server. Sentry is enabled when
GENEALOGY_SENTRY_DSN is set; otherwise init_sentry is a no-op and the
library has no telemetry side effects.

Per Platform Standard 06 (observability) and ADR-0014 (Lambda Sentry
observability) — adapted for a local Python stdio process.
"""

from __future__ import annotations

import os

import sentry_sdk


def init_sentry(*, environment: str | None = None, release: str | None = None) -> bool:
    """Initialize Sentry if GENEALOGY_SENTRY_DSN is set.

    Returns True if Sentry was initialized, False if skipped.

    Callers (e.g. an MCP server entry point) should invoke this once at startup
    before any work runs. Imports of `genealogy` as a library do NOT trigger
    Sentry — only explicit init_sentry() calls do, so library users are not
    surprised by outbound telemetry.

    Environment variables:
        GENEALOGY_SENTRY_DSN: Sentry DSN. If unset or empty, Sentry is skipped.
        GENEALOGY_ENV: Environment tag (defaults to "local"). Used unless the
            `environment` parameter is passed explicitly.
        GENEALOGY_RELEASE: Release version tag. Used unless the `release`
            parameter is passed explicitly.
    """
    dsn = os.environ.get("GENEALOGY_SENTRY_DSN", "").strip()
    if not dsn:
        return False

    sentry_sdk.init(
        dsn=dsn,
        environment=environment or os.environ.get("GENEALOGY_ENV", "local"),
        release=release or os.environ.get("GENEALOGY_RELEASE"),
        # Conservative defaults for a local single-user MCP server:
        # - send full stack traces, but not user PII
        # - no performance/profiling overhead unless the user opts in
        send_default_pii=False,
        traces_sample_rate=0.0,
        profiles_sample_rate=0.0,
        # Capture log records as breadcrumbs but don't auto-send error logs as
        # Sentry events (we want explicit captures only).
        attach_stacktrace=True,
    )
    return True
