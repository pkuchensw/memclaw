Use this skill for bash/python/file operations in workspace.

Rules:
1. Never destructively overwrite originals without backup/temp path.
2. Validate command outputs before writing final artifacts.
3. Keep execution deterministic and idempotent.
4. Record failure signatures and checks performed.
