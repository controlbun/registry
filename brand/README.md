# brand

> **Status 2026-09-20.** Live. Source artwork and where each file is used.

Source artwork. Tracked, not deployed: `astro/public/` carries only the sizes the
site links.

    avatar-512.png            upload this to GitHub, HF, npm, anywhere with an avatar
    avatar-on-dark-512.png    only for surfaces you control and know are dark
    mark-outlined-1254.png    master, works on any background
    mark-plain-1254.png       master, dark backgrounds only
    mark-light-1254.png       the original opaque exports, kept as the record of
    mark-dark-1254.png        what was handed over

All four masters carry a real alpha channel except the two named `light`/`dark`,
which are the opaque originals.

## Which file where

`avatar-512.png` is the one to upload. It is the outlined mark, cropped to the
artwork and padded to a square, so the bun fills the frame instead of floating in
margins that a circular crop would eat.

The outline is why it is the default everywhere. It draws every edge regardless of
what sits behind it, so the same file reads on a white page, on GitHub's dark
theme, and on the near-white GitHub uses in light mode. Verified by compositing,
not by assuming.

`avatar-on-dark-512.png` has no outline and dissolves on anything light. Use it
only where you control the surface and know it is dark.

## Measured 2026-09-13

    light   beret #3570FD vs page 4.26:1   vs bun 4.06:1   outline 11.75:1
    dark    beret #84A3FD vs page 7.93:1   vs bun 2.29:1   bun 18.12:1

The dark beret against the bun is under 3:1, so those two light shapes soften into
each other where they meet. Contrast ratio measures brightness only, and the hue
difference between blue and cream does work the number cannot see, so at every size
from 16px up the hat still reads as a hat. Real but minor. A thin stroke in the
background color along that edge fixes it, which is what the outlined file already
does.

## Known and unfixed

The sparkles stop working below about 32px. They become three stray pixels that
read as dirt rather than as motion, which is why `avatar-512.png` is better used
large and the favicon would be better cropped tighter still.

These are raster. The real asset is an SVG: a few KB instead of a few hundred,
sharp at any size, and recolorable by editing four hex values instead of redrawing.
The numbers above are what to hand an illustrator rather than asking them to match
by eye.
