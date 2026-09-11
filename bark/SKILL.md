---
name: bark
description: Send a push notification to the user's iOS device via Bark. Use this skill when the user asks to "send a bark", "push a notification", "notify my phone", or wants an iOS push alert (as opposed to Slack).
---

# Bark Skill

Send an iOS push notification via the Bark app's public API (`api.day.app`).

## Credentials

The device key and AES256 encryption key live in `~/.claude/.env`:
```
BARK_DEVICE_KEY=...
BARK_AES_KEY=...
```
Never hardcode these in scripts or in this skill file — always load them at runtime (Python: `python-dotenv` per the user's global convention; shell: read them from the file when needed, as shown below).

## Parameters

- `body` (required unless `markdown` is used): The notification content
- `title` (optional): The notification title. Defaults to no title if omitted.
- `sound` (optional): One of the built-in sounds (see list below). Defaults to the system default sound if omitted.
- `markdown` (optional): Markdown text. The Bark app parses it client-side (`NotificationServiceExtension/Processor/MarkdownProcessor.swift`) and replaces the notification body with the parsed plain text — headers/bold/lists/quotes etc. get stripped to readable plain text (iOS notifications can't render rich markdown formatting). Works with encrypted pushes too, since `ciphertext` is processed before `markdown` in the extension's pipeline.

## Default: Send Encrypted

**Every push should be sent encrypted by default** (see the "Encrypted Push" section below for the how-to) — the user confirmed on-device decryption works and wants this as the standard behavior, not an opt-in. Only send a plain, unencrypted push (title/body directly in the URL path) if the user explicitly asks for it unencrypted/plain.

## How to Send (plain, unencrypted — only when explicitly requested)

Use curl against `https://api.day.app/<key>/...`. Title and body must be URL-encoded (spaces, `!`, etc.). Load the key from `~/.claude/.env` rather than hardcoding it:

```bash
BARK_DEVICE_KEY=$(grep '^BARK_DEVICE_KEY=' ~/.claude/.env | cut -d= -f2)
```

With title and sound:
```bash
curl -s "https://api.day.app/${BARK_DEVICE_KEY}/<TITLE>/<BODY>?sound=<SOUND>"
```

With title only:
```bash
curl -s "https://api.day.app/${BARK_DEVICE_KEY}/<TITLE>/<BODY>"
```

Body only, no title:
```bash
curl -s "https://api.day.app/${BARK_DEVICE_KEY}/<BODY>"
```

A response of `{"code":200,"message":"success",...}` confirms delivery.

## Available Sounds

alarm, anticipate, bell, birdsong, bloom, calypso, chime, choo, descent, electronic, fanfare, glass, gotosleep, healthnotification, horn, ladder, mailsent, minuet, multiwayinvitation, newmail, newsflash, noir, paymentsuccess, shake, sherwoodforest, silence, spell, suspense, telegraph, tiptoes, typewriters, update

If the user requests a sound not in this list, point out the closest valid match rather than sending an invalid value.

## Notes

- Reserved URL characters in title/body (spaces, `!`, `&`, `?`, `#`, etc.) should be percent-encoded or the shell's quoting relied upon carefully — prefer `--data-urlencode` with a GET-style curl only if issues arise; for simple text, direct interpolation into the URL path has worked fine in practice.

## Encrypted Push (default)

Bark supports end-to-end encryption: the payload (title/body/sound/etc as JSON) is AES-encrypted client-side and sent as a `ciphertext` param instead of plain title/body in the URL path. The user's device already has **Push Encryption** configured with AES256/GCM using the key in `BARK_AES_KEY` (`~/.claude/.env`) — confirmed working via decrypted test messages.

Key facts (from Bark's source, `Model/Algorithm.swift` and `NotificationServiceExtension/Processor/CiphertextProcessor.swift`):
- Supported algorithms: AES128 (16-byte key), AES192 (24-byte key), AES256 (32-byte key)
- Supported modes: CBC, ECB, GCM
- Key and IV are treated as **literal ASCII strings** — their UTF-8 bytes are used directly as the crypto key/IV (not hex-decoded), so key length and IV length must match the character count exactly.
- IV length required: CBC = 16 chars, GCM = 12 chars, ECB = no IV.
- GCM uses CryptoSwift's "combined" mode — the auth tag is appended directly after the ciphertext bytes before base64 encoding.
- **The `iv` can be sent per-request** as a separate URL/query param alongside `ciphertext` (`?ciphertext=...&iv=...`), which overrides the app's locally configured IV for that message. The **key must still be pre-configured on the device** — there's no way to transmit the key over the wire.

**Use the bundled script** to send an encrypted push (handles AES-256-GCM encryption + random 12-char IV + delivery):

```bash
/opt/miniconda3/envs/claude-sandbox/bin/python ~/.claude/skills/bark/scripts/send_encrypted.py --body "text" --title "text" --sound "name"
/opt/miniconda3/envs/claude-sandbox/bin/python ~/.claude/skills/bark/scripts/send_encrypted.py --markdown $'**bold**\n- item one\n- item two' --title "text"
```

`--title` and `--sound` are optional; either `--body` or `--markdown` is required. Requires `pycryptodome` in the `claude-sandbox` env (`pip install pycryptodome` if missing).

If a one-off variant is needed (different key/algorithm/mode than the default), write a small ad-hoc script instead:
1. Build the JSON payload, e.g. `{"title": "...", "body": "...", "sound": "..."}`
2. Encrypt it with the given key/mode (AES-GCM: `nonce=iv.encode('utf-8')`, then `ciphertext + tag`, base64-encoded)
3. Send via `curl --get "https://api.day.app/<deviceKey>" --data-urlencode "ciphertext=<b64>" --data-urlencode "iv=<iv>"` (omit `iv` if using ECB or the device's pre-configured IV)

If asked to use a "random IV," generate a random alphanumeric ASCII string of the exact required length (12 for GCM, 16 for CBC) — not random bytes hex-encoded.

A `{"code":200,"message":"success"}` response only confirms the Bark server relayed the push — it does **not** confirm the device could decrypt it, since the server never validates ciphertext. Ask the user to confirm the notification displayed correctly if this matters.
