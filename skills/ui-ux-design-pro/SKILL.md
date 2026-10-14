---
name: ui-ux-design-pro
description: Research real web, desktop, and mobile UI patterns and turn them into distinctive, implementation-ready frontend design direction. Use when Codex needs to design or redesign a website, product interface, dashboard, desktop app, or mobile app; collect UI references; define a visual system; or build a polished responsive interface. Do not use for a tiny isolated component change with an already established design system.
---

# UI UX Design Pro

Use product research to understand familiar patterns and flows, then use UX theory and standards to test whether the resulting interface is clear, efficient, and inclusive. Design an original interface; never reproduce a competitor's screen.

## Establish The Brief

Capture only the inputs that change the design:

1. Product, audience, and primary task.
2. Target surface: responsive web, desktop app, iOS, Android, or cross-platform mobile.
3. Critical flow and required states: empty, loading, validation, error, success, and permission states when relevant.
4. Brand constraints, technical stack, existing components, and accessibility requirement.
5. The desired character in a few adjectives and what to avoid.

Infer routine defaults from the codebase. Ask only for a missing constraint that would materially change the design.

## Build An Evidence Mix

Read [references/ui-source-catalog.md](references/ui-source-catalog.md) and, when the task is substantial, [references/design-foundations.md](references/design-foundations.md).

For each substantial interface, use this evidence mix:

- One platform or accessibility foundation matching the target surface.
- Two real-product references matching the primary flow, risk level, or information density.
- Two or three applicable theory lenses selected from the foundations reference. Treat them as decision rules, not a long reading list.
- At most one optional visual-direction reference. Use it for expression only, never as flow evidence.

Use live web or image search when available. Prefer real shipped product flows over isolated concept shots for navigation, onboarding, forms, billing, settings, search, and error handling. If the task's domain is not represented in the catalog, follow its domain search recipe instead of assuming a generic SaaS pattern. Use gallery shots only to calibrate visual expression.

Record a compact evidence matrix: evidence type, source, relevant surface or principle, decision to adapt, risk to avoid, and acceptance check. Do not browse broadly once the matrix explains the critical flow.

## Apply Theory As Guardrails

Choose only the lenses that change the design decision:

- Use **Double Diamond** when the problem, audience, or success measure is uncertain. Discover and define before generating layouts; develop and test alternatives before treating one as final.
- Use **Nielsen heuristics** to inspect feedback, language, control, error recovery, and consistency in every critical flow.
- Use **Hick-Hyman** and progressive disclosure when choices, filters, settings, or navigation would otherwise overload a first-time user.
- Use **Fitts' law** for primary and high-frequency actions: make targets appropriately large, reachable, and separated from destructive actions.
- Use **Gestalt grouping** for hierarchy and dense data: proximity, similarity, and common region must communicate structure before decoration does.
- Use **WCAG 2.2** as the accessible interaction baseline. Validate focus, contrast, labels, target size, keyboard behavior, and non-color cues where relevant.

Do not invoke a theory as a formula or as evidence that a design is correct. Pair it with product context, platform conventions, and direct validation.

## Preserve Originality And Rights

- Never copy screenshots, icons, illustrations, text, logos, a distinctive layout, or a proprietary component library from a reference.
- Extract principles, hierarchy, interaction sequences, density, and component roles instead of pixels.
- Combine observations from multiple sources; do not let one reference determine the final interface.
- Use official brand assets only when the user supplies them or authorizes their use.
- State when a reference is inspiration rather than evidence of a platform convention.

## Define The Design System

Before implementation, define a small, coherent system that the target UI can actually use:

1. Design thesis: audience, purpose, emotional tone, and differentiator.
2. Typography roles, color roles, spacing scale, radii, elevation, and content width.
3. Responsive grid, breakpoints, density, and navigation transformation.
4. Component set required by the critical flow, including state and error behavior.
5. Data-display, form, empty, loading, and destructive-action patterns as applicable.
6. Motion purpose and reduced-motion behavior; use motion to clarify state, not decorate every element.

Use the existing project design system when one is present. Supplement it with the evidence matrix; do not add a component library solely to imitate a reference.

## Apply Platform Rules

### Responsive Web

- Start with the primary task at a narrow mobile width, then scale content density intentionally.
- Check 375px, 768px, 1024px, and 1440px or the project's supported equivalents.
- Preserve keyboard navigation, visible focus, semantic structure, and a usable touch target at every width.

### Desktop Application

- Support efficient scanning, keyboard and pointer workflows, durable navigation, and appropriate information density.
- Do not force a mobile-card layout onto a data-dense desktop workflow.

### Native Or Cross-Platform Mobile

- Follow the selected platform's navigation, safe-area, input, keyboard, permission, and gesture conventions.
- Prioritize one clear primary action per screen and keep critical actions reachable without relying on color alone.
- Validate small-screen, dynamic-text, landscape, and interruption behavior when relevant.

## Implement With Intent

1. Build the critical flow and its states before secondary screens.
2. Use semantic, reusable components where repetition is real; avoid generic abstractions before a second use.
3. Keep the visual direction specific to the product. Avoid interchangeable gradient cards, excessive glass effects, and default typography without a reason.
4. Use consistent SVG iconography, clear hover or pressed states, and visible focus states.
5. Preserve the existing codebase's framework and component conventions unless they block the design requirement.

Use `surgical-coding-debug` for scoped implementation and verification work after the design direction is chosen.

## Validate Before Delivery

Check the final surface for:

- Task clarity, hierarchy, empty/loading/error/success states, and destructive-action feedback.
- Evidence traceability: the selected theory lenses have a visible decision and acceptance check, rather than an unexplained visual convention.
- Responsive reflow with no hidden controls or horizontal scrolling.
- Keyboard or assistive-technology path, label associations, contrast, focus visibility, and reduced motion.
- Platform-specific navigation, input, and density expectations.
- Originality: no copied brand assets, text, or recognizably cloned composition.

Use browser or device inspection when available. Report the widths or devices checked and any remaining limitation.

## Handoff

Provide the brief, short evidence matrix, design system decisions, implementation outcome, and validation performed. Keep detailed design reasoning internal unless the user asks for a design document.

## Avoid

- Treating visual galleries as evidence of usable flows.
- Collecting dozens of references or theories when a small, task-matched evidence mix answers the question.
- Applying a theory without naming the concrete decision and acceptance check it changes.
- Copying a single product's distinctive look or brand assets.
- Adding a new component library just to match a reference.
- Applying desktop density, hover-only controls, or tiny tap targets to mobile.
- Treating accessibility as a final cosmetic pass.
