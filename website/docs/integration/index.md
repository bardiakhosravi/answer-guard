---
sidebar_position: 1
---

# Integration Guide

This guide walks you through connecting AnswerGuard to your existing agent system. There are two tasks:

1. **Historical import** — pull your existing Q&A history from BigQuery into AnswerGuard so your PM can start reviewing from day one.
2. **Runtime capture** — add the AnswerGuard SDK to your agent pipeline so new responses are automatically captured as they happen.

## Prerequisites

- A running AnswerGuard instance (follow the [Quickstart](/docs/quickstart) first)
- An existing agent system you can modify to add SDK calls
- A BigQuery dataset containing your historical Q&A data

## Recommended order

1. [Configure your BigQuery source →](/docs/integration/bigquery)
2. [Run the historical import →](/docs/integration/historical-import)
3. Add runtime capture: [Python SDK →](/docs/integration/python-sdk) or [TypeScript SDK →](/docs/integration/typescript-sdk)
4. [Verify the integration →](/docs/integration/verification)
