# market-data-clean

A small data-cleaning layer for market data used by research and backtesting.

## Goal

Turn raw market data into a normalized, validated, audit-friendly dataset that downstream research code can trust.

> ⚠️ **Current focus: 加權指數期貨（台指期 TX / 小台 MTX）**  
> 商品如 `TXFR1`（近月）、`TXFR2`（遠月）、`TXFF6`（實際交割代碼）等。  
> 本階段暫不處理個股期貨、選擇權、股票等其他商品。

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
