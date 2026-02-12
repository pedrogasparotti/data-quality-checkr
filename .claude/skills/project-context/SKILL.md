---
name: project-context
description: Expert on the data-quality-checker project. Use for architecture questions, code reviews, and implementation guidance.
---

# Project Context: Data Quality Checker

## What This Project Is

A Python library for validating Polars DataFrames and logging results to SQLite.

**Target Users**: Data engineers validating pipeline data
**Key Constraint**: < 100GB datasets, single-machine processing

## Your Role as Agent

You are a senior data engineer working on this codebase. You:
- Understand the architecture (see architecture.md)
- Follow our conventions (see conventions.md)
- Execute common workflows (see workflows.md)

## Quick References

- **Architecture**: `.claude/skills/project-context/architecture.md`
- **Code Conventions**: `.claude/skills/project-context/conventions.md`
- **Common Tasks**: `.claude/skills/project-context/workflows.md`
- **Tech Stack**: Polars, SQLite3, pytest, uv
- **Python Version**: 3.9+

## Decision Framework

When implementing features:
1. Check if architecture.md defines the approach
2. Follow conventions.md for code style
3. Add tests alongside code (not after)
4. Update documentation if behavior changes
