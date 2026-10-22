# MVP design verification — 22 October 2026

Final result: passed

## Visual truth and implementation

Selected source: `docs/design/2026-10-21-mvp-mockups/screens-graphite-sage/06-incident-review.png` and `09-mobile-review.png`, plus the selected design-system/interaction contracts. Local implementation: http://127.0.0.1:8008. Source and rendered images were opened together in the same comparison inputs, followed by focused decision-control crops.

Evidence directory: `reports/mvp-implementation-2026-10-21/screenshots/`.

| Evidence | Pixels and normalization | State |
|---|---|---|
| Desktop source | 1487×1058, resized to 1440×1024 in `source-desktop-normalized.png` | W04 smoke candidate, false-alarm draft |
| Desktop implementation | Cua capture 2149×1528 includes extra canvas; content region cropped to 1440×1024 in `review-desktop-final-normalized.png` | Actual W04, video, saved false alarm |
| Mobile source | 853×1844, resized to 389×841 in `source-mobile-normalized.png` | W04 still at 1 second, draft |
| Mobile implementation | Native capture 581×1259 includes extra canvas; content cropped to 389×843 in `mobile-visible-final-normalized.png` | Actual W04 still at 1 second, saved false alarm, page scrolled approximately 90px |

Effective desktop CSS viewport: 1440×1024. Mobile: 389×843 (within one pixel of planned 390px width). Inherited browser zoom yields devicePixelRatio 0.6700000167; viewport capability sizes were 965×686 and 261×565. Capture API full-page images and native visible captures differ: full-page images reset capture origin and misplace fixed bars relative to the current scroll. Native visible capture plus DOM control geometry is authoritative for persistent mobile actions. No browser chrome or blank capture canvas was assessed as application UI.

## Comparison history

1. Earlier desktop build: evidence height pushed decisions below the first viewport. Fixed the desktop evidence maximum to 48vh at the target viewport; the decision tray and Save control now fit. Evidence: `review-desktop-before.png`, `review-desktop-final-normalized.png`.
2. Narrow review with the actual long camera name put Save below the first screen (P2). Fixed the header with a two-column layout and a persistent mobile action bar, with page-bottom clearance and 44px action targets. Evidence: `mobile-viewport-normalized.png` before; `mobile-visible-final-normalized.png` after. DOM measured Save at approximately y789–833 before the final extra 8px secondary-target adjustment; both actions remain inside the viewport. No horizontal overflow at either target width.
3. Filter row with two selectors wraps on narrow screens. Mobile navigation now includes Sign out; signing out and signing back in were exercised successfully.

## Required fidelity surfaces

- **Typography:** System sans-serif, restrained semibold headings, tabular source times and readable secondary copy match the selected direction. Actual camera names can wrap instead of truncating evidence context. Desktop decision text was inspected in `source-decision-region.png` and `implementation-decision-region.png`; these were opened together.
- **Spacing/layout:** Navigation, video-first hierarchy, source timeline and three-part desktop decision tray follow the source. Mobile stacks the same content. Persistent mobile review actions are an intentional adaptation for longer real content. Desktop keeps uncropped 16:9 source evidence in a centered container; the mock stretches/crops the scene wider. This preserves evidence and changes region proportions deliberately.
- **Colors/tokens:** Graphite #252C29, raised surfaces #303A35, sage #A9C8B5 with dark #17291E action labels, amber #FFB340 evidence and separate red error states. The saved button is disabled because no edits are pending; this differs correctly from the enabled draft button in the mock.
- **Images/assets:** Actual authenticated source frames replace the illustrative mock scene and its example box. Native aspect ratio, real tracked person boxes and configured zone geometry are preserved. Standard Phosphor vector controls remain crisp. No invented image or decorative replacement was used.
- **Copy/content:** Design-preview badges were replaced with real camera/upload metadata and Export. Raw flags, temporal candidates, saved human decisions and limited visibility are explicit. Actual development sample names and saved review state explain the remaining text differences.

## Interaction verification

In-app browser: login; actual video upload and preview preparation; all-five configuration; keyboard polygon creation; MPS job progress; native video play/pause; source seeking and single-frame movement; still fallback and next still; false-alarm review and reload; manual uncertain observation; history filtering and audit; MP4 download; mobile menu and sign-out. Native local API/worker acceptance separately verifies cancellation, retry, anonymous/range access, all three export formats and their stored review data. Latest browser console warnings/errors: none.

No actionable P0/P1/P2 design differences remain. Safari/WebKit and a real remote-client session were not exercised; these are compatibility coverage gaps, not passed checks. Real footage model accuracy is outside this visual result.

## Checklist

- [x] Source and implementation opened together at normalized dimensions.
- [x] Full-view and readable decision-region comparisons.
- [x] Earlier P2 findings fixed and revised captures compared.
- [x] Desktop and narrow layouts, keyboard controls and focus indicators inspected.
- [x] Actual media and saved states verified; console checked.

## Demo-readiness follow-up — 22 October 2026

Current-run functional/visual evidence is in [the follow-up audit](reports/demo-readiness-2026-10-22/report.md). The existing Graphite/Sage composition is retained. Library Activity and New analysis use existing tokens and native disclosure controls; history now reuses the accessible dialog; discard choices stay inside the manual form and dialog actions wrap on narrow widths. No dependencies were added.

Current desktop screenshots verify library counts/actions, keyboard zone setup, all-five processing completion and preservation of an unsaved review after declining Back navigation. Backend 65 tests, frontend 14 tests, TypeScript, production build and the real API/MPS-worker journey passed. A native confirmation from the earlier manual form stalled the in-app browser during the audit. The revised history/export/manual-dialog and narrow-screen acceptance checks remain explicitly pending; the earlier completion statement above applies only to the previous pass. Do not infer current mobile or full-browser sign-off from it.
