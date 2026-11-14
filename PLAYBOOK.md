# Instagram posting playbook — @abirhasanrakib_

Every scheduled run follows this file. It covers what to post, how to design it, and how to publish it.

## Locked format (approved by the owner on 2026-11-09 — do not change)

Match these approved posts exactly in presentation; only the design inside the screen changes:
- App → `reference/app-approved-1.jpg` … `-5.jpg` (**5-slide carousel**: hand holding phone, description + nav bar, typography, colors, CTA)
- Dashboard → `posts/2026-11/2026-11-09-pm-hospital-ops-dashboard-1.jpg` … `-4.jpg` (**carousel**: full window, left half, right half, CTA; no popup/zoom card)
- Website → `posts/2026-11/2026-11-10-am-meeting-notes-website-1.jpg` … `-8.jpg` (**carousel**: whole home page in two columns, top of page large, the whole page rotated 90° in equal bands through the footer, CTA)

Always: 1080×1350, `#EEEEEE` background, light UI, no CTA bar or "Designed by" strip on the design slides; the only CTA is the fixed last slide.
Do not edit `tools/render.py` or the mockup assets unless the owner asks.

## The schedule

- Two posts a day, Asia/Dhaka time: **morning 08:37** (`am`) and **night 20:39** (`pm`).
- Rotation never breaks: **app → dashboard → website → app → …** across consecutive slots.
  On a 3-column Instagram grid this keeps each column one type, which is the look the owner wants.
- `calendar.json` lists every slot from 2026-11-09 pm to 2026-12-09 pm: type, niche, brand name, palette hint, status.
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
Keep website pages 4500–7000px tall so the rotated part fits in 7 slides. Store slide paths in the slot as `images` (list) and leave `image` null.

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

Canvas for every post: 1080×1350, flat `#EEEEEE` studio background, **no CTA bar, no "Designed by", no logo strip**.
The renderer handles the mockup; you only design the screen.

| type | screen.html size | mockup the renderer adds |
|---|---|---|
| app | 393×852 (iPhone) | hand holding the phone (the owner's reference photo) |
| dashboard | 1440×960, no scroll | one light browser window, centered. **Single screen only: no zoom card, no popup, no modal, no floating overlay** |
| website | 1440 wide, 4500–7000 tall | carousel (see table above): two-column overview, top of page large, rotated page bands |

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
- People: initials avatars by default. For a photo (avatar, hero image), generate it with Figma `generate_image`
  in file `IVWMA2qO8U4XdLphCuds1y` (owner drafts), save it in the design folder, and use it. AI credits are limited:
  at most 2 images per post. If generation fails, design without photos.
- After rendering, **open the JPG and look at it**. Fix anything off, re-render, look again.
- **Owner's style order (2026-11-13, after the Basketly post was rejected):** never use emoji, flag emoji or cartoon/clip-art
  imagery anywhere in a design (no emoji as product images, icons or badges). Use Lucide icons, text badges, or **realistic photos**
  (Figma `generate_image`; crop one photo several ways with `background-position` for product thumbnails).
  App designs must look premium and unique: neat, clean, gorgeous, with **glassmorphism** (frosted `backdrop-filter` cards and
  pills over a real photo) as the default look. Reference picks the owner liked: `designs/2026-11-13-pm-lumea-pilates-app`,
  `designs/2026-11-13-pm-solace-stays-app`, `designs/2026-11-13-pm-mossa-grocery-app`.
- Figma file for generated photos: `IVWMA2qO8U4XdLphCuds1y` ("IG app photos", owner's drafts); the old file `BJu214JqvIholCIGac8Bbo` is not editable.


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
