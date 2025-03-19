# Testing Analysis Rules

## Directory Structure
```
testing/
├── api/              # API test analysis
│   ├── _rules.md    # API testing rules
│   ├── _coverage.md # API test coverage
│   └── routes/      # Per-route test analysis
├── database/        # Database test analysis
│   ├── _rules.md    # Database testing rules
│   └── _perf.md     # Performance test metrics
├── frontend/        # Frontend test analysis
│   ├── _rules.md    # Frontend testing rules
│   └── components/  # Component test analysis
└── e2e/            # End-to-end test analysis
    ├── _rules.md    # E2E testing rules
    └── _flows.md    # User flow coverage
```

## Required Files

### API Testing
- `_coverage.md`: Test coverage metrics per endpoint
- `_progress.md`: Test implementation status
- One analysis file per route group under routes/

### Database Testing
- `_coverage.md`: Model test coverage
- `_perf.md`: Query performance test results
- `_migrations.md`: Migration test coverage

### Frontend Testing
- `_coverage.md`: Component test coverage
- `_integration.md`: Integration test status
- Component-specific test analysis files

### E2E Testing
- `_coverage.md`: Flow coverage metrics
- `_scenarios.md`: Test scenario documentation
- `_performance.md`: E2E performance metrics

## Update Requirements

### Daily Updates
- Test execution results
- Coverage metrics
- Failed test analysis

### Weekly Updates
- Performance test results
- Integration test status
- E2E test scenarios

### Monthly Updates
- Test strategy review
- Coverage goals assessment
- Performance baseline review

## Metrics to Track

### Coverage Metrics
- Unit test coverage
- Integration test coverage
- E2E test coverage
- Branch coverage
- Statement coverage

### Performance Metrics
- Test execution time
- Query performance
- API response times
- Frontend render times
- E2E scenario duration

### Quality Metrics
- Test reliability
- Flaky test rate
- Test maintenance cost
- Bug detection rate
- Coverage trends

## Analysis Requirements

### API Test Analysis
- Must track rate limit test coverage
- Must verify error handling
- Must include auth scenarios
- Must test edge cases

### Database Test Analysis
- Must cover all models
- Must test relationships
- Must verify constraints
- Must test migrations

### Frontend Test Analysis
- Must cover all components
- Must test user interactions
- Must verify state updates
- Must test error handling

### E2E Test Analysis
- Must cover critical flows
- Must test error scenarios
- Must verify integrations
- Must include performance tests

## Review Process
1. Daily test execution review
2. Weekly coverage review
3. Monthly performance review
4. Quarterly test strategy review

## Documentation Links
- [Test Strategy Document]
- [Coverage Reports]
- [Performance Baselines]
- [Test Guidelines] 