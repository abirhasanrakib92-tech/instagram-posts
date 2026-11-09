# Instagram posting playbook — @abirhasanrakib_

Every scheduled run follows this file. It covers what to post, how to design it, and how to publish it.

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
3. If the slot is `planned`, design and render it now (see below), push, and mark it `ready`.
4. Post it (see Publishing). Record `media_id`, set `posted`, commit and push.
5. Prepare the **next** slot the same way (design → render → push → `ready`), so it is waiting before its time.
   If anything about the next one fails, leave it `planned`; the next run will build it.

## Designing a post

Folder: `designs/<slot-id>-<short-slug>/screen.html` (+ any images it uses). Output:
`posts/<YYYY-MM>/<slot-id>-<short-slug>.jpg`, made with

```
python3 tools/render.py designs/<dir> <app|dashboard|website> posts/<YYYY-MM>/<file>.jpg
```

Canvas for every post: 1080×1350, flat `#EEEEEE` studio background, **no CTA bar, no "Designed by", no logo strip**.
The renderer handles the mockup; you only design the screen.

| type | screen.html size | mockup the renderer adds |
|---|---|---|
| app | 393×852 (iPhone) | hand holding the phone (the owner's reference photo) |
| dashboard | 1440×960, no scroll | light browser window, centered; plus a zoom card of the element with `data-zoom` |
| website | 1440 wide, 4500–8000 tall | two long cards: top of the page in front, lower sections peeking behind |

Conventions:
- `<link rel="stylesheet" href="../../assets/fonts.css">` — families: Inter Tight, Geist, Manrope, Plus Jakarta Sans, DM Sans,
  Figtree, Onest, Outfit, Sora, Urbanist, Space Grotesk, Bricolage Grotesque, Instrument Sans, Instrument Serif, Fraunces, JetBrains Mono.
  Rotate fonts between posts.
- Icons: `{{icon:<lucide-name>:<size>:<#hex>[:<stroke>]}}` (names from `node_modules/lucide-static/icons`).
- Dashboard: `<meta name="mock-url" content="app.<brand>.com">` for the address bar; put `data-zoom` on the one card worth showing up close.
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
  in file `BJu214JqvIholCIGac8Bbo` (team "FB Post"), save it in the design folder, and use it. AI credits are limited:
  at most 2 images per post. If generation fails, design without photos.
- After rendering, **open the JPG and look at it**. Fix anything off, re-render, look again.

## Publishing

1. Commit the design folder + JPG, `git push origin main`.
2. Public URL: `https://raw.githubusercontent.com/abirhasanrakib92-tech/instagram-posts/main/<path to jpg>`.
   Confirm it returns HTTP 200 and `image/jpeg` before posting.
3. Post with Windsor.ai: `execute_action`, connector `instagram`, account `17841402898456368`,
   action `create_image_post`, params `{image_url, caption}`.
4. Caption (English, under 2,200 characters):
   - Hook line about the problem the design solves (one line, one emoji max)
   - 1–2 short sentences on the design decisions in this screen
   - A question to drive comments, ending with 👇
   - A blank line, then 8–12 hashtags: always `#uidesign #uxdesign #uiux #productdesign`, plus type tags
     (`#mobileappdesign #appdesign` / `#dashboarddesign #saasdesign #webapp` / `#webdesign #landingpage #websitedesign`)
     and 2–3 niche tags.
5. Save the caption, image path and `media_id` in the slot, set `posted`, commit, push.

Commit messages end with:

```
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
```

## If something breaks

- Windsor error or token expired: do not retry more than once; leave the slot `ready` and say what failed.
- GitHub push refused: the repo must be attached to the session with push access (owner `abirhasanrakib92-tech`, repo `instagram-posts`).
- Never post anything that is not this slot's image, and never delete or edit existing posts or comments.
