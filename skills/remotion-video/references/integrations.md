# Integrations

Remotion integrates with external tools and libraries. Load this file only when the video type or user request calls for one of these integrations.

## Playwright MCP

Web browsing and scraping. Required for product demo and lower third types that scrape live websites.

**Setup**: Add Playwright MCP to the agent config. In Claude Code, send the prompt `add Playwright`. When prompted, install globally. Confirm with `/mcp`.

**Use for**:
- Scraping product pages (name, price, specs, images)
- Taking screenshots of website elements
- Downloading images from live pages
- Extracting brand colors from CSS

**When to use**: Any time the agent needs to visit a URL and extract structured data or images.

## Lottie Animations (`remotion@lottie`)

Resolution-independent animations (vector-based alternatives to GIFs). Thousands available at [lottiefiles.com](https://app.lottiefiles.com).

**Setup**:

```bash
npx remotion@lottie
```

**Usage**: Download a Lottie JSON file from lottiefiles.com, place in `public/` or `assets/`, then import into a composition:

```tsx
import loadingLottie from "../assets/loading.json";
import { Lottie, LottieAnimationData } from "@remotion/lottie";

<Lottie animationData={loadingLottie as LottieAnimationData} />
```

**When to use**: When the user wants polished pre-made animations (loading spinners, celebration effects, icons), or when they provide a Lottie file.

## 3D Assets (`@remotion/three`)

Three.js integration for 3D rendering. Can convert SVGs to 3D objects with materials and lighting.

**Setup**:

```bash
npx remotion@three
```

**Usage**: Import SVG as a 3D shape, apply metallic/glossy materials, add lighting:

```tsx
import { Three } from "@remotion/three";
```

**When to use**: When the user asks for 3D elements, metallic effects, or wants to elevate a flat SVG into a 3D scene. Works well for hero product shots and logo reveals.

## ElevenLabs (Optional — Requires API Key)

Voice-over generation via ElevenLabs API. Requires the user to have an ElevenLabs account and API key.

**Setup**: Requires `ELEVENLABS_API_KEY` environment variable. Use via MCP integration or direct API calls.

**Before using**: Ask the user to confirm they have an ElevenLabs API key. If they don't, skip voice-over or suggest they sign up at elevenlabs.io.

**When to use**: When the user explicitly asks for voice-over, narration, or speech in their video.

## Replicate (Optional — Requires API Key)

Access to AI image and video models (image generation, style transfer, etc.) via Replicate's API. Requires the user to have a Replicate account and API key.

**Setup**: Requires `REPLICATE_API_TOKEN` environment variable.

**Before using**: Ask the user to confirm they have a Replicate API key. If they don't, use SVG-only graphics instead.

**When to use**: When the user wants AI-generated imagery, style-transferred backgrounds, or generative art elements that can't be achieved with SVG alone.
