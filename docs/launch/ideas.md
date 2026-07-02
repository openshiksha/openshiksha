# OpenShiksha — Direction Ideas (now that the platform is built)

> Prioritized backlog of *what OpenShiksha should do next*, maintained by the
> `openshiksha-plan` routine. The platform itself is feature-complete for a
> launch: modern stack, live in prod, PWA-offline, 3 languages, WCAG-AA-gated,
> observable, OSS-ready, with a not-in-the-market bounded-AI demo (12 beats).
> The bottleneck is no longer code — it's **audience, content, and real users**.

## Now (the launch arc)

1. **The launch video** — see [`video-plan.md`](video-plan.md). The single
   highest-leverage artifact: it powers the Show HN post, the README, the
   Product Hunt page, and any pilot pitch. Everything below rides on it.
2. **The meta devlog cut** — a second, separate video/post: *"Four scheduled AI
   agents planned, built, reviewed, and deployed this ed-tech platform — ~500
   PRs, with receipts."* `docs/daily-plans/` + `docs/changes/` + the PR history
   are the receipts. Arguably more viral than the product video for the HN
   audience; keep it separate so the product video stays about kids and
   teachers, not about AI tooling.
3. **Launch sequence** — Show HN → r/opensource + r/India edu subs → Product
   Hunt. Prereqs: video published, prod URL solid (DNS flip, TLS, real AI key),
   a "try it in 60 seconds" demo login on the landing page.

## Next (after launch)

4. **A real pilot** — one school, tutor, or NGO classroom in India actually
   using it for a term. One testimonial clip of a real student beats every
   feature. This also forces the content question (below) honestly.
5. **Content depth** — the imported question bank is the moat for real usage:
   audit coverage per CBSE chapter, expand via the (verified, PV-gated)
   AI practice-problem pipeline once PV-3 ships. Content, not features.
6. **Contribution funnel** — the widget SDK is the "good first issue" machine:
   *"write an interactive widget in an afternoon"* (`npm run widget:new`).
   A CONTRIBUTING section + 2–3 scoped widget ideas turns viewers into
   contributors. Language #4 (Tamil — the non-Devanagari stress test) is the
   other perfect community task: config + content, zero code.

## Later / parked

7. **PV-3 on-screen practice generator** — the last unshipped wow beat
   (`ai-features` routine owns it); include in the video if it lands in time.
8. **AI-tutor chat branch** (`ai/2026-06-04-ai-tutor-chat`) — stays parked.
   It's the "air" anti-pattern the whole demo positions *against*; reviving it
   would blur the bounded-AI story that makes the video distinctive.
9. **Teacher self-serve onboarding** — guided first-run (create class → invite
   code → first AI widget) matters the moment strangers arrive from the video;
   design after watching the first real teacher stumble, not before.
