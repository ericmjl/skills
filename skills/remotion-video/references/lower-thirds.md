# Lower Third / Overlay

Create a transparent lower third overlay with avatar, name/title, and subscriber count or social proof. Rendered with transparency for compositing on top of other footage.

## Input

User provides a channel URL, brand URL, or social profile link (e.g., a YouTube channel, Twitter profile, company page).

## Prerequisites

- **Playwright MCP** for web browsing — see [integrations.md](integrations.md) for setup

## Workflow

### Step 1: Scrape Profile Data

Use Playwright to visit the URL. Extract:

- **Avatar / logo image** — download to `public/`
- **Display name** — channel name, brand name, or username
- **Subscriber / follower count** — exact number
- **Tagline or bio** — short description if available
- **Brand colors** — from profile theme or page design

Present the scraped data. **Wait for user approval** before coding.

### Step 2: Build the Lower Third

Create a Remotion composition at 1080x1920 (or match the target video resolution). The lower third occupies only the bottom portion of the frame.

**Layout**:
- Positioned in the lower third of the frame, above the bottom safe zone
- Transparent background (the composition will be rendered with alpha)

**Elements** (left to right):
1. **Avatar** — circular crop (64-80px diameter), subtle border in brand color, scales in with spring
2. **Name** — Inter 700, 36-44px, white (or brand-appropriate color)
3. **Subtitle** — Inter 400, 28px, secondary color (tagline, bio, or role)
4. **Social proof badge** — subscriber/follower count with icon, Inter 600, 28px, accent color

**Animation sequence**:
1. Background bar slides in from left with spring (0 to full width over ~15 frames)
2. Avatar scales from 0 to 1 with spring, 5-frame delay
3. Name text fades in, 3-frame delay after avatar
4. Subtitle fades in, 2-frame delay after name
5. Social proof badge fades in last, 3-frame delay

**All elements use `spring({ damping: 200 })` for entrance.**

### Step 3: Add Controls

Add timing/position sliders so the user can adjust:
- Vertical position (y offset)
- Horizontal position (x offset)
- Overall scale
- Animation speed (entrance duration)
- Text content (name, subtitle) — editable without code changes

See [advanced-patterns.md](advanced-patterns.md) for the timing sliders pattern.

### Step 4: Render with Transparency

```bash
npx remotion render <composition-id> out/lower-third.webm --transparent
```

## Visual Style

Adapt to the brand/channel's colors. Default dark overlay:

| Element | Value |
|---|---|
| Bar background | `rgba(0, 0, 0, 0.7)` with blur |
| Primary text | `white` |
| Secondary text | `#94a3b8` |
| Accent | Brand color from scraped data |

## Duration

3-5 seconds (entrance animation + hold). Configurable via timing sliders.

## Output

- Remotion composition with transparent background
- Rendered `.webm` with alpha channel
- Launch `npx remotion studio` for preview with controls
