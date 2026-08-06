"""Shared constants for the V-IMS AI demo.

DEMO_ANALYSIS_DATE is fixed at 2026-08-05 so that days-to-expiry calculations,
risk scores and FEFO rankings are reproducible regardless of when the
application is run.  Do NOT replace this with date.today().
"""
from datetime import date

DEMO_ANALYSIS_DATE: date = date(2026, 8, 5)
