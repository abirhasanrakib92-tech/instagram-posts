# Instagram posting playbook — @abirhasanrakib_

Every scheduled run follows this file. It covers what to post, how to design it, and how to publish it.

## Locked format (approved by the owner on 2026-11-09 — do not change)

Match these approved posts exactly in presentation; only the design inside the screen changes:
- App → `reference/app-approved-1.jpg` … `-5.jpg` (**5-slide carousel**: hand holding phone, description + nav bar, typography, colors, CTA)
- Dashboard → `posts/2026-11/2026-11-09-pm-hospital-ops-dashboard-1.jpg` … `-4.jpg` (**carousel**: full window, left half, right half, CTA; no popup/zoom card)
- Website → `posts/2026-11/2026-11-10-am-meeting-notes-website-1.jpg` … `-8.jpg` (**carousel**: whole home page in two columns, top of page large, the whole page rotated 90° in equal bands through the footer, CTA)

Always: 1080×1350, `#EEEEEE` background, light UI, the brand chrome ("Designed by" bar on all types, WhatsApp pill on dashboards only, see below) on the design slides; the fixed CTA slide stays last.
Do not edit `tools/render.py` or the mockup assets unless the owner asks.

## The schedule

- Two posts a day, Asia/Dhaka time: **morning 08:37** (`am`) and **night 20:39** (`pm`).
- Rotation never breaks: **app → dashboard → website → app → …** across consecutive slots.
  On a 3-column Instagram grid this keeps each column one type, which is the look the owner wants.
- `calendar.json` lists every slot from 2026-11-09 pm to 2026-12-11 pm (shifted 4 slots on 2026-11-18 after missed runs): type, niche, brand name, palette hint, status.
  Status goes `planned` → `ready` (designed, rendered, pushed) → `posted`.
- Every post is a **different niche**. Never reuse a niche, brand name, layout skeleton or color scheme from an earlier slot.

## What a run does

1. `cd` into the repo clone, `git pull`, then `npm ci --silent` (fonts + icons; needed by the renderer).
2. Work out the current slot from the Dhaka clock: before 14:00 → today's `am`, otherwise today's `pm`.
   Find it in `calendar.json`. If its status is already `posted`, stop — never post twice.
   If its status is `ready-pending-approval`, the owner has not approved it yet: do NOT post it; report that it is waiting for approval and stop.
3. If the slot is `planned`, design and render it now (see below), push, and mark it `ready`.
4. Post it (see Publishing). Record `media_id`, set `posted`, commit and push.
5. Prepare the **next** slot the same way (design → render → push → `ready`), so it is waiting before its time.
   If anything about the next one fails, leave it `planned`; the next run will build it.

## Post format per type (all approved by the owner on 2026-11-09 — every post is a carousel ending with the CTA slide)

| type | format | how to render | how to publish |
|---|---|---|---|
| dashboard | **4 slides**: 1 full screen, 2 left half, 3 right half, 4 CTA | `python3 tools/carousel.py designs/<dir> dashboard posts/<YYYY-MM>/<slot-id>-<slug>` → `-1.jpg … -4.jpg` | `create_carousel_post` with all URLs in order |
| app | **5 slides**: 1 hand holding phone, 2 description (UPPERCASE, key phrases bold) + the app's nav bar enlarged, 3 typography, 4 colors, 5 CTA | `python3 tools/carousel.py designs/<dir> app posts/<YYYY-MM>/<slot-id>-<slug>` → `-1.jpg … -5.jpg` | `create_carousel_post` with all URLs in order |
| website | **5–10 slides**: 1 whole home page in two columns, 2 top of page large, 3+ whole page rotated 90° in equal bands ending on the footer (max 7), last CTA | `python3 tools/carousel.py designs/<dir> website posts/<YYYY-MM>/<slot-id>-<slug>` → `-1.jpg … -N.jpg` | `create_carousel_post` with all URLs in order (max 10) |

The CTA slide is fixed (tools/carousel.py `cta_slide`): Abir Hasan Rakib · UI/UX Designer, "Open for new projects", WhatsApp +880 1730 402 994, Email abirhasanrakib92@gmail.com, @abirhasanrakib_, Save for later. Never change it unless the owner asks.
Keep website pages 5000–7000px tall so slide 1 has no blank band and the rotated part fits in 7 slides. Store slide paths in the slot as `images` (list) and leave `image` null.

App designs must include these in `<head>` (they feed slides 2–4), and the bottom nav bar must have class `tab` or attribute `data-nav`:
```
<meta name="app-name" content="Habit Tracker">
<meta name="app-desc" content="One or two sentences about what the app lets people do, with 2 **key phrases** in double asterisks.">
<meta name="fonts" content="<font family from assets/fonts.css>|One sentence on why this typeface fits the product.">
<meta name="palette" content="#HEX:Name|#HEX:Name|#HEX:Name|#HEX:Name|#HEX:Name|#HEX:Name">   (exactly 6, the real colors used)
```

## Designing a post

Folder: `designs/<slot-id>-<short-slug>/screen.html` (+ any images it uses). Output: the carousel slides
`posts/<YYYY-MM>/<slot-id>-<short-slug>-1.jpg … -N.jpg`, made with

```
python3 tools/carousel.py designs/<dir> <app|dashboard|website> posts/<YYYY-MM>/<slot-id>-<short-slug>
```

Canvas for every post: 1080×1350, flat `#EEEEEE` studio background; carousel.py adds the approved brand chrome.
The renderer handles the mockup; you only design the screen.

| type | screen.html size | mockup the renderer adds |
|---|---|---|
| app | 393×852 (iPhone) | hand holding the phone (the owner's reference photo) |
| dashboard | 1440×960, no scroll | one light browser window, centered. **Single screen only: no zoom card, no popup, no modal, no floating overlay** |
| website | 1440 wide, 5000–7000 tall | carousel (see table above): two-column overview, top of page large, rotated page bands |

Conventions:
- `<link rel="stylesheet" href="../../assets/fonts.css">` — families: Inter Tight, Geist, Manrope, Plus Jakarta Sans, DM Sans,
  Figtree, Onest, Outfit, Sora, Urbanist, Space Grotesk, Bricolage Grotesque, Instrument Sans, Instrument Serif, Fraunces, JetBrains Mono.
  Rotate fonts between posts.
- Icons: `{{icon:<lucide-name>:<size>:<#hex>[:<stroke>]}}` (names from `node_modules/lucide-static/icons`).
- Dashboard: `<meta name="mock-url" content="app.<brand>.com">` for the address bar. Design the full screen only; never add popups, modals, dropdowns, toasts or tooltips floating over the layout (a small chart hover label inside a chart is fine).
- App: draw the iOS status bar (9:41, signal, wifi, battery) at the top 54px and the home indicator at the bottom; the island comes from the photo.

### Quality bar (check every one before rendering)

- **Light UI only.** Off-white or white surfaces, one or two accent colors from the slot's palette hint.
- **Real content, never lorem ipsum.** Believable names, numbers that add up, dates around the posting date,
  realistic product copy. Totals must match their parts.
- **Top-notch craft:** clear hierarchy, 8px spacing rhythm, consistent radii, tabular numbers, no empty dead zones,
  nothing clipped or overflowing, no text smaller than 11px at design size.
- Charts are hand-built SVG with axes, gridlines and a highlighted point or tooltip.
- **No real brands or logos** (fictional brand from the calendar; plain-text mentions of common tools are fine),
  no real people's photos, no copyrighted characters.
- People: always real photo avatars (see Dashboard style standard; avatar bank in `assets/avatars/`), never initials. For other photos (hero image, product), generate them with Figma `generate_image`
  in file `IVWMA2qO8U4XdLphCuds1y` (owner drafts), save it in the design folder, and use it. AI credits are limited:
  at most 2 images per app/dashboard post and 3–4 per website post (see Design style standard). If generation fails, retry once with a simpler prompt before designing without photos.
- After rendering, **open the JPG and look at it**. Fix anything off, re-render, look again.
- **Owner's style order (2026-11-13, after the Basketly post was rejected):** never use emoji, flag emoji or cartoon/clip-art
  imagery anywhere in a design (no emoji as product images, icons or badges). Use Lucide icons, text badges, or **realistic photos**
  (Figma `generate_image`; crop one photo several ways with `background-position` for product thumbnails).
  App designs must look premium and unique: neat, clean, gorgeous, with **glassmorphism** (frosted `backdrop-filter` cards and
  pills over a real photo) as the default look. Reference picks the owner liked: `designs/2026-11-13-pm-lumea-pilates-app`,
  `designs/2026-11-13-pm-solace-stays-app`, `designs/2026-11-13-pm-mossa-grocery-app`.
- Figma file for generated photos: `IVWMA2qO8U4XdLphCuds1y` ("IG app photos", owner's drafts); the old file `BJu214JqvIholCIGac8Bbo` is not editable.


## Design style standard (owner's order, 2026-11-14 — applies to EVERY post from now on)

The owner rejected the first Voltway website (flat, text-heavy, no photos, blank band in the right column of slide 1)
and gave six references: `reference/website-style/ref-1.jpg … ref-6.jpg` (DermaCare, Archi Studio, Terra Estate,
NOVA, Formo Academy, Cosmico). **Open and study them before designing.** Approved example in this style:
`designs/2026-11-14-pm-voltway-ev-website`. Every post must look like it belongs next to these: unique, premium, best-in-class UI.

What the references have in common (do all of it):
- **Photo-led.** Large realistic photos carry the page: hero photo, photo cards, a full-width photo banner, a portrait
  for testimonials/team. Generate 3–4 photos per website post with Figma `generate_image` (file `IVWMA2qO8U4XdLphCuds1y`)
  and reuse them with different crops (`background-position`). Never ship a website without photos.
- **Hero as a composed block**, not text on a blank page: a dark or tinted rounded card with the headline + CTA beside a big
  photo, with glass overlay cards on the photo (a key number, a live status card, a small badge).
- **Typography with contrast:** a clean grotesk for headings (tight tracking, 56–90px) with **one or two accent words in an italic
  serif** (Instrument Serif / Fraunces) or in the accent color. Small uppercase eyebrows or pill labels ("Who it's for").
- **Bento sections:** 3-up photo cards with glass captions and arrow buttons; a dark card mixed into light rows;
  numbered 01–04 accordion with the active item filled dark; stat cards; pricing with the hero plan in the dark brand color.
- **Two-tone palette:** warm off-white page + one deep brand color (forest, charcoal, terracotta, navy) + one bright accent
  (lime, orange, blue). Rounded 24–32px containers, soft borders, generous 120–150px gaps between sections.
- **Ending:** a bold accent-color CTA band, then a dark footer with link columns, newsletter field and a **giant brand wordmark**.
- **Page height 5000–6500px** (carousel.py refuses under 4900) so slide 1's right column starts with content, never blank.
- Check slide 1 like the owner will on the phone: both columns full, no empty band, nothing clipped, words not orphaned
  (force line breaks in headings when a single word would wrap alone).
- Same quality bar for apps and dashboards: real photos where they make sense, glass, deep brand color + bright accent, bento layout.


## Dashboard style standard (owner's order, 2026-11-14 — every dashboard from now on)

The owner rejected the earlier dashboard look and gave 14 references: `reference/dashboard-style/ref-01.jpg … ref-14.jpg`
(Payno, Noteflow, Atur HR, Veloxa fleet, HR portal, Task.iq, nursing, MediCore, Monetra, Shopeers, Finexy, Salezy, property finance).
**Open and study them before designing.** Approved example: `designs/2026-11-15-pm-ledgerly-revenue-dashboard`.
Every dashboard must look like a professional product designer made it, and each one must be unique (new layout skeleton,
new hero component, new chart mix, new palette) so no two posts look alike.

- **Images go where images belong. Never put initials or text in an image slot.** Profile/user avatars, team stacks,
  customer/patient/driver rows, doctor lists, contact cards and "send money" recipients all use real photos.
  Use the avatar bank in `assets/avatars/` (amara, rohan, mei, daniel, sofia, karim, olivia, kenji, marcus; copy the
  files into the design folder). When a design needs a product/vehicle/property/hero photo, generate it with Figma
  `generate_image`; for more faces, generate one 3x3 headshot grid and crop it (one credit, nine avatars), then add them to the bank.
- **Structure:** soft tinted canvas (#F3F2F8, #EEF0EC …), white cards with 20–24px radius and 16px gutters,
  a pill top nav (dark active pill) or a slim icon rail, round icon buttons, user pill with photo + name + role.
- **Greeting header** ("Good evening, Sofia" + one sentence with bold real numbers) with actions on the right
  (date range pill, Export, a primary or AI button, team avatar stack).
- **One hero card** in the deep brand color or a soft gradient/glass (big number 48–56px, delta pill, mini breakdown),
  balanced by KPI tiles where one tile is filled with the accent color.
- **Charts that designers save:** highlighted bar with a dark tooltip and hatched/muted other bars, segmented gauges,
  waterfall/bridge, cohort heatmap, dot matrix, timeline with avatar chips. Hand-built SVG, real axes, numbers that add up.
- **Lists/tables** with photo, name + secondary line, amount, and colored status pills.
- Fill the full 1440×960 with no dead space and nothing clipped: check the bottom row and every card edge on slides 2 and 3.


## Owner's feedback, 2026-11-18 (applies from now on)

- **Dashboard carousel (owner, 2026-11-18, replaces earlier rules):** slide 1 = full screen WITH the brand chrome
  ("Designed by" bar + WhatsApp pill); slide 2 = exactly the left half of the window, slide 3 = exactly the right half,
  cut at the window midline (design x=720), with NO brand chrome (same look as the approved 2026-11-09 Carewell post).
  Lay dashboards out as two 688px halves (24–712 and 728–1416, 16px gutter at x=712–728) so no card crosses the midline.
  Example: `designs/2026-11-19-am-sentinel-pay-fraud-dashboard`.
- **Websites must not all look the same.** The dark hero card + stat row + bento + 01–04 accordion + 3 pricing cards +
  dark footer with giant wordmark has been used enough. Each website picks a different skeleton (e.g. editorial serif
  layout, full-bleed photo hero with the product UI on it, arch/shaped photos, pricing as a comparison table, light footer).
  Example of the new direction: `designs/2026-11-19-pm-roomcraft-ai-interior-website`.


## Brand chrome + mockup shadow (approved by the owner 2026-11-14 — on every post from 2026-11-15)

Every design slide (not the CTA slide, and not dashboard slides 2–3, see the 2026-11-18 feedback) carries the owner's chrome, added automatically by tools/carousel.py:
a top pill with his photo (`assets/brand/abir.jpg`), "Designed by / Abir Hasan *Rakib*", heart/comment/share icons and
"SAVE for LATER" + bookmark on EVERY post type; the WhatsApp pill (+880 1730 402 994) at the bottom goes on
**dashboards only** (owner, 2026-11-14) — app and website slides get the top bar only. Layouts leave room for it
(dashboard halves pan from each edge, website columns/bands sit between the bars, app slides shift/scale down).
Mockup shadows are deliberately faint (owner: the old shadow was too heavy): 1px hairline + a soft, low-opacity drop.
Do not darken them again. If the owner sends a sharper profile photo, replace `assets/brand/abir.jpg`.


## Growth rules (owner's standing order: every post should aim to go viral)

Do all of this on **every** post. Nothing here may break the locked format.

### 1. Research before designing (WebSearch, 2–4 searches)
- What is trending right now in UI for this niche and type (e.g. "dashboard UI trends 2026", "<niche> app design inspiration")?
  Use it to pick a fresh, scroll-stopping angle: bold hero number, unusual chart, striking accent, a clever detail.
- The design must earn **saves and shares**: show something useful a designer would want to keep
  (a smart layout pattern, a well-solved component, realistic data), not just pretty filler.

### 2. Hashtag research (WebSearch every time, never copy last post's set)
- **Hard limit: 5 hashtags.** Instagram caps posts at 5 (rolled out from Dec 2025); more can fail or be cut.
- Search what tags designers actively use for this exact niche/type right now, then pick:
  1 broad design tag (`#uidesign`, `#uxdesign` or `#uiux`), 2 type tags (e.g. `#dashboarddesign`, `#landingpage`, `#mobileappdesign`),
  2 niche tags (e.g. `#healthtech`, `#fintechdesign`).
- Never use generic or spammy tags: `#explore #viral #reels #fyp #instagood #likeforlike`.
- Put the hashtags at the end of the caption.

### 3. Hook first, then SEO (owner's standing order: every post needs a hook)
Only the first line shows before "more", so **line 1 is always the hook**. Every caption, every platform.
- **Line 1 = hook**, under ~90 characters. It must stop the scroll on its own.
  Hook formulas that work for design content (rotate them, never reuse the same hook twice):
  - Bold opinion: “Your habit app shouldn't make you feel guilty.”
  - Surprising number: “68% of support chats, solved without a human.”
  - Relatable pain: “Nobody started a business to do bookkeeping.”
  - Reframe: “Range anxiety is really information anxiety.”
  - Mini-story / question the user would ask: “I asked my budget app ‘can I afford Japan?’ and it answered.”
  - Contrast: “Every AI product says ‘automate’. This one shows how.”
  Avoid weak openers: “Here's my new design”, “Check this out”, “New shot”, “UI design for…”.
- **Line 2 = plain searchable description** with the main keywords (Instagram search and Google index it), e.g.
  `Hospital dashboard UI design: bed capacity & patient flow`.
- 1–2 short sentences on the design decisions.
- A save or share prompt, e.g. `Save this for your next dashboard project` or `Send this to a dev who'd build it`.
- A question to drive comments.
- Blank line, then the 5 hashtags. Total under 2,200 characters, English.
- LinkedIn captions follow the same rule: the first line is the hook.
- **No emojis anywhere** (captions, LinkedIn posts). Comment replies are the one exception, see section 4. The owner wants writing that reads like a person, not like AI. Also avoid other AI tells: no "Let's dive in", no "game-changer", no stacked buzzwords.

### 4. Comment replies (every run, after publishing)
- Read comments on posts from the last 3 days with Windsor `get_data` (connector `instagram`; call `get_fields` first to find
  the comment fields; widen the date range if empty).
- Reply to every new genuine comment with `reply_to_comment` using a very short reply in the owner's style (owner's order,
  2026-11-14), e.g. "Appreciate it! ❤️", "Thanks! ❤️", "Thank You! 🙌". Rotate these so neighbouring replies are not identical;
  one emoji (❤️ or 🙌) at the end is fine. No long replies and no follow-up questions. Exception: hiring or pricing questions get
  a short thank-you plus WhatsApp +8801730402994 or abirhasanrakib92@gmail.com. Never reply twice to the same comment.
- Hide obvious spam/scam/bot comments with `hide_comment` (never delete).
- Note replied comment ids in `calendar.json` under the slot (`replied_comment_ids`) so later runs skip them.

### 5. Learn from results
- Once a week (Monday morning run), read reach/saves/shares for the last 7 posts with Windsor `get_data` and add a 3-line note
  to `growth-notes.md`: which niche/style did best and what to do more of. Use those notes when designing.

## Publishing

1. Commit the design folder + JPG, `git push origin main`.
2. Public URL: `https://raw.githubusercontent.com/abirhasanrakib92-tech/instagram-posts/main/<path to jpg>`.
   Confirm it returns HTTP 200 and `image/jpeg` before posting.
3. Post with Windsor.ai: `execute_action`, connector `instagram`, account `17841402898456368`:
   every post → action `create_carousel_post`, params `{image_urls: [all slides in order], caption}`.
   Verify every URL returns HTTP 200 first.
4. Caption: follow **Growth rules** below (hook on line 1, keywords on line 2, save/share prompt, question, max 5 researched hashtags).
5. Save the caption, image path and `media_id` in the slot, set `posted`, commit, push.

Commit messages end with:

```
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
```

## If something breaks

- Windsor error or token expired: do not retry more than once; leave the slot `ready` and say what failed.
- GitHub push refused: the repo must be attached to the session with push access (owner `abirhasanrakib92-tech`, repo `instagram-posts`).
- Never post anything that is not this slot's image, and never delete or edit existing posts or comments.
