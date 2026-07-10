---
name: Content pack proposal
about: Propose or offer to author a pack of questions/problems for the shared bank
title: "[Content]: "
labels: content-pack
assignees: ''
---

<!--
This is a PROPOSAL / coordination surface — NOT where you submit a pack.
Content packs are DATA (questions authored as JSON) and are submitted through
the contrib/packs/ pull-request funnel: see contrib/packs/README.md. There the
CI job validates your pack against the schema, and after merge a maintainer
imports it as PENDING for in-app review + approval before it reaches students.

Use this issue to agree on scope first: what to cover and who will write it. If
your idea needs a brand-new widget KIND (not just config for an existing one),
that is code — open a Widget proposal instead (docs/widgets/review-bar.md).
-->

## Topic & grade band

<!-- The subject/skill and the grade range. E.g. "equivalent fractions, grades 4-6". -->

## Rough size

<!-- Approximate number of questions/subparts you have in mind. -->

## Does it need a new widget kind?

- [ ] **No** — plain questions, or config for an existing widget kind
      (see the vendored kinds in apps/core/data/widget_schemas/).
- [ ] **Yes** — a new interactive widget kind is needed. That is CODE, not
      content: open a **Widget proposal** first (link it here) so the kind
      lands via PR review before the pack references it.

## License & provenance

<!-- Content ships with an attribution/provenance block (author, source,
     license). Confirm you have the right to contribute this material and note
     its source/license here. Original or openly-licensed (e.g. CC BY) only. -->

## Are you offering to author it?

- [ ] Yes — I'll author the pack JSON and open a PR to `contrib/packs/`
      (format + local validation one-liner in contrib/packs/README.md).
- [ ] No — proposing the topic for someone else to pick up.
