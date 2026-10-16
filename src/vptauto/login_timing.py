"""Shared deadlines for login workers and their supervisor (seconds)."""

WINDOW_TIMEOUT = 25
STAGE_TIMEOUT = 45
# Forced login can wait for the server to disconnect an existing session.
FORCE_LOGIN_TIMEOUT = 180
FLOW_TIMEOUT = FORCE_LOGIN_TIMEOUT + 4 * STAGE_TIMEOUT
JOB_TIMEOUT = WINDOW_TIMEOUT + FLOW_TIMEOUT + 5
