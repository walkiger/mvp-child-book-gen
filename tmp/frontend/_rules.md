# Frontend Analysis Rules

## Directory Structure
```
frontend/
├── components/       # Component analysis
│   ├── _rules.md    # Component-specific rules
│   ├── _metrics.md  # Component performance metrics
│   └── _reuse.md    # Component reusability analysis
├── state/           # State management analysis
│   ├── _rules.md    # State management rules
│   └── _flows.md    # State flow analysis
└── error_handling/  # Error handling analysis
    ├── _rules.md    # Error handling rules
    └── _coverage.md # Error handling coverage
```

## Required Files

### Components Directory
- `_metrics.md`: Performance metrics, render times
- `_reuse.md`: Component reuse statistics
- `_coverage.md`: Component test coverage
- One analysis file per major component

### State Directory
- `_flows.md`: State flow diagrams and analysis
- `_complexity.md`: State complexity metrics
- `_performance.md`: State updates performance

### Error Handling Directory
- `_coverage.md`: Error handling coverage
- `_patterns.md`: Error handling patterns
- `_feedback.md`: User error feedback analysis

## Update Requirements

### Daily Updates
- Component performance metrics
- Error handling statistics
- Implementation progress

### Weekly Updates
- Component test coverage
- State complexity metrics
- Reusability analysis

### Monthly Updates
- Architecture review
- Performance optimization
- Accessibility audit

## Metrics to Track

### Component Metrics
- Render times
- Bundle sizes
- Test coverage
- Reuse frequency
- Prop complexity

### State Metrics
- Update frequency
- State tree depth
- Selector performance
- Cache hit rates

### Error Handling Metrics
- Error occurrence rates
- Recovery success rates
- User feedback effectiveness
- Error boundary coverage

## Analysis Requirements

### Component Analysis
- Must include accessibility considerations
- Must document prop interfaces
- Must track breaking changes
- Must analyze render performance

### State Analysis
- Must document state shape
- Must track selector usage
- Must analyze update patterns
- Must document side effects

### Error Handling Analysis
- Must categorize error types
- Must document recovery flows
- Must track user feedback
- Must analyze boundary effectiveness

## Review Process
1. Daily component performance review
2. Weekly state management review
3. Monthly architecture review
4. Quarterly pattern review

## Documentation Links
- [Frontend Architecture Document]
- [Component Library]
- [State Management Guide]
- [Error Handling Documentation] 