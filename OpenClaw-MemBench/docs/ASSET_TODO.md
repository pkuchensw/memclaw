# External Asset TODO (Manual Collection)

This file tracks assets that are intentionally not committed yet and should be added manually.

## Required for full benchmark realism

1. Long videos for clip extraction tasks (10-20 min each)
2. PDF bundles for paper extraction tasks
3. Calendar/email mock exports for scheduling tasks
4. Mixed-quality CSV and DB snapshots for conflict resolution tasks
5. Runtime logs containing version conflicts and failure signatures
6. Browser snapshots/screenshots for evidence arbitration tasks
7. Optional UI screenshots for computer-use style tasks

## Suggested location layout

- assets/videos/
- assets/pdfs/
- assets/email_calendar/
- assets/tables/
- assets/logs/
- assets/screenshots/

## Integration checklist

- Place asset metadata in each workspace task folder under episodes/.
- Do not expose grading ground truth before run.
- Keep checks deterministic by pinning file names and hashes.
