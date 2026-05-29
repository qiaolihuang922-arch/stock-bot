# Handoff: evidence_phase_4_market_theme_confirmed_evidence.sql

## Purpose

`db/sql/evidence_phase_4_market_theme_confirmed_evidence.sql` is a manual SQL artifact for creating or reviewing the `public.market_theme_confirmed_evidence` schema used by future read-only reconstruction of confirmed market/theme evidence.

## Copy And Execution Notes

Copy the entire SQL file into Supabase SQL editor and execute it as one block. Do not copy only the middle section; missing the final semicolon, closing delimiter, or tail statement can produce `ERROR 42601 syntax error at end of input`.

This artifact is not a backfill. Do not connect from agents to production for validation, do not run production backfill, and do not add grants, secrets, service-role credentials, or connection strings.

## Syntax Error Context

The likely causes of the reported end-of-input error are an incomplete pasted SQL block, a missing statement terminator, an unclosed dollar quote or `BEGIN ... END` block, or a missing closing parenthesis in the copied text. This patch keeps validation local/non-production and makes the file end with an explicit read-only validation marker statement.
