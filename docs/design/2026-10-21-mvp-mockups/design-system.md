# Industrial AI — refined Evidence Focus design system

Design review draft, 21 October 2026. The user selected the dark Evidence Focus concept and requested meticulous Apple-inspired mockups of the complete MVP before implementation. This is a web product, not an Apple-branded/native application.

The reference is Apple's emphasis on clear hierarchy, familiar controls, legibility, adaptable layouts and deliberate grouping. The proposed choices below adapt those principles to an industrial video-review workflow; they are not a claim of Apple certification or tested accessibility conformance.

## Product priorities

1. Evidence is the primary content. Video/frame visibility takes priority over dashboards and decorative analytics.
2. Every flag has a source interval, a capability and an explicit machine/human distinction.
3. A reviewer can reject, confirm, remain uncertain, or record a missed event. No default judgment is selected for them.
4. A processing failure, missing observation or poor visibility must never turn into a reassuring safety result.
5. One shared component system serves every page and every capability; do not create five visually unrelated review products.

## Foundations

| Token | Value | Use |
|---|---|---|
| Canvas | `#111318` | Main dark surface |
| Raised surface | `#1B1E24` | Sheets, dialogs, restrained grouped controls |
| Control surface | `#252A32` | Secondary controls and fields |
| Divider | `#343A44` | Quiet structural separation; not a substitute for spacing |
| Primary text | `#F5F5F7` | Reading and headings |
| Secondary text | `#A8ADB7` | Supporting information |
| Muted text | `#858D98` | Nonessential metadata; never essential disabled-only information |
| Primary action | `#0071E3` with white label | Task actions and selected interactive controls |
| Focus | `#64B5FF` | Two-pixel keyboard focus ring, two-pixel offset |
| Attention | `#FFB340` | Candidate evidence, uncertainty and unsaved state when text also explains it |
| Error/destructive | `#FF6B6B` | An actual error or explicit destructive confirmation |

Measured token contrast, not a claim about every generated raster pixel: primary text/canvas 17.07:1; secondary/canvas 8.25:1; muted/raised surface 4.98:1; white/primary button 4.70:1; focus/raised surface 7.63:1. Test the implemented components, hover states, zoom and reduced-contrast imagery independently.

Use `system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif`; do not download or bundle Apple's fonts. Tabular numerals for source clocks and ranges. Page title 28/34 px semibold; section title 18/24 px semibold; body 15/22 px; metadata 14/20 px. A narrow-screen title may be 22/28 px. Avoid light/thin weights, all-caps paragraphs and information that relies on small print.

Spacing uses an eight-pixel rhythm with four-pixel adjustments inside controls. Desktop page padding 32 px, mobile 16 px. Authenticated navigation 64 px high on desktop. Controls normally 44 px high; touch hit regions at least 44×44 px even when the visible icon is 20 px. Buttons radius 10 px, inputs 8 px, dialogs 16 px. Do not turn every group into a rounded card.

System values are implementation contracts. The generated images are visual references, not CSS measurements; enforce these values in shared components rather than copying raster inconsistencies.

## Navigation and hierarchy

- Text-only **Industrial AI** wordmark. No new symbol, Apple logo, decorative crest or fake window chrome.
- Authenticated destinations: **Video library**, **Review**, **Incident history**. Blue underline and semibold text identify the current destination; color is not the only cue.
- **Operator** opens the session menu. Sign-out is a named action, not a mysterious icon.
- Setup and progress belong to Video library; evidence review belongs to Review; saved incident details belong to Incident history.
- A detail sheet preserves list/filter context. Escape closes it when no unsaved draft is at risk; focus returns to its invoking control.
- On narrow screens, navigation becomes a labeled Menu control. Do not shrink a desktop table or navigation row until it is unreadable.

## Icon grammar

Use one regular-weight outline family, proposed Phosphor. Pick the closest actual library symbol during implementation; no handmade SVG/emoji substitutes or downloaded SF Symbols. Keep optical size/stroke weight consistent. Decorative icons are hidden from assistive technology; every icon-only action has an accessible name and tooltip.

| Meaning | Icon treatment and behavior |
|---|---|
| Upload | Tray with upward arrow, accompanied by Upload video |
| Export preparation | Export/tray action with Prepare export; change to Download only once an artifact exists |
| Play / Pause | A play triangle when paused; pause bars only while playing |
| Frame stepping | Left/right chevrons, names Previous frame / Next frame |
| Fullscreen | Standard outward-corner icon, never a generic expand metaphor |
| Search / clear | Magnifier / clear x, with visible field label or accessible name |
| Password visibility | Eye / eye-slash, keyboard-operable, never a text-only glyph |
| Fire / smoke / smoking / helmet / zone | Consistent small outline capability icons; always paired with a text label |
| False alarm | Static x-circle plus text, not an empty radio-like circle in history |
| Uncertain | Question-circle plus explicit text |
| Processing complete | Small check with Complete; never Safe or Compliant |
| Pending / active stage | Quiet clock / restrained spinner; Reduced Motion uses a static label |
| Zone edit / delete / undo | Pencil / trash / counterclockwise arrow; names remain visible in the editing toolbar |

## Components and states

| Component | Contract |
|---|---|
| Primary button | One primary action for the active task; clear verb; stable width during busy state; prevent duplicate submission |
| Secondary button | Same height and type scale, quiet surface/outline; destructive action is not a competing primary until confirmation |
| Disabled button | Explain the missing requirement beside the relevant field; disabled appearance alone is insufficient |
| Segmented control | Video / Frames; changes the presentation of the same source time, preserves review draft |
| Toggle | Entire label row is associated with its switch; keyboard Space; has a programmatic checked state |
| Decision group | One radio group, ordered Confirm incident / False alarm / Uncertain; initially none selected |
| Notes | Directly editable; no redundant edit icon; allow 1,000 characters; show a truthful counter only near the limit |
| Field error | Visible label, inline reason, correction guidance; focus the first invalid field on submit |
| Search/filter | Keyboard-operable, visible clear/reset path; empty search results differ from an empty library |
| Status | Icon/text plus optional color. Processing status and human decision are independent |
| Modal | Focus trap, named heading, predictable Cancel/close, focus restoration, no backdrop click that silently destroys a dirty draft |
| Save feedback | Pending label, then saved state/quiet announcement; failure retains the draft and offers Retry |
| Toast | Supplementary feedback only; errors and review status also remain in the relevant screen |
| Timeline | Original source-time intervals; distinct playhead and event span; seek positions bound to the source/preview map |
| Video/frame view | Contain imagery at its actual aspect ratio; pillarbox 4:3 footage rather than stretch it; never invent enhanced details |

Hover shifts are subtle; focus must be unmistakable. Limit ordinary transition durations to about 120–180 ms and honor reduced motion. Use native semantics for buttons, fields, radio groups and dialogs. At 200% zoom content reflows instead of overlapping; table navigation and sheet controls remain usable.

## Why the review variants differ

- **Fire:** a bright doorway flag can remain uncertain; the interface must not call it a verified flame.
- **Smoke:** a persistent model flag can still be a false alarm; temporal evidence is not human confirmation.
- **No helmet:** retain explicit headwear evidence and person association, but explain limited head detail. No helmet box is not equivalent to no helmet.
- **Smoking behavior:** show person, cigarette and hand-to-mouth evidence separately. Missing evidence is not no smoking, and cigarette/gesture evidence alone is not a verified smoking event.
- **Restricted area:** show the saved zone and track, with entry time unknown when a person was first seen inside. Review is read-only for zone/configuration; editing creates a new analysis.

## References

Apple's [Layout](https://developer.apple.com/design/human-interface-guidelines/layout), [Buttons](https://developer.apple.com/design/human-interface-guidelines/buttons), [Typography](https://developer.apple.com/design/human-interface-guidelines/typography), and [Accessibility](https://developer.apple.com/design/human-interface-guidelines/accessibility) guidance informed the hierarchy, consistency, legibility and control decisions. Native macOS/iOS recommendations are adapted to this browser application rather than copied as operating-system chrome.

## Build verification still required

Static mockups cannot prove keyboard operation, screen-reader behavior, focus restoration, actual font scaling, browser playback, temporal alignment or backend persistence. Those are explicit acceptance checks in the MVP plan. All model states, track IDs and review fixtures shown here are illustrative, not additional detector-test results.
