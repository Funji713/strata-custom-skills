# Slide Blueprint and Visual Storyboard

Use this reference when designing a new deck or substantially redesigning one. A blueprint should let another person build each slide without guessing where the main content goes. A storyboard should let the user judge its visual direction before final production.

## Per-slide record

Keep the record compact, but include these decisions for **each** slide:

| Decision | What to specify |
| --- | --- |
| Purpose and takeaway | The question answered and the exact claim or topic title the audience will see |
| Content | Final wording when known; otherwise a clearly labeled placeholder with the required evidence or asset |
| Composition | Each element's role, approximate position and proportion, alignment, and relationship to other elements; identify title, evidence, explanation, source, and any callout without drawing a box around each one |
| Visual treatment | Slide archetype, hierarchy, type scale, colors with semantic meaning, image treatment or chart encoding, and intentional whitespace |
| Image provenance | The source page or file and intended crop for a reused visual; otherwise the concept and composition for an imagegen visual, identified as generated where authenticity could be mistaken |
| Reading path | Where the eye enters, how the evidence is read, and what the viewer should retain |
| Source and notes | Evidence provenance, assumptions, speaker details, and accessibility needs that should not crowd the canvas |

Use proportions or a simple grid to communicate geometry. Pixel coordinates are useful only when a fixed output size or template requires them. Reuse a small set of archetypes, but adapt the composition when the evidence requires it. Do not force every slide into the same arrangement. Plan open space as an intentional part of the layout. Vary rhythm through scale, crop, alignment, and visual weight rather than alternating generic card grids.

## Visual preview

- Render **one frame per slide** at the intended aspect ratio. Show the actual layout, representative type, palette, chart or image areas, and approximate content density. The preview should convey the intended visual character, not merely boxes with labels or a grid of rounded cards.
- Where an image supports the message, pair it with concise text. Use the corresponding image or a legible crop from the supplied source first. If none exists, generate a fitting visual for the planned composition; do not leave an empty image placeholder in the storyboard when image generation is available. Keep source screenshots and generated visuals distinguishable in the blueprint and notes, and mark generated imagery on the slide if viewers might otherwise mistake it for factual evidence.
- Use the deck's production route when practical. A draft slide render, PDF page, or image frame is suitable. An HTML or SVG storyboard is also suitable for a planning-only deliverable if it renders reliably. Use supplied brand assets as supplied; do not synthesize a logo or factual image.
- Show frames together as a contact sheet for pacing and consistency, and make individual frames available at a size where text and alignment can be reviewed. When the final deck itself is rendered and inspected, those renders satisfy this preview requirement.
- Put `PLACEHOLDER`, `ILLUSTRATIVE`, or equivalent directly on any unsourced mock content. Keep it visible in both the blueprint and frame. Do not imply that decorative sample data supports a conclusion.
- Compare the frames with the blueprint: each planned element appears, evidence is legible, title and hierarchy match the message, and adjacent slides have a coherent rhythm. Check whether any border, fill, or container earns its place by clarifying structure; remove decorative boxes. Fix crowded or inconsistent frames before handing off the design.

The storyboard is a design approval surface. It is not a substitute for checking editability, notes, links, accessibility, and exported file behavior when producing the finished deck.
