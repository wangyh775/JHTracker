## Context

See `proposal.md` for motivation. Current `skills/job-sourcing-and-scoring/SKILL.md` has a vague "Search the web" step with no tool priority, no platform routing, and no verification gate. Agent has no structured protocol to follow, leading to fabricated data.

## Goals / Non-Goals

**Goals:**
- Define a strict priority-ordered tool chain for web retrieval (Firecrawl → CDP/Playwright → Exa → Tavily → built-in)
- Implement platform routing based on `enterprise_preference` (央国企/外企/民企/不限)
- Add a three-step authenticity verification gate (URL reachability → content consistency → cross-source verification)
- Add refusal protocol — Agent must report failure instead of fabricating
- Add provenance trace logging for every sourced record
- Add `enterprise_preference` field to `data/profile.md`

**Non-Goals:**
- No changes to the database schema (source_url and trace fields already exist)
- No changes to the MCP server's core write logic (only docstring updates)
- No changes to the applications table structure

## Decisions

- **Tool chain order**: Firecrawl scrape (proxy=enhanced) first → CDP network interception → Exa → Tavily → built-in. Rationale: Firecrawl handles JS rendering and proxy bypass best for Chinese platforms; CDP catches SPA XHR data; Exa/Tavily are general fallbacks.
- **Platform routing in Skill, not in code**: The routing table lives in the Skill SOP doc, not in Python code. This makes it easy to update without deployments. Agent reads the SOP and applies it.
- **Two-tier verification**: Cross-source verification is a soft requirement — if a second source can't be found, data is still written but marked `single_source`. Rationale: many niche companies only appear on one platform.
- **CDP via Playwright**: Use Playwright's `page.route()` for network interception. Available through our existing Firecrawl browser execute capability.
- **enterprise_preference in profile.md**: Simple YAML-like field, read by Agent at task start. Falls back to asking user if absent.

## Risks / Trade-offs

- [Firecrawl proxy may not bypass all anti-scraping] → Fall back to CDP/Playwright browser automation
- [CDP interception is slower than direct scrape] → Use only as second layer, not first
- [Platform routing may miss opportunities] → 不限 fallback covers all platforms
- [Cross-source verification may fail for niche companies] → Allow single_source with provenance note