# Wi-Fi and Network Connectivity Issues

## Symptoms

Common symptoms include:

- Unable to connect to a Wi-Fi network
- Connected to Wi-Fi but no internet access
- Wi-Fi adapter missing or disabled
- Frequent connection drops
- VPN fails to establish a tunnel

## Initial Troubleshooting

1. Check whether Airplane Mode is disabled.
2. Verify that Wi-Fi is enabled in the OS network settings.
3. Restart the Wi-Fi adapter (disable/enable in Device Manager).
4. Forget the Wi-Fi network and reconnect with the password.
5. Restart the router if multiple devices are affected.

## Windows Diagnostics

Open Command Prompt as Administrator and run:

```text
ipconfig /all
ipconfig /release
ipconfig /renew
ipconfig /flushdns
```

If DNS resolution fails but the IP address is valid, try a public DNS
resolver (1.1.1.1 or 8.8.8.8) to isolate ISP DNS problems.

## VPN-Specific Checks

1. Confirm the VPN client is up to date.
2. Check whether split tunnelling is misconfigured.
3. Verify the VPN gateway/server is reachable (`ping` or `tracert`).
4. Re-authenticate if the token/certificate has expired.

## When to Escalate

Escalate to network engineering if the router restart does not resolve the
issue, if multiple users on the same subnet are affected, or if `tracert`
shows packet loss beyond the local gateway.
