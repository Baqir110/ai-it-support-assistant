# System Crashes and Stability Issues

## Symptoms

- Blue Screen of Death (BSOD) with a stop code
- System randomly restarts or freezes
- System won't boot past the manufacturer logo
- Kernel panics (macOS/Linux)

## Initial Troubleshooting

1. Record the exact error/stop code shown on the crash screen.
2. Note any recent changes: new hardware, driver updates, Windows updates.
3. Restart the system and check Event Viewer / crash logs for details.
4. Boot into Safe Mode to determine if a third-party driver is the cause.

## Diagnostic Commands (Windows)

```text
sfc /scannow
DISM /Online /Cleanup-Image /RestoreHealth
```

Review `C:\Windows\Minidump` for crash dump files if deeper analysis is
needed.

## Common Root Causes

- Faulty or outdated device drivers (especially GPU/storage controllers)
- Failing RAM (run Windows Memory Diagnostic)
- Overheating due to dust buildup or failed cooling
- Corrupted system files

## When to Escalate

Escalate immediately - system instability risks data loss and can indicate
imminent hardware failure. Always escalate if a stop code repeats across
multiple reboots or if the system fails to boot at all.
