# External Asset Status and TODO

This document tracks the status of multimodal assets required for benchmark tasks.

## Current Assets Status

### ✅ Already Provided

The following assets are already included in the repository:

| Asset Type | Location | Quantity | Description |
|-----------|----------|----------|-------------|
| **Conflicts** | `assets/conflicts/` | 5 groups | Conflict evidence files for source conflict resolution |
| **Email/Calendar** | `assets/email_calendar/` | 25 emails, 4 ICS | Email threads and calendar files for version/update tasks |
| **Images** | `assets/images/` | ~20 images | Mixed fashion, food package, and document scans |
| **PDFs** | `assets/pdfs/` | 24 files | Clean papers, noisy scans, table-heavy documents |
| **Videos** | `assets/videos/` | 6 videos | 8-15 min videos with JSON timestamp markers |
| **Logs** | `assets/logs/` | 10 files | Failure logs with repeated error signatures |
| **Screenshots** | `assets/screenshots/` | 8 images | Browser snapshots and UI screenshots |
| **Tables** | `assets/tables/` | 5 files | CSV and SQLite database snapshots |

### ⚠️ Can Be Supplemented

The following assets are functional but could benefit from expansion:

| Asset Type | Current | Recommended | Priority |
|-----------|---------|-------------|----------|
| Conflicts | 5 groups | 8-10 groups | Medium |
| Email/Calendar | 25 emails | 40+ emails | Medium |
| Images | ~20 | 40+ | **High** |
| Videos | 6 | 8-10 | Medium |
| Screenshots | 8 | 10+ | Low |
| Tables | 5 | 8-10 | Low |

## Detailed Asset Guide

### 1. Images Pack (`assets/images/`)

**Current Status**: ~20 images provided (mostly in `fashion/` subdirectory)

**What to Add**:
- More **food_package** category images (currently mostly in fashion folder)
- More **document_scan** category images
- Various sizes and orientations
- 5-10 intentionally mislabeled files for conflict/staleness tests

**Naming Convention**:
```
assets/images/
├── fashion/fashion_{001..020}.png       # Current
├── food_package/food_{001..020}.png     # Needs supplement
└── document_scan/scan_{001..020}.png    # Needs supplement
```

**Used In**: Recent Constraint Tracking, Procedure Transfer, Staleness/Applicability Judgment

### 2. Videos Pack (`assets/videos/`)

**Current Status**: 6 videos provided with JSON timestamp markers

**What to Add**:
- 2-4 additional videos for diversity
- Different domains (lectures, product launches, tutorials)
- One video with codec issue sample for interruption tasks

**Naming Convention**:
```
assets/videos/
├── {task_name}_{01..06}.mp4      # Current
├── {task_name}_{01..06}.json     # Timestamp markers
├── lecture_{07..10}.mp4          # New additions
└── lecture_{07..10}.json         # Corresponding markers
```

**JSON Marker Format**:
```json
{
  "duration_seconds": 540,
  "markers": [
    {"time": 60, "label": "key_point_1"},
    {"time": 180, "label": "key_point_2"}
  ]
}
```

**Used In**: Recent Constraint Tracking, Procedure Transfer, Goal Interruption/Resumption

### 3. PDF Bundle (`assets/pdfs/`)

**Current Status**: 24 PDFs provided (sufficient)

**Composition**:
- 8 clean academic papers
- 8 noisy scanned documents
- 8 table-heavy documents

**Naming Convention**:
```
assets/pdfs/
├── clean_paper_{01..08}.pdf
├── noisy_scan_{01..08}.pdf
└── table_doc_{01..08}.pdf
```

**Used In**: Recent Constraint Tracking, Memory Operation Selection, Goal Interruption/Resumption

### 4. Email and Calendar (`assets/email_calendar/`)

**Current Status**: 25 emails, 4 ICS files provided

**What to Add**:
- 15+ more email messages
- Cross-timezone meeting scenarios
- Recurring schedule conflict cases
- Source timestamps for arbitration

**Naming Convention**:
```
assets/email_calendar/
├── mailbox/
│   ├── thread_{01..10}/
│   │   └── message_{001..00N}.eml
├── calendars/
│   ├── personal_{01..04}.ics
│   └── work_{01..04}.ics
└── metadata.csv  # Extraction keys per file
```

**Used In**: Version Update, Source Conflict Resolution, Goal Interruption/Resumption

### 5. Conflict Evidence (`assets/conflicts/`)

**Current Status**: 5 conflict groups provided

**What to Add**:
- 3-5 more conflict pairs
- README vs logs conflicts
- Policy v1 vs policy v2 conflicts
- Config vs runtime output conflicts

**Naming Convention**:
```
assets/conflicts/
├── conflict_{01..05}/           # Current
│   ├── source_a.md
│   ├── source_b.md
│   └── metadata.yaml
└── conflict_{06..10}/           # New additions
```

**Metadata Format**:
```yaml
# metadata.yaml
type: "policy_conflict"
confidence_hint: "source_a_is_newer"
arbitration_rule: "timestamp_wins"
```

**Used In**: Source Conflict Resolution, Staleness/Applicability Judgment

### 6. Runtime Logs (`assets/logs/`)

**Current Status**: 10 failure logs provided (sufficient)

**Composition**:
- CUDA mismatch errors
- Pagination miss warnings
- Overwrite warnings
- Corrected run logs for anti-memory verification

**Naming Convention**:
```
assets/logs/
├── error_cuda_mismatch_{01..03}.log
├── error_pagination_{01..03}.log
├── error_overwrite_{01..03}.log
└── corrected_run_{01..03}.log
```

**Used In**: Repeated Mistake Prevention

## Capability-to-Asset Mapping

| Capability | Required Assets |
|-----------|-----------------|
| **01_Recent_Constraint_Tracking** | images, videos, pdfs |
| **02_Version_Update** | email_calendar, logs, conflicts |
| **03_Procedure_Transfer** | images, videos, web snapshots |
| **04_Repeated_Mistake_Prevention** | logs, shell transcripts |
| **05_Source_Conflict_Resolution** | conflicts, screenshots, email_calendar |
| **06_Memory_Operation_Selection** | mixed pack (small subset each) |
| **07_Goal_Interruption_Resumption** | videos, email_calendar, multi-file workspaces |
| **08_Staleness_Applicability_Judgment** | versioned docs, conflicts |

## Quick Verification

Check current assets status:

```bash
# Count assets in each category
echo "Images:"
find assets/images/ -type f \( -name "*.png" -o -name "*.jpg" \) | wc -l

echo "PDFs:"
ls assets/pdfs/*.pdf 2>/dev/null | wc -l

echo "Videos:"
ls assets/videos/*.mp4 2>/dev/null | wc -l

echo "Logs:"
ls assets/logs/*.log 2>/dev/null | wc -l

echo "Emails:"
find assets/email_calendar/ -name "*.eml" 2>/dev/null | wc -l

echo "Screenshots:"
ls assets/screenshots/*.png 2>/dev/null | wc -l
```

## Integration Checklist

When adding new assets:

- [ ] Place files in correct subdirectory under `assets/`
- [ ] Follow naming convention (see above)
- [ ] Add metadata files where applicable (JSON/YAML sidecars)
- [ ] Update workspace task folder under `episodes/` if needed
- [ ] Do not expose grading ground truth in asset files
- [ ] Keep checks deterministic by pinning file names

## Summary

- **Fully Ready**: PDFs (24), Logs (10)
- **Available, Can Supplement**: Conflicts (5→8), Email (25→40), Videos (6→8), Screenshots (8→10), Tables (5→8)
- **Needs Most Attention**: Images (~20→40, need more food_package and document_scan)

The benchmark is **fully functional** with current assets. Supplementation is optional for increased diversity.
