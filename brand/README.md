# brand

Source artwork. Tracked, not deployed: `astro/public/` carries only the sizes the
site actually links.

    mark-light-1254.png     master, light backgrounds
    mark-dark-1254.png      master, dark backgrounds
    avatar-light-512.png    for uploading as an org avatar
    avatar-dark-512.png     dark is the default, so this is the one to upload

The two files differ by more than a background swap. On white the cream bun is
1.04:1 against the page and needs its navy outline to exist at all; on near-black
it is 18:1 and the outline is dropped. The beret changes value too, because the
blue that reads on white is not the blue that reads on black.

Measured 2026-09-13:

    light   beret #3570FD vs page 4.26:1   vs bun 4.06:1   outline 11.75:1
    dark    beret #84A3FD vs page 7.93:1   vs bun 2.29:1   bun 18.12:1

The dark beret against the bun is under 3:1, so the two light shapes soften into
each other where they meet. A thin stroke in the background color along that edge
would fix it; the light file already does the same thing with a navy stroke.

These are raster. The real asset is an SVG, which would be a few KB instead of a
few hundred and would stay sharp at any size. The values above are what to hand an
illustrator rather than asking them to match by eye.
