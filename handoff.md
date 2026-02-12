> welcome to life, you are a data engineer mentor. write inthis repo your 
commands and guidelines that will help you trought your ork in .md files, 
user the repo structure that better suits you                   
     # Data Engineering Mentor
     A comprehensive reference guide for data engineering 
  - commands,
     patterns, and best practices.
     ## Repository Structure
     ```
     docs/
     ├── sql/              # SQL commands, patterns, and optimization
     ├── python/           # Python & PySpark for data engineering
     
### SQL Guide (Complete)
Located at `docs/sql/README.md`, includes:
- Deduplication patterns
- Incremental load patterns
- SCD Type 2 slowly changing dimensions
- Window functions (running totals, LAG/LEAD, percentiles)
- Performance optimization (indexing, partitioning)
- Data quality queries (null analysis, duplicates, 
eferential integrity)
- Schema management and migration patterns

✢ Creating SQL guide… (esc to interrupt · ctrl+t to hide 
odos)
  ⎿  ☒ Create repository structure with directories
     ☒ Write main README with overview
     ☐ Create SQL commands and best practices guide
     ☐ Create Python/PySpark data engineering guide
     ☐ Create data quality patterns guide
     ☐ Create ETL/ELT pipeline patterns guide
     ☐ Create CLI tools and commands reference
---

## Agent Setup Research (Complete)

### Recommended Approach: Claude Code Skill

\
Create a skill at 
.claude/skills/data-engineering-mentor/SKILL.md`:

```yaml
---
name: data-engineering-mentor
description: Data engineering expert providing guidance on 
ata pipelines, quality checks, ETL design, and 
rchitecture. Use for design reviews, mentorship, and best 
ractice questions.
argument-hint: [topic] or [code-to-review]
---

You are an experienced data engineering mentor with deep 
xpertise in:

1. **Data Pipelines & ETL** - Architecture, orchestration 
Airflow, dbt), quality
2. **Data Quality** - Validation design, anomaly detection,
governance
3. **Database Design** - Schema design, partitioning, 
ptimization
4. **Tools** - SQL, Python (pandas, PySpark, Polars), 
odern data stack

## Mentoring Approach
- Start with fundamentals before implementation
- Provide concrete, runnable examples
- Discuss tradeoffs and context
- Review code for data patterns and optimization

## Reference Documentation
Consult these project docs for patterns:
- SQL patterns: docs/sql/README.md
- Python patterns: docs/python/README.md
- Pipeline patterns: docs/pipelines/README.md
- Data quality: docs/data-quality/README.md
- CLI reference: docs/cli/README.md
- Architecture: docs/architecture/README.md
```

### Alternative: Subagent (For Advanced Use)

Create at `.claude/agents/data-engineering-mentor.md` if 
ou need:
- Task isolation (doesn't clutter main conversation)
- Persistent memory across sessions (`memory: user`)
- Restricted tool access
- Different model (opus for capability, haiku for speed)

### Directory Structure for Agent

```
.claude/
├── skills/
│   └── data-engineering-mentor/
│       ├── SKILL.md              # Main agent instructions
│       ├── docs/                 # Supporting 
ocumentation
│       │   ├── data-quality-patterns.md
│       │   └── etl-best-practices.md
│       └── examples/             # Code examples
│           ├── validation.sql
│           └── quality-checks.py
└── agents/                       # Alternative: subagent 
pproach
    └── data-engineering-mentor.md
```

---

## Remaining Documentation Sections

### 1. Python/PySpark Guide (`docs/python/README.md`)
Content to include:
- Core data processing patterns (pandas, Polars, PySpark)
- File I/O patterns (parquet, JSON, CSV)
- Data validation and transformation patterns
- Performance optimization (vectorization, partitioning)
- Common utilities and helper functions
- Type hints best practices

### 2. Pipeline Patterns (`docs/pipelines/README.md`)
Content to include:
- Airflow DAG patterns and best practices
- dbt patterns (models, tests, macros)
- Error handling and retry strategies
- Idempotency patterns
- Incremental processing patterns
- Pipeline testing strategies

### 3. Data Quality Guide (`docs/data-quality/README.md`)
Content to include:
- Great Expectations patterns and setup
- dbt testing patterns
- Validation strategies (schema, business logic, freshness)
- Data quality metrics and monitoring
- Anomaly detection approaches
- Quality reporting patterns

### 4. CLI Tools Reference (`docs/cli/README.md`)
Content to include:
- Database CLIs (psql, mysql, bq, snowsql)
- Cloud CLIs (aws, gcloud, az) for data ops
- Data file tools (jq, csvkit, parquet-tools)
- dbt CLI reference
- Docker commands for data infrastructure
- Shell scripting patterns for data ops

### 5. Architecture Patterns 
`docs/architecture/README.md`)
Content to include:
- Data modeling (star schema, snowflake, data vault)
- Data lake/lakehouse (Delta Lake, Iceberg)
- Stream vs batch processing
- Data warehouse design patterns
- Data mesh concepts
- CDC patterns
- Schema evolution strategies

---

## Next Steps

1. **Create agent structure**: `mkdir -p 
claude/skills/data-engineering-mentor/{docs,examples}`
2. **Write SKILL.md**: Use template above
3. **Fill remaining docs**: Complete the 5 empty sections
4. **Test agent**: `/data-engineering-mentor How should I 
esign quality checks?`
5. **Iterate**: Refine based on usage

---

## Core Principles (From README.md)

1. **Data Quality First** - Validate early, validate often
2. **Idempotency** - Operations should be safely repeatable
3. **Observability** - Log, monitor, alert on everything
4. **Schema Evolution** - Plan for change from day one
5. **Documentation** - If it's not documented, it doesn't 
      + exist
