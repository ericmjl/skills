# Testimonial / Social Proof Video

Create an animated testimonial video featuring real customer reviews, star animations, and social proof counters. Scrape data from a Google Business Profile.

## Input

User provides a Google Business Profile / Google Maps URL (e.g., `https://maps.google.com/some-business`).

## Workflow

### Step 1: Scrape Reviews

Visit the Google Business Profile URL. Extract:

- **Business name and category**
- **Overall star rating** (e.g., 4.8)
- **Total number of reviews** (e.g., "2,340 reviews")
- **3 best/most compelling reviews** — 5-star, with actual review text and reviewer first name
- **Business photo or logo** if available (save to `public/`)

If the page can't load Google reviews directly, use an alternative: search for the business name + "reviews" and scrape from the search results card.

Present business info and 3 selected reviews. **Wait for approval** before coding.

### Step 2: Build the Video

Build 5 scenes (20 seconds total). Uses **light theme** (see `defaults.md` Visual Style — Light Theme).

**SCENE 1 — Hook (3s)**:
- Clean white/light background (`#f8f9fa`) with subtle warm gradient (soft peach `#fff7ed` fading to white)
- Large gold star cluster: 3 overlapping star SVGs at different sizes/rotations, scattered in upper area, 15% opacity as decoration
- Bold text centered in safe zone, two lines:
  - "What people are saying about" — Inter 700, 44px, dark `#1a1a1a`
  - "[Business Name]" — Inter 800, 56px, gold `#f59e0b`
- Text enters with spring from below (translateY 40px to 0)
- Below text: overall star rating as 5 inline stars (40px, gold filled) with number ("4.8") — fades in 10 frames after text

**SCENE 2 — Star Rating Reveal (3s)**:
- Light background (`#f8f9fa`)
- 5 large star SVGs (60px each) in a row, centered
- Stars fill in one by one left to right with gold (`#f59e0b`) using spring animation, staggered 8 frames
- If rating is not a whole number (e.g., 4.8), the last star fills proportionally (use `clip-path` or width mask)
- Below stars: rating number counts up from 0.0 using `interpolate()`, dark text `#1a1a1a`
- Below that: "Based on [X] reviews" fades in, `#64748b`, with number counting up from 0
- Subtle gold particle shimmer behind stars

**SCENE 3 — Review Carousel (9s, 3 reviews x 3s each)**:
- Light background (`#f8f9fa`)
- Each review is a card taking full safe zone width:
  - Top: 5 small gold stars (28px)
  - Middle: review text in quotes, Inter 400, 36px, dark text `#1a1a1a` — max 3 lines, truncate with "..."
  - Bottom: reviewer first name + "Google Review" label, Inter 400, 28px, `#64748b`
  - Card background: white (`#ffffff`), subtle border (`#e2e8f0`), rounded corners (16px), soft shadow
- Card transitions: each card slides out left while next slides in from right, using `TransitionSeries` with slide transitions
- Small Google "G" logo icon (built as SVG — the 4-color G) next to "Google Review"
- Progress indicator: 3 dots below card, active dot is gold

**Decorative graphics** around each review card (fill empty space):
- ABOVE: large quotation mark SVG in gold at 10% opacity, 200px tall, top-left of safe zone
- BELOW (pick ONE per review, stagger entrance with card):
  - Review 1: animated 5-star rating bar chart (5 horizontal bars, gold fill on light gray track, spring)
  - Review 2: thumbs-up icon with spring + count-up number showing total reviews
  - Review 3: map pin icon with location text, subtle pulse animation
- Decorative elements: muted colors, 30-50% opacity, gold (`#f59e0b`) or muted gray (`#94a3b8`)

**SCENE 4 — Social Proof Stack (3s)**:
- Light background (`#f8f9fa`)
- 3 stat lines stagger in from bottom with spring, 10-frame delays:
  - Gold star icon + "[X] star rating" — dark text `#1a1a1a`
  - People icon + "[X]+ happy customers" (count up)
  - Map pin icon + "[City, State]"
- Icons gold (`#f59e0b`), text dark `#1a1a1a`

**SCENE 5 — CTA (2s)**:
- Light background (`#f8f9fa`)
- Business name in large text (Inter 800, 56px, `#1a1a1a`), scales in with spring, centered
- Prominent CTA button: full safe-zone width, 72px tall, rounded 16px, gold background `#f59e0b`, white text "Book Now" or "Call Today" at 40px
- Button enters with spring from below
- Below button: website URL or phone number, Inter 600, 36px, `#64748b`
- No fade to black — end on clean light background with CTA visible

## Visual Style

Uses the **light theme** from `defaults.md`. Gold (`#f59e0b`) replaces indigo as the accent color throughout.

## Duration

20 seconds. 5 scenes.

## Output

- Remotion composition at 1080x1920, 30fps
- Launch `npx remotion studio` for preview
