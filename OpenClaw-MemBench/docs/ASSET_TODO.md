# External Asset TODO (Manual Collection)

This file tracks assets that are intentionally not committed yet and should be added manually.

## Priority Asset Pack (What you can build manually now)

1. Images pack for RCT/PT/SAJ
- 3 domains x 40 images each (fashion, food package, document scan)
- include mixed orientation and mixed aspect ratios
- include 10 intentionally mislabeled files for conflict/staleness tests
- target path: assets/images/<domain>/

2. Videos pack for RCT/PT/GIR
- 6 videos, each 8-15 minutes, 1080p mp4
- include timeline markers file per video: .json with key intervals
- include one video with codec issue sample for interruption tasks
- target path: assets/videos/

3. PDF bundle for RCT/MOS/GIR
- at least 24 PDFs with varied template/layout
- 8 clean papers, 8 noisy scans, 8 mixed table-heavy docs
- include a per-file metadata csv with expected extraction keys
- target path: assets/pdfs/

4. Email and calendar bundle for VU/SCR/GIR
- mailbox export with update threads (at least 20 messages)
- calendar ICS set with conflicting events and timezone variants
- include source timestamps to support arbitration
- target path: assets/email_calendar/

5. Conflict evidence bundle for SCR/SAJ
- pairs of conflicting files: README vs logs, policy_v1 vs policy_v2, config vs runtime output
- include confidence hints in sidecar yaml for grader white-box checks
- target path: assets/conflicts/

6. Runtime logs for RMP
- 10 failure logs with repeated error signatures (cuda mismatch, pagination miss, overwrite warning)
- include corrected run logs for anti-memory verification
- target path: assets/logs/

## Required for full benchmark realism

1. Long videos for clip extraction tasks (10-20 min each)
2. PDF bundles for paper extraction tasks
3. Calendar/email mock exports for scheduling tasks
4. Mixed-quality CSV and DB snapshots for conflict resolution tasks
5. Runtime logs containing version conflicts and failure signatures
6. Browser snapshots/screenshots for evidence arbitration tasks
7. Optional UI screenshots for computer-use style tasks

## Capability-to-Asset Mapping

1. 01_Recent_Constraint_Tracking
- required: images, videos, pdfs

2. 02_Version_Update
- required: email_calendar, logs, conflicts

3. 03_Procedure_Transfer
- required: images, videos, web snapshots

4. 04_Repeated_Mistake_Prevention
- required: logs, shell transcripts

5. 05_Source_Conflict_Resolution
- required: conflicts, screenshots, email_calendar

6. 06_Memory_Operation_Selection
- required: mixed pack from all above (small subset each)

7. 07_Goal_Interruption_Resumption
- required: videos, email_calendar, multi-file workspaces with checkpoints

8. 08_Staleness_Applicability_Judgment
- required: versioned docs/policies/config snapshots

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
