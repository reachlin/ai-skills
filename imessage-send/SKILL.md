---
name: imessage-send
description: Send a single iMessage on macOS via AppleScript/osascript driving the Messages app. Use this skill whenever the user asks to "send an iMessage", "text someone on iMessage", "message <person> on iMessage/Messages", or wants to send a test/notification message to a phone number or email through Apple Messages. Only applies on macOS with Messages.app signed into iMessage — not for SMS-only recipients, group messages, or bulk/mass sending.
version: 1.0.0
---

# iMessage Send Skill

Send one iMessage to one recipient using AppleScript, driven through `osascript`.

## When This Skill Applies

Activate when the user wants to send a single iMessage to a specific recipient (phone number or email/Apple ID) via Messages.app on macOS.

Do **not** use this for:
- Bulk/mass messaging — this skill sends to exactly one recipient per invocation, never loop it over a list of people
- SMS-only recipients (green-bubble, no iMessage) — the AppleScript `buddy ... of service "iMessage"` lookup requires the recipient to be iMessage-reachable, or it throws a "Can not get buddy" error
- Group messages or attachments — out of scope for this pattern

## Required Parameters

- **recipient**: phone number (e.g. `+15551234567`) or email/Apple ID. If the user says "send yourself a test message" without naming an address, ask which of their own iMessage-reachable addresses/numbers to use (or check if one is already configured in their notes/memory) rather than guessing — there's no safe default recipient to assume. If the user names someone else, use that instead.
- **message**: the text body to send — required, never send with an empty or placeholder body

If the user says "send one" or "send a test" without giving text, it's fine to send a short generic message (e.g. "Test message from Claude Code").

## How to Send

Use the heredoc form of `osascript`, **not** the one-liner form. The one-liner (`osascript -e 'tell application "Messages" to send "..." to buddy "..." of service "iMessage"'`) fails with `execution error: Messages got an error: Invalid key form. (-10002)` because AppleScript can't resolve `service "iMessage"` as a bare string key — it must be resolved as an object reference first via a `whose` filter.

```bash
osascript <<'EOF'
tell application "Messages"
    set targetService to 1st service whose service type = iMessage
    set targetBuddy to buddy "<recipient>" of targetService
    send "<message>" to targetBuddy
end tell
EOF
```

Substitute `<recipient>` and `<message>` directly into the heredoc. No output on success. Run it with the Bash tool.

## Prerequisites

- Messages.app must be installed and signed into an iMessage account on this Mac
- The recipient must be reachable via iMessage (blue bubble) — SMS-only contacts will fail
- No special permissions needed beyond the usual macOS Automation/Accessibility prompt the first time `osascript` controls Messages.app (macOS will prompt for this the first time; if it's denied, System Settings → Privacy & Security → Automation → Terminal (or the app running these commands) needs Messages checked)

## Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| `Invalid key form. (-10002)` | Used the one-liner form instead of resolving `service` as an object first | Use the heredoc pattern above |
| `Can not get buddy "..."` | Recipient isn't iMessage-reachable, or the address/number is malformed | Confirm the recipient uses iMessage; try the exact email/number format they use in Contacts |
| No error, but message not delivered | Messages.app not signed in, or network/Apple ID issue | Open Messages.app manually and confirm it's signed in and can send a message there |

## Notes

- Sending a message is a real, visible action to the recipient — confirm with the user before sending if the recipient or content wasn't explicitly stated by them in this conversation
- This skill only sends; it doesn't read replies or poll for delivery status
