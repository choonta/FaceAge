# FaceAge — DESIGN.md

> Upload this file to [Claude Design](https://claude.ai/design) to scaffold a complete clinical-scientific design system in one shot: color tokens, typography scale, components, and a working UI kit.

---

## 1. Visual Theme & Atmosphere

FaceAge is a peer-reviewed deep learning system published in *The Lancet Digital Health*, developed at Harvard/BWH. Every design decision should signal **clinical precision, scientific authority, and data integrity** — not consumer polish.

The aesthetic is institutional-minimal: crisp white canvas, cool neutral surfaces, and a single restrained blue accent that carries all interactive weight. Data visualizations and model output numbers are the heroes; decoration is the enemy. Think medical instrument UI meets academic paper layout — exact, quiet, trustworthy.

Density is intentional. Clinicians and researchers scan tables and metrics, not marketing copy. Generous whitespace structures the page but never wastes it.

---

## 2. Color Palette & Roles

| Token | Hex | Role |
|---|---|---|
| `--color-bg` | `#FFFFFF` | Page background, primary canvas |
| `--color-surface` | `#F4F6F9` | Cards, panels, sidebar backgrounds |
| `--color-surface-raised` | `#EBEEF3` | Hover states, secondary surfaces |
| `--color-border` | `#D1D9E0` | Dividers, input outlines, table rules |
| `--color-border-subtle` | `#E8ECF1` | Subtle separators, zebra rows |
| `--color-primary` | `#1A4A8A` | Primary CTAs, active nav, links, focus rings |
| `--color-primary-hover` | `#153D75` | Primary hover / pressed state |
| `--color-primary-light` | `#E8F0FA` | Primary tint for badges, highlights, selected rows |
| `--color-accent` | `#C94A2E` | FaceAge score callouts, critical flags, age-delta indicators |
| `--color-accent-light` | `#FBEAE7` | Accent tint background for alert surfaces |
| `--color-success` | `#2A6B42` | Within-normal-range indicators, passing QA status |
| `--color-success-light` | `#E6F4EC` | Success tint backgrounds |
| `--color-warning` | `#8A5A00` | Outlier flags, attention-required states |
| `--color-warning-light` | `#FDF3DC` | Warning tint backgrounds |
| `--color-text-primary` | `#0D1A26` | Body copy, table data, headings |
| `--color-text-secondary` | `#4A5C6B` | Labels, captions, metadata, axis labels |
| `--color-text-disabled` | `#9AABB8` | Placeholder text, inactive controls |
| `--color-text-inverse` | `#FFFFFF` | Text on primary / dark surfaces |

**Usage rules:**
- `--color-primary` is the only interactive color. Never use accent, success, or warning for links or buttons.
- `--color-accent` (`#C94A2E`) is reserved exclusively for biological age output values and delta indicators (FaceAge − chronological age). Do not use it for decorative purposes.
- Background is always `#FFFFFF`. Never use colored or gradient backgrounds on the main canvas.
- Use surface colors only for structural elements (cards, panels) — not as decorative fills.

---

## 3. Typography Rules

**Primary typeface:** Inter (Google Fonts)  
**Monospace / data output:** JetBrains Mono (Google Fonts)

| Style | Family | Size | Weight | Line-height | Usage |
|---|---|---|---|---|---|
| Display | Inter | 2.25rem (36px) | 700 | 1.2 | Page titles, hero section headings |
| Heading 1 | Inter | 1.75rem (28px) | 600 | 1.3 | Section headings |
| Heading 2 | Inter | 1.375rem (22px) | 600 | 1.35 | Sub-section headings, card titles |
| Heading 3 | Inter | 1.125rem (18px) | 600 | 1.4 | Panel headers, sidebar labels |
| Body | Inter | 1rem (16px) | 400 | 1.6 | Primary body copy, descriptions |
| Body Small | Inter | 0.875rem (14px) | 400 | 1.55 | Table data, form labels, secondary text |
| Caption | Inter | 0.75rem (12px) | 400 | 1.5 | Timestamps, footnotes, axis labels |
| Data Output | JetBrains Mono | 1.5rem (24px) | 500 | 1.2 | FaceAge score display, model output values |
| Code | JetBrains Mono | 0.875rem (14px) | 400 | 1.6 | Inline code, CLI output, config snippets |
| Label / Tag | Inter | 0.6875rem (11px) | 600 | 1.0 | Status badges, column headers (uppercase) |

**Rules:**
- Column headers and badge labels use `text-transform: uppercase; letter-spacing: 0.06em`.
- The FaceAge output score uses `JetBrains Mono` at 24px weight 500 with `--color-accent` to make it instantly scannable.
- Never use font weights above 700 or below 400.
- Body line-height never below 1.55 — readability at medical information density.

---

## 4. Component Stylings

### Buttons

```
Primary:
  background: var(--color-primary)
  color: var(--color-text-inverse)
  padding: 10px 20px
  border-radius: 6px
  font: Inter 14px weight-500
  hover: background var(--color-primary-hover)
  focus: outline 2px solid var(--color-primary), outline-offset 2px

Secondary (outline):
  background: transparent
  color: var(--color-primary)
  border: 1.5px solid var(--color-primary)
  padding: 9px 19px
  border-radius: 6px
  hover: background var(--color-primary-light)

Ghost:
  background: transparent
  color: var(--color-text-secondary)
  padding: 10px 20px
  border-radius: 6px
  hover: background var(--color-surface-raised), color var(--color-text-primary)

Destructive:
  background: var(--color-accent)
  color: var(--color-text-inverse)
  padding: 10px 20px
  border-radius: 6px
  hover: background #A83B24
```

### Inputs & Form Controls

```
Text input:
  background: var(--color-bg)
  border: 1.5px solid var(--color-border)
  border-radius: 6px
  padding: 9px 12px
  font: Inter 14px
  color: var(--color-text-primary)
  focus: border-color var(--color-primary), box-shadow 0 0 0 3px var(--color-primary-light)
  placeholder: var(--color-text-disabled)

Select:
  Same as text input + chevron icon right-aligned in var(--color-text-secondary)
```

### FaceAge Score Card (primary data component)

```
Container:
  background: var(--color-bg)
  border: 1.5px solid var(--color-border)
  border-radius: 10px
  padding: 24px
  display: flex, flex-direction: column, gap: 8px

Score value:
  font: JetBrains Mono 36px weight-600
  color: var(--color-accent)

Score label:
  font: Inter 12px uppercase weight-600 letter-spacing 0.06em
  color: var(--color-text-secondary)

Delta indicator (FaceAge − chrono age):
  font: JetBrains Mono 14px weight-500
  Positive delta (biologically older): color var(--color-accent)
  Negative delta (biologically younger): color var(--color-success)
  Neutral (±2 yrs): color var(--color-text-secondary)
```

### Data Table

```
Table:
  width: 100%
  border-collapse: collapse
  font: Inter 14px

Header row:
  background: var(--color-surface)
  border-bottom: 2px solid var(--color-border)
  font: Inter 11px uppercase weight-600 letter-spacing 0.06em
  color: var(--color-text-secondary)
  padding: 10px 16px

Data row:
  border-bottom: 1px solid var(--color-border-subtle)
  padding: 12px 16px
  color: var(--color-text-primary)

Hover row:
  background: var(--color-surface)

Zebra (optional):
  Even rows: background var(--color-surface) at 50% opacity
```

### Status Badge

```
Base: display inline-flex, align-items center
      padding: 2px 8px, border-radius: 4px
      font: Inter 11px uppercase weight-600 letter-spacing 0.06em

Pass / Normal:
  background: var(--color-success-light)
  color: var(--color-success)

Flag / Outlier:
  background: var(--color-accent-light)
  color: var(--color-accent)

Pending / Processing:
  background: var(--color-primary-light)
  color: var(--color-primary)

Warning:
  background: var(--color-warning-light)
  color: var(--color-warning)
```

### Alert / Disclaimer Banner

```
background: var(--color-surface)
border-left: 4px solid var(--color-primary)
border-radius: 0 6px 6px 0
padding: 14px 18px
font: Inter 14px
color: var(--color-text-primary)

For warnings: border-left-color var(--color-warning)
For critical: border-left-color var(--color-accent)
```

---

## 5. Layout Principles

- **Base grid:** 8px. All spacing values are multiples of 8 (8, 16, 24, 32, 48, 64, 96).
- **Max content width:** 1200px, centered, horizontal padding 32px desktop / 16px mobile.
- **Primary layout:** Left sidebar (240px fixed) + main content area. Sidebar holds navigation; content holds data panels.
- **Card grid:** 12-column, gutters 24px. Data summary cards span 3 columns; full result tables span 12.
- **Section rhythm:** 48px vertical gap between top-level sections. 24px between sub-sections within a card.
- **Data panels:** Never nest more than two levels of cards. Surface-on-surface with `--color-surface-raised` as inner level.

---

## 6. Depth & Elevation

FaceAge uses two elevation levels only. No heavy drop shadows — clinical UIs imply precision, not decoration.

```
Level 0 (flat):
  Surface distinction via background color change only (bg → surface → surface-raised)
  No shadow

Level 1 (card):
  box-shadow: 0 1px 3px rgba(13, 26, 38, 0.08), 0 1px 2px rgba(13, 26, 38, 0.06)
  Used for: data cards, result panels, modal dialogs

Level 2 (dropdown / tooltip):
  box-shadow: 0 4px 12px rgba(13, 26, 38, 0.12), 0 2px 6px rgba(13, 26, 38, 0.08)
  Used for: dropdown menus, floating tooltips, popovers

Borders replace shadows wherever possible. When in doubt, use a border.
```

---

## 7. Do's and Don'ts

**Do:**
- Use `JetBrains Mono` for all numerical model output (FaceAge scores, MAE values, patient IDs)
- Always show the delta (FaceAge − chronological age) alongside the raw score — this is the clinically meaningful number
- Use left-aligned text in tables for all columns except numerical scores (right-align numbers)
- Place the `--color-accent` FaceAge score prominently at the top of any result card
- Include the disclaimer text on every screen that presents model predictions: *"For research use only. Not intended for clinical care or commercial use."*
- Use `border-radius: 6px` consistently for inputs, cards, and buttons — rounded but not playful
- Prefer tables over charts for raw prediction outputs; use charts only for aggregate distributions or survival curves

**Don't:**
- Never use gradients, glassmorphism, or animated backgrounds
- Never color-code rows purely by FaceAge value — use the delta badge instead to show relative biological age
- Never omit confidence intervals or uncertainty indicators when displaying aggregate statistics
- Never use accent red (`--color-accent`) for generic error states — reserve it exclusively for age output
- Don't use more than 3 typeface sizes on a single card
- Don't place model output scores in body copy inline — always present them in a dedicated score card component
- Never use `font-weight: 800` or `900` — Inter at 700 is the maximum permitted weight
- Don't auto-play animations or transitions longer than 200ms — medical users need stable, scannable interfaces

---

## 8. Responsive Behavior

| Breakpoint | Width | Layout behavior |
|---|---|---|
| Mobile | < 640px | Single column, sidebar collapses to bottom nav bar, tables scroll horizontally |
| Tablet | 640px – 1024px | Sidebar collapses to icon-only rail (48px), card grid switches to 6-column |
| Desktop | 1024px – 1280px | Full sidebar (240px) + 12-col content grid |
| Wide | > 1280px | Max-width 1200px centered, sidebar fixed |

- Touch targets: minimum 44×44px for all interactive elements on mobile
- Score cards stack vertically on mobile, single column full-width
- Data tables on mobile: priority columns only (subj_id, faceage, delta); secondary columns hidden with a "show more" toggle
- Font sizes do not scale with viewport — use the fixed scale defined in Typography
- Horizontal scrolling is permitted for data tables only — never for page-level content

---

## 9. Agent Prompt Guide

Reusable prompts for Claude Design once this system is scaffolded. Save these to your `SKILL.md`.

```
# SKILL: FaceAge Design System

system_identity: >
  You are designing for a peer-reviewed clinical deep learning system published in
  The Lancet Digital Health. Every screen must communicate scientific precision and
  institutional trust. Data is the hero. Decoration is the enemy.

prompts:
  result_screen: >
    Build a patient result screen showing: chronological age, FaceAge score in
    JetBrains Mono using --color-accent, biological age delta with directional
    color coding, and a QA status badge. Include the research disclaimer footer.
    Use the FaceAge Score Card component spec.

  cohort_dashboard: >
    Build a cohort analysis dashboard with: summary stat cards (N, mean FaceAge,
    mean delta, MAE), a sortable data table of all subjects, and a distribution
    histogram of FaceAge − chronological age deltas. Follow the 12-column grid,
    8px spacing system, and Level 1 elevation for all cards.

  pipeline_status: >
    Build a pipeline run status screen showing: input folder path, subject count,
    processing progress bar, per-subject status badges (processing / done / failed),
    and estimated time remaining. Use monospace for file paths and numeric counts.

  onboarding: >
    Build the environment setup guide page with: GPU vs CPU path selector tabs,
    numbered setup steps with code blocks (JetBrains Mono), command copy buttons,
    and a verification checklist. Use the Alert component for the disclaimer.
    No gradients, no illustrations — text and code only.
```
