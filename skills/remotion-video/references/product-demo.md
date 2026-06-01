# Product Demo + Launch Video

Create a product demo and launch video from any product URL. Scrape real branding, download product images, and build an animated ad with simulated demo and screenshot showcase.

## Input

User provides a product URL (e.g., `https://your-product-url.com`).

**Variant — multi-product catalog**: If the user provides a catalog/store page with multiple products, see [Multi-Product Mode](#multi-product-mode) below.

## Prerequisites

- **Playwright MCP** for web scraping — see [integrations.md](integrations.md) for setup

## Workflow

### Step 1: Research & Asset Download

Use Playwright MCP to visit the URL. Extract:

- **Product name and logo** — download logo/favicon to `public/`
- **Brand colors** — pull from the site's CSS or visible design
- **Tagline / hero headline**
- **Core user flow** — what does someone DO with this product?
- **3 key features** or value propositions
- **Social proof** — user counts, testimonials, logos
- **Product images** — find product screenshots/images the site already displays (hero images, product UI screenshots, feature images, app previews). Download 2-3 of the best to `public/product-1.png`, `product-2.png`, etc. Look for `<img>` tags, `og:image` meta tags, background images. Prefer PNG/JPG product mockups over generic stock photos. Only take browser screenshots as a last resort.

Present findings and a proposed 6-scene outline. **Wait for approval** before coding.

### Step 2: Build the Video

Build 6 scenes (25 seconds total):

**SCENE 1 — Hook (3s)**:
- Bold text: a pain-point question relevant to the product (e.g., "Still editing videos manually?")
- Text slams in with spring from 2x scale, holds 2s, fades out
- Dark background with subtle brand-color radial glow

**SCENE 2 — Product Intro (3s)**:
- Product name/logo scales in with spring from 3x to 1x
- Real tagline slides up below
- Particle burst behind logo: 20 circles expanding outward with random trajectories, fading out, using brand accent color

**SCENE 3 — Simulated Demo (8s)**:
- Recreate a simplified, MOBILE-SIZED version of the product's core interaction using React components (styled divs, inputs, buttons, cards in brand colors)
- NO device mockup frame — build UI elements directly on dark background, large enough to fill safe zone width (960px+)
- Animate a cursor (small white circle with subtle trail) that:
  - Moves to an input field (full width, 72px tall, 36px text) using `spring({ damping: 15 })`
  - Click ripple effect (expanding circle that fades)
  - Text types into field character by character at 36px font size
  - Cursor moves to a large button (full width, 64px tall)
  - Click ripple on button, button depresses (scale 0.95)
  - Loading spinner appears (0.5s), then results animate in with staggered spring
  - Result cards/text: 36px+ body text

**SCENE 4 — Product Image Showcase (5s)**:
- Display downloaded product images LARGE (near-full width, 900px+), centered with drop shadow and rounded corners (16px)
- NO device mockup frame — product images already look polished
- Animate through 2-3 images:
  - Image 1 scales in from 0.9 to 1.0 with spring, holds 1.5s
  - Crossfade to Image 2, holds 1.5s
  - Crossfade to Image 3, holds 1.5s
- Feature headline (56px, Inter 700) fades in above or below, updating with each transition

**SCENE 5 — Feature Callouts (3s)**:
- Product image scales down to 40%, moves to top
- 3 feature lines animate in below, staggered by 10 frames:
  - Each line: colored icon (checkmark, lightning, star) + short text (36px+)
  - Lines slide in from right with `spring()`

**SCENE 6 — Social Proof + CTA (3s)**:
- Everything fades out
- If social proof found: animate number counting up from 0 (e.g., "50,000+ users")
- Product URL pulses gently (scale 1.0 to 1.03), positioned above bottom safe zone
- Fade to black

## Cursor Design

White circle (12px), 50% opacity trailing shadow, smooth bezier paths between click targets. Never teleport — always animate movement.

## Visual Style

Use dark theme from `defaults.md`, but adapt accent colors to match the product's brand. If the website uses a distinctive Google Font, match it instead of Inter.

## Duration

25 seconds. 6 scenes.

## Output

- Remotion composition at 1080x1920, 30fps
- Launch `npx remotion studio` for preview

## Multi-Product Mode

When the user provides a catalog or store page (e.g., a product listing page with multiple items), generate a separate Remotion composition for each product instead of one combined video.

**Pattern**:
1. Use Playwright MCP to scrape all product cards on the page
2. For each product, extract: name, price, key specs, image URL, screenshot of product card
3. Store as an array of product data objects
4. Create one shared `ProductCard` React component that accepts product props (name, price, image, specs)
5. Create one Remotion composition per product, each using the shared component
6. Each composition appears as a separate entry in Remotion Studio

**When to use**: The user says "create a video for each product" or provides a page with 3+ products.

**Key insight**: Build a reusable template component first, then instantiate it. This avoids duplicating scene code across compositions.
