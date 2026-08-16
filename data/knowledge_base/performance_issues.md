# System Performance Issues

## Symptoms

- General slowness or lag when opening applications
- High CPU or memory usage at idle
- Fans running constantly at high speed
- Disk activity light constantly on

## Initial Troubleshooting

1. Check Task Manager (Ctrl+Shift+Esc) for processes with abnormal CPU/RAM.
2. Close unused browser tabs and background applications.
3. Check available disk space; performance degrades sharply below ~10% free.
4. Restart the system to clear leaked memory/handles.

## Diagnostic Commands (Windows)

```text
tasklist /v
wmic cpu get loadpercentage
wmic logicaldisk get size,freespace,caption
```

## Common Root Causes

- Startup app bloat (too many apps launching at boot)
- Malware or crypto-mining processes
- Failing disk (check SMART status)
- Insufficient RAM for current workload

## When to Escalate

Escalate if SMART status reports disk pre-failure, if malware is suspected,
or if the issue persists after a clean reboot and startup app cleanup.
