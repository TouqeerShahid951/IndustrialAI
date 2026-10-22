# Prototype Instructions

Run the local server yourself and open the preview in the browser available to this environment. Do not give the user server-start instructions when you can run it.

Before making substantial visual changes, use the Product Design plugin's `get-context` skill when the visual source is unclear or no longer matches the current goal. When the user gives durable prototype-specific design feedback, preferences, or decisions, record them in `AGENTS.md`.

When implementing from a selected generated mock, treat that image as the source of truth for layout, component anatomy, density, spacing, color, typography, visible content, and hierarchy.

Build app UI in `src/`. Keep `.openai/hosting.json`, `worker/index.js`, `scripts/prepare-sites-build.mjs`, and `tests/sites-worker.test.mjs` intact so the same local prototype can be handed to Sites. Before a Sites handoff, run `npm run build` and `npm run test:sites`; the build must leave `dist/client/index.html`, `dist/server/index.js`, and `dist/.openai/hosting.json`.

Durable design preference: use the Evidence Focus layout and theme 3, Soft Graphite and Sage. Follow the selected fourteen mockups in `docs/design/2026-10-21-mvp-mockups/screens-graphite-sage/`: restrained system typography, graphite surfaces, sage actions with dark labels, amber candidate evidence, red reserved for critical/error states. Preserve source aspect ratio and distinguish machine evidence from saved human decisions.

Evidence-player feedback (2026-10-22): use cyan candidate boxes with dark contrast outlines and readable labels over warm/fire footage. Keep playback and incident tracks on one aligned original-source-time axis, with a visible shared playhead and separate overlapping events. Preserve exact intervals and distinguish model output from human decisions.
