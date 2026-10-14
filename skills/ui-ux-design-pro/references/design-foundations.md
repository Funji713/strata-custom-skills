# UI Design Foundations

Use this reference only for substantial design work. Select two or three lenses that materially change a decision; do not cite every theory by default.

## Decision Lenses

| Design need | Lens | Apply it as | Acceptance check | Source |
|---|---|---|---|---|
| Uncertain problem or broad scope | Double Diamond | Separate discovery, definition, development, and delivery; revise when testing changes the problem. | The primary task and success measure are explicit before implementation. | https://www.designcouncil.org.uk/resources/framework-for-innovation/ |
| Critical-flow usability | Nielsen's 10 heuristics | Expose system status, use the user's language, preserve control, prevent errors, and support recovery. | Each critical state gives clear feedback and a viable next action. | https://www.nngroup.com/articles/ten-usability-heuristics/ |
| Too many choices | Hick-Hyman law | Prioritize frequent choices and reveal advanced options progressively. | A first-time user can identify the primary choice without scanning every option. | https://journals.sagepub.com/doi/10.1080/17470215208416600 |
| Frequent or consequential actions | Fitts' law | Size and place high-value targets for their context; isolate destructive actions. | The main action is comfortably reachable and cannot be triggered by an adjacent accidental tap. | https://doi.org/10.1037/h0055392 |
| Dense visual hierarchy | Gestalt grouping | Use proximity, similarity, common region, and continuity to reveal relationships. | Users can distinguish groups and scanning order without relying only on borders or color. | https://www.interaction-design.org/literature/topics/gestalt-principles |
| Accessible web interaction | WCAG 2.2 | Design and verify perceivable, operable, understandable, and robust interactions. | Relevant focus, label, keyboard, target-size, contrast, and non-color checks pass. | https://www.w3.org/TR/WCAG22/ |

## Selection Rules

- Apply WCAG 2.2 to every web-facing interface and use the target platform guidance alongside it.
- Apply Nielsen heuristics to every critical flow, but report only findings that change the design.
- Add Hick-Hyman for menus, filters, multi-step forms, configuration, or choice-heavy screens.
- Add Fitts' law for mobile actions, repeated desktop work, and irreversible or high-risk actions.
- Add Gestalt grouping for dashboards, tables, comparison views, and other data-dense surfaces.
- Add Double Diamond when the user problem or success measure is not yet well defined; skip it for a well-scoped implementation change.

## Evidence Matrix Example

| Evidence type | Source | Decision | Acceptance check |
|---|---|---|---|
| Product | A broker's order ticket | Keep quote context visible during order review. | Users see instrument, side, price type, and quantity before confirmation. |
| Theory | Hick-Hyman | Keep order type choices compact; reveal advanced conditions on demand. | The default order can be configured without opening advanced settings. |
| Standard | WCAG 2.2 | Use text and icon labels for price direction and a visible focus outline. | Meaning remains available without color or pointer input. |
