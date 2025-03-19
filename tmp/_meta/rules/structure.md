# Temporary Analysis Directory Structure Rules

## Directory Organization Rules

### 1. Directory Creation Rules
- New directories must mirror the actual codebase structure where possible
- Each major component (backend, frontend, testing) has its own root directory
- Subdirectories should be created when 3 or more related files exist
- Maximum directory depth: 4 levels

### 2. Required Files
- Every directory must contain a `_rules.md` file
- Every feature directory must contain a `_progress.md` file
- Every testable component must have a `_coverage.md` file
- Performance-critical components must have a `_metrics.md` file

### 3. File Naming Conventions
- Meta/configuration files start with `_` (e.g., `_rules.md`)
- Progress tracking files start with `progress_`
- Metric tracking files start with `metric_`
- Todo lists start with `todo_`
- Analysis files start with `analysis_`
- All files must be markdown format (.md)

### 4. Update Frequency
- Progress files: Update daily when active, weekly when stable
- Metrics files: Update after each significant change
- Coverage files: Update after each test run
- Analysis files: Update when new insights are gained

### 5. Automatic Subdivision Rules
Create new subdirectory when:
1. More than 5 related files exist in a directory
2. A new major feature is being developed
3. A component requires isolated tracking
4. Multiple team members are working on related components

### 6. File Structure Templates
Each file type must follow its template from tmp/_meta/templates/
- progress.md
- metrics.md
- coverage.md
- analysis.md
- rules.md

### 7. Linking Rules
- All progress files must link to relevant code files
- All metrics must reference their collection method
- All analysis must link to supporting evidence

### 8. Cleanup Rules
- Archive completed feature directories after 30 days
- Remove metrics older than 90 days
- Consolidate progress files monthly
- Remove empty directories immediately

### 9. Required Sections
Every progress file must include:
- Current status (🔴 BLOCKED | 🟡 IN PROGRESS | 🟢 COMPLETED)
- Completion percentage
- Last update timestamp
- Completed items
- In-progress items
- Blocked items
- Next steps

Every metrics file must include:
- Current values
- Historical trends
- Success criteria
- Alert thresholds
- Collection timestamp

### 10. Creation of New Subdivisions
When creating a new subdivision:
1. Create `_rules.md` first
2. Create required tracking files
3. Update parent directory's rules if needed
4. Add relevant templates
5. Document the purpose of the subdivision 