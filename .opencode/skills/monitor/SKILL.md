# Monitor Skill

Provides slash‑command logging and reporting for the project.

## Commands

- `/monitor:log` – Append an operation entry to the log.
- `/monitor:record` – Log operation and generate a report if files changed.
- `/monitor:update` – Reconcile profile and regenerate dashboards.
- `/monitor:status` – Show open tasks, recent activity, pending items.
- `/monitor:task-start <name>` – Start a task.
- `/monitor:task-update <name>` – Update a task.
- `/monitor:task-close <name>` – Close a task.
- `/monitor:clean-logs` – Trim old log entries.
- `/monitor:clean-reports` – Trim old reports.
- `/monitor:clean-tasks` – Trim old tasks.
- `/monitor:search <query>` – Keyword search in the log.
- `/monitor:report` – Generate a report from the current log.

## Usage

Load the skill with:

```
/skill monitor
```

Then use any of the `/monitor:*` commands as described above.

## Notes

- The skill assumes the `monitor/` directory (with `scripts/`, `logs/`, `reports/`, `profile.json`) exists at the project root.
- No additional Python packages are required beyond the standard library.
