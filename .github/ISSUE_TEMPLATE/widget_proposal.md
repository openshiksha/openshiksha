---
name: Widget proposal
about: Propose a new interactive widget kind for the Widgets Framework
title: "[Widget]: "
labels: widget-proposal
assignees: ''
---

<!--
Widgets are CODE and ship only through pull-request review — never through the
content-pack pipeline (that pipeline carries data: questions + widget CONFIG
for kinds that already exist). Proposing here first means we agree on scope
before you build. The bar your eventual PR must clear is documented in
docs/widgets/review-bar.md; the SDK guide is docs/widgets/anatomy.md.
-->

## What does it teach?

<!-- The concept/skill, and the grade range. E.g. "equivalent fractions, grades 4-6". -->

## Interaction sketch

<!-- What does the student actually DO? Drag, type, arrange, plot…?
     A rough sketch/screenshot/GIF helps a lot. -->

## Answer-producing or explanatory?

- [ ] **Answer-producing** — the widget reports a value that the deterministic
      grader marks (like `number-line`). Describe the reported value and how
      precision/snapping keeps every reachable value gradeable:
- [ ] **Explanatory** — the student explores, nothing is graded (like
      `thermo-piston`).

## Config fields

<!-- The teacher-facing params you expect in params.schema.json, with types and
     bounds. E.g. min:number, max:number, step:number>0, label:string. -->

## Sandbox fit

<!-- The runtime is a network-less, deterministic `allow-scripts` iframe; render
     must be self-contained (no imports/closures/eval, no network, no unseeded
     randomness — per-student variation comes from croupier {{var}} upstream).
     Anything about your idea that might strain those rules? Say it here. -->

## Accessibility plan

<!-- How is every interaction keyboard-operable? What ARIA semantics apply
     (e.g. slider with aria-valuenow)? -->

## Are you offering to build it?

- [ ] Yes — I'd like to implement it after the scope is agreed
      (start with `npm run widget:new`, see docs/widgets/build-your-first-widget.md)
- [ ] No — proposing the idea for someone else to pick up
