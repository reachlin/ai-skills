---
name: linkedin-post
description: Draft and publish a LinkedIn post announcing a project, tool, or piece of work, then post it to the user's LinkedIn feed via the browser. Use this skill whenever the user says "post to linkedin", "publish to linkedin", "share this on linkedin", "announce this on linkedin", or similar. Always confirms the exact draft text with the user before publishing, and appends a "published by Claude Code" disclosure line.
---

# LinkedIn Post Skill

Turn a piece of finished work (a repo, a tool, a blog post, a milestone) into a short LinkedIn post and publish it to the user's feed.

## Step 1: Identify what's being announced

If the user names a specific thing ("post about the almanac repo"), use that. If it's ambiguous or they just say "post this to linkedin" right after finishing something, infer the subject from the current conversation — but if there's real ambiguity about what to announce, ask rather than guess.

Pull real details from the source (README, repo description, blog post) rather than inventing them. A GitHub repo's README and description are the best source for an open-source project announcement.

## Step 2: Draft the post

Style, confirmed with the user on 2026-07-20:
- **Product-focused, not process-focused.** Describe what the thing *is* and *does*. Don't narrate "I spent today building X" or walk through how it was built — that reads as a dev-log, not an announcement. (Save the build-process narrative for the `daily-report` skill's blog posts instead.)
- Lead with the name and a one-line description of what it is.
- One short paragraph on what it does / why it's useful.
- One link (repo, post, etc.).
- 3-5 relevant, lowercase hashtags at the end (e.g. `#opensource #ai #aws`).
- Keep it tight — a few short paragraphs, not a wall of text.

Always end the post with this disclosure line, as its own paragraph after the hashtags:
```
Published by Claude Code, automatically.
```

## Step 3: Confirm before publishing — never skip this

Publishing to LinkedIn is a public, visible action. Show the exact draft text (via AskUserQuestion with the draft in the `preview` field, or just pasted in chat) and get an explicit go-ahead before posting. If the user pushes back or says something short and ambiguous (e.g. just "AI bot"), don't guess what they mean — ask them directly what they'd like changed, then redraft and reconfirm.

Never post without this confirmation step, even if the user's original request sounded like blanket permission ("publish my work to linkedin automatically") — "automatically" refers to automating the mechanics (drafting + posting via browser), not to skipping approval of the actual text.

## Step 4: Publish via browser

Requires the `mcp__claude-in-chrome__*` tools (load via ToolSearch if deferred: `select:mcp__claude-in-chrome__tabs_context_mcp,mcp__claude-in-chrome__navigate,mcp__claude-in-chrome__computer,mcp__claude-in-chrome__find`). This uses the user's real logged-in Chrome session — a fresh headless browser (e.g. chrome-devtools MCP) will not be signed into LinkedIn.

1. `tabs_context_mcp` (createIfEmpty: true) to get a tab.
2. `navigate` to `https://www.linkedin.com/feed/`.
3. `find` the "Start a post" element and click it to open the composer.
4. Click into the text area, then `type` the full post text (including the disclosure line).
5. **Wait for the link preview card to finish loading before clicking Post.** Pasting a URL triggers an async preview card that loads a moment later and pushes the Post button down — clicking at the pre-preview coordinates misses. Take a fresh screenshot right before clicking Post to get the actual button position; don't reuse coordinates captured earlier in the flow.
6. Click Post. Screenshot to confirm — the composer closes and the new post appears at the top of the feed with a "Post successful" toast.

If a correction comes in after the post is already live (e.g. "add a line about X"), don't re-post — use the post's `···` menu → **Edit post**, amend the text, and **Save**.

## Step 5: Report back

Confirm what was posted and that it's live. No need to fetch or paste the public URL unless asked.
