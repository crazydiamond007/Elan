# Mobile accessories and pagination correction — 2026-10-18

The owner's Android screenshots showed the portrait tote cropped into a shallow 2:1 banner and
an oversized pagination frame. This correction preserves the desktop layouts and existing assets.

- Below 768px, the Accessories image uses a square frame and `object-fit: contain`, showing the
  full bag, handles and plinth. Its responsive size hint reflects the contained portrait width.
- Mobile pagination now sizes to its content, with 12px vertical padding, a 10px corner radius,
  shorter section gaps and a 32px top margin. The label, numbers, directions and status remain.
  Every actionable page control retains a minimum 44px height. Longer page ranges still wrap.
- A browser check exposed an existing form-history reset clearing every `aria-disabled` attribute,
  including static pagination boundaries. `forms.js` now marks pending submitters and resets only
  those controls, preserving Previous/Next boundary semantics.

## Executed checks

- Focused checks at **1440, 768, 430, 393, 375 and 320px**, including mobile touch emulation, passed.
  At 393px, the bag frame is **353×353px**, and the pagination content box is **275×119px**.
  Full-image fitting, first/last page navigation, 44px controls and no horizontal overflow were checked.
  Scoped axe scans for the mobile tile and pagination reported zero A/AA violations.
- Existing catalog, product and collections browser audits passed at **1440/1024/768/390/320px**,
  including loaded images, unavailable variants and no-JavaScript selection behavior.
- Existing bag/checkout audits passed at those five widths through the live LAN URL, including
  the no-JavaScript shopping journey. A targeted history-restoration check verified that pending
  submitters reset while the static last-page disabled label survives.
- The 393px bag and pagination screenshots were visually reviewed. Tailwind, production hashed
  static collection, JavaScript syntax/formatting, Ruff and `git diff --check` passed.

Reports/captures are in ignored `.qa/mobile-refinement/chromium/`. Focused temporary browser tools
are `/tmp/maison-mobile-refinement.mjs` and `/tmp/maison-form-reset-check.mjs`. No dependency, database
migration or new image was needed. These checks do not substitute for physical Android testing.

During verification, the Windows Wi-Fi address changed from `192.168.3.30` to `10.109.25.174`.
The old endpoint consequently timed out while Gunicorn and the localhost relay remained healthy.
The owned forwarding/firewall rule was moved to the current Wi-Fi address and the service's explicit
host updated. The active preview for this review is **http://10.109.25.174:8001/**. The original
forwarding entry on port 80 remains untouched. As documented in the LAN guide, this address can change
when the PC changes networks. The phone must be connected to the same network as the PC.
