# Backend Analysis Rules

## Directory Structure
```
backend/
├── api/              # API endpoint analysis
│   ├── _rules.md    # API-specific rules
│   ├── _metrics.md  # API performance metrics
│   └── routes/      # Per-route analysis
├── core/            # Core business logic analysis
│   ├── _rules.md    # Core logic rules
│   └── services/    # Service-specific analysis
├── database/        # Database analysis
│   ├── _rules.md    # Database rules
│   ├── _schema.md   # Schema evolution tracking
│   └── _perf.md     # Performance metrics
└── error_handling/  # Error handling analysis
    ├── _rules.md    # Error handling rules
    └── _coverage.md # Error handling coverage
```

## Required Files

### API Directory
- `_metrics.md`: Response times, error rates, usage patterns
- `_progress.md`: Implementation status of API endpoints
- One analysis file per route group under routes/

### Core Directory
- `_coverage.md`: Test coverage metrics
- `_progress.md`: Implementation status
- Service-specific analysis files under services/

### Database Directory
- `_schema.md`: Schema version tracking
- `_perf.md`: Query performance metrics
- `_migrations.md`: Migration history

### Error Handling Directory
- `_coverage.md`: Error handling test coverage
- `_patterns.md`: Error handling patterns in use
- `_metrics.md`: Error occurrence rates

## Update Requirements

### Daily Updates
- API metrics
- Error rates
- Implementation progress

### Weekly Updates
- Test coverage
- Performance metrics
- Schema evolution

### Monthly Updates
- Architecture analysis
- Technical debt assessment
- Security review

## Metrics to Track

### API Metrics
- Response times (avg, p95, p99)
- Error rates per endpoint
- Usage patterns
- Rate limiting statistics

### Database Metrics
- Query performance
- Index usage
- Connection pool status
- Migration success rates

### Error Handling Metrics
- Error occurrence rates
- Recovery success rates
- Average resolution time
- Pattern effectiveness

## Analysis Requirements

### API Analysis
- Must include rate limiting considerations
- Must document authentication requirements
- Must track breaking changes

### Database Analysis
- Must include migration impacts
- Must track query optimization
- Must document schema changes

### Error Handling Analysis
- Must categorize error types
- Must track recovery mechanisms
- Must document error patterns

## Review Process
1. Daily review of metrics
2. Weekly review of progress
3. Monthly review of architecture
4. Quarterly review of patterns

## Documentation Links
- [Backend Architecture Document]
- [API Documentation]
- [Database Schema]
- [Error Handling Guide] 