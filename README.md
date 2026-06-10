# market-data-clean

A small data-cleaning layer for market data used by research and backtesting.

## Goal

Turn raw market data into a normalized, validated, audit-friendly dataset that downstream research code can trust.

## Scope

- ingest raw files
- normalize schema and timestamps
- validate rows
- split accepted / rejected records
- emit a cleaning report

## MVP

1. Define the data contract
2. Implement validation rules
3. Add a simple CLI
4. Write a sample cleaning pipeline

## Repo layout

- `docs/` — contracts and assumptions
- `src/` — package code
- `tests/` — unit tests

## Status

This repo is intentionally small at first. The contract comes before feature growth.
