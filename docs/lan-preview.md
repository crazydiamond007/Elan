# Android preview on the local network

This temporary review configuration uses Gunicorn with `DEBUG=False`, hashed/compressed WhiteNoise
static files and the existing validated WebP media route. It uses the local PostgreSQL database and
requires an explicit private IPv4 host; wildcard hosts are not accepted. The LAN URL has no Admin
routes. Keep Admin on the existing loopback development server.

This is HTTP on a trusted LAN, not public production hosting. No router forwarding or public tunnel
is configured. Test the fictional shopping flow without entering credentials or real customer data.
Android measurements on this setup reflect your workstation and Wi-Fi connection; they are not
public-host performance benchmarks. HTTP also lacks the secure context required by some browser APIs.

Build the current assets, then start the review server from WSL, substituting your Windows Wi-Fi IP:

```bash
npm run css:build
uv run --locked python scripts/build_static.py
LAN_PREVIEW_HOST=192.168.3.30 LAN_PREVIEW_PORT=8001 \
  uv run --locked --env-file .env gunicorn \
  --env DJANGO_SETTINGS_MODULE=config.settings.lan \
  --bind 0.0.0.0:8001 --config deploy/gunicorn.conf.py config.wsgi:application
```

The IP above is the address discovered for this session, not a permanent project default. Verify it
after changing networks. The Windows localhost relay must be enabled and able to reach the WSL app.

WSL2 NAT needs Windows forwarding for other devices. The reviewed
[`windows_lan_preview.ps1`](../scripts/windows_lan_preview.ps1) configures only the chosen Windows
address/port, forwarding through the verified Windows localhost relay, with an inbound firewall rule
restricted to that interface and its local subnet. This avoids opening the WSL Hyper-V VM firewall.
It preserves unrelated forwarding rules and refuses to replace an unowned rule on that endpoint.
`-Profile Any` accommodates a Wi-Fi network currently classified Public while keeping the explicit
interface/address/subnet limits; it does not change the Windows network classification.
Run it in an elevated Windows PowerShell session, substituting the current Wi-Fi address:

```powershell
& '\\wsl.localhost\Ubuntu-26.04\home\narcisse\projects\maison-elan\scripts\windows_lan_preview.ps1' `
  -LanAddress 192.168.3.30 -Port 8001
```

Windows administrator rights are needed for port forwarding and the firewall rule. Execution policy
may require explicitly allowing this reviewed script for the current process; no machine-wide policy
change is needed. See [Microsoft's WSL networking guide](https://learn.microsoft.com/en-us/windows/wsl/networking#accessing-a-wsl-2-distribution-from-your-local-area-network-lan).

Connect Android to the same Wi-Fi and open the printed `http://...:8001/` URL. Guest Wi-Fi/client
isolation or an Android VPN can block access between devices. Test menu/search, image previews, the
product gallery and simulated checkout. Cache the first visit, then repeat for a warm-load comparison.
Use Android Chrome's remote debugging if you need measured loading traces.

To remove this forwarding rule, run the same PowerShell command with `-Remove`. Stop Gunicorn with
Ctrl+C, or stop the optional user service with:

```bash
systemctl --user stop maison-elan-lan.service
```

The transient user service, when used, ends with the WSL instance; it is not a persistent public
deployment. Logs are available with `journalctl --user -u maison-elan-lan.service`.

## Executed setup and verification — 2026-10-18

- The storefront checkpoint was committed and pushed first as `f6ba9d6`.
- The preview service `maison-elan-lan.service` was started with two Gunicorn workers on port 8001.
  Windows forwards only `192.168.3.30:8001` to its working localhost WSL relay. The existing port-80
  forwarding entry was preserved. The new firewall rule was verified as TCP/8001, local address
  `192.168.3.30`, interface `WiFi`, remote scope `LocalSubnet`.
- Direct forwarding to the WSL virtual address timed out under the existing Hyper-V firewall.
  Using the verified localhost relay restored HTTP 200 without changing that VM firewall policy.
  The final address was checked from both Windows and WSL, bypassing HTTP proxy settings.
- **240 full-suite tests passed in 25.60s** before the storefront commit. **76 relevant tests passed
  in 4.13s** for the LAN settings, private-host validation, production settings and local Admin/pages.
  Django system checks, applied-migration verification, Ruff, formatting, PowerShell parsing,
  Tailwind and the production static build passed.
- The actual LAN URL passed shopping/checkout browser audits at five widths and navigation/search
  audits at sixteen viewport sizes, including keyboard, no-JavaScript and accessibility checks.
  A Pixel 7 touch-emulation journey completed product selection, bag and simulated checkout with
  CSRF protection enabled. Its search fits without scrolling. Hashed CSS was served compressed with
  immutable caching; `/admin/` returns 404 on LAN and untrusted Host values return 400.
- Chromium emits an expected notice that COOP is ignored on a non-secure HTTP LAN origin. QA now
  records that exact notice separately while continuing to fail on application, CSP and other
  console errors. App security headers were not removed to silence the notice. Initial browser runs
  stopped on that notice; the final recorded runs passed with it disclosed.

Reports/captures are in ignored `.qa/lan-preview/chromium/`; the additional Pixel 7 audit is temporary
tooling at `/tmp/maison-lan-android.mjs`. These are emulated-browser checks, not physical Android
performance measurements. Keep the PC and WSL instance running while testing from the phone.
