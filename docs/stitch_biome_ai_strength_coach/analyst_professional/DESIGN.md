---
name: Analyst Professional
colors:
  surface: '#19120a'
  surface-dim: '#19120a'
  surface-bright: '#41382e'
  surface-container-lowest: '#140d06'
  surface-container-low: '#221a12'
  surface-container: '#261e15'
  surface-container-high: '#31281f'
  surface-container-highest: '#3c3329'
  on-surface: '#f0e0d1'
  on-surface-variant: '#d8c3ad'
  inverse-surface: '#f0e0d1'
  inverse-on-surface: '#382f25'
  outline: '#a08e7a'
  outline-variant: '#534434'
  surface-tint: '#ffb95f'
  primary: '#ffc174'
  on-primary: '#472a00'
  primary-container: '#f59e0b'
  on-primary-container: '#613b00'
  inverse-primary: '#855300'
  secondary: '#adc6ff'
  on-secondary: '#002e6a'
  secondary-container: '#0566d9'
  on-secondary-container: '#e6ecff'
  tertiary: '#8fd5ff'
  on-tertiary: '#00344a'
  tertiary-container: '#1abdff'
  on-tertiary-container: '#004966'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#ffddb8'
  primary-fixed-dim: '#ffb95f'
  on-primary-fixed: '#2a1700'
  on-primary-fixed-variant: '#653e00'
  secondary-fixed: '#d8e2ff'
  secondary-fixed-dim: '#adc6ff'
  on-secondary-fixed: '#001a42'
  on-secondary-fixed-variant: '#004395'
  tertiary-fixed: '#c5e7ff'
  tertiary-fixed-dim: '#7fd0ff'
  on-tertiary-fixed: '#001e2d'
  on-tertiary-fixed-variant: '#004c6a'
  background: '#19120a'
  on-background: '#f0e0d1'
  surface-variant: '#3c3329'
typography:
  display-xl:
    fontFamily: Inter
    fontSize: 36px
    fontWeight: '600'
    lineHeight: '1.2'
    letterSpacing: -0.02em
  heading-lg:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: '1.3'
    letterSpacing: -0.01em
  heading-md:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '500'
    lineHeight: '1.4'
    letterSpacing: -0.01em
  body-base:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: '1.6'
    letterSpacing: '0'
  body-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: '1.5'
    letterSpacing: '0'
  data-metric:
    fontFamily: Space Grotesk
    fontSize: 28px
    fontWeight: '500'
    lineHeight: '1.1'
    letterSpacing: -0.03em
  label-caps:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '600'
    lineHeight: '1'
    letterSpacing: 0.05em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 48px
  section: 64px
---

## Brand & Style

The brand personality is rooted in elite performance, precision, and stoic discipline. It avoids the typical "fitness motivation" tropes—neon splashes and high-energy imagery—in favor of a high-fidelity, data-centric interface. This design system evokes the feeling of a high-end flight deck or a professional sports telemetry suite.

The visual style is a blend of **Minimalism** and **Corporate Modernism**, heavily influenced by the "Linear" aesthetic. It relies on mathematical precision, generous whitespace, and a restrained use of color to direct focus toward data and progress. The emotional response is one of calm authority; the AI is not a cheerleader, but a specialized strength consultant providing objective, actionable insights.

## Colors

This design system utilizes a deep, monochromatic foundation to create a "cinematic dark mode" environment. The primary background is near-black to reduce eye strain during deep analysis sessions. 

The **Amber (#f59e0b)** accent is used surgically; it is the sole "active" signal in the UI, reserved for primary calls to action, active navigation states, and critical highlights. Status colors (Green, Red, Blue) are strictly functional, used only for trend indicators, progress bars, and system alerts to maintain the professional, analytical tone. Gradients are avoided entirely, except for very subtle 1% opacity overlays on large surfaces to prevent flat-panel fatigue.

## Typography

The typography strategy prioritizes density and clarity. **Inter** serves as the workhorse for all UI elements, providing a neutral, geometric foundation that feels institutional and reliable. 

For technical data displays—such as weight loads, rep counts, and volume metrics—**Space Grotesk** is introduced. Its slightly more technical, futuristic apertures reinforce the "AI coach" narrative. Headings should utilize tighter letter spacing to maintain a premium "editorial" feel, while body text uses standard spacing for maximum legibility against the dark background.

## Layout & Spacing

The application follows a **Fixed Grid** model for the primary content area to ensure a consistent data-reading experience across various desktop monitor sizes. 

The **240px persistent left sidebar** provides immediate access to high-level navigation, acting as the structural anchor. The main content area is capped at **1200px** and centered, creating balanced "gutters" on ultra-wide displays that enhance the cinematic feel. A rigorous 8px baseline grid is used for all internal component spacing, ensuring that cards, inputs, and icons align with mathematical precision.

## Elevation & Depth

In this design system, depth is communicated through **Tonal Layering** and **Low-contrast Outlines** rather than traditional shadows. 

The background starts at the deepest level (#0a0a0a). Content containers, such as cards and sidebars, are elevated one step to #141414. To define these edges, a subtle 1px border (#262626) is applied. This creates a "flat-depth" look where objects appear to be seated in the same plane but distinguished by value. On the rare occasion a modal is required, a backdrop blur of 8px is used to maintain the glass-like cinematic quality without breaking the dark aesthetic.

## Shapes

The shape language is disciplined and consistent. A **Soft (0.5rem / 8px)** corner radius is applied to all primary containers, buttons, and input fields. This radius is large enough to feel modern and premium, but sharp enough to maintain a professional "analyst" edge. Small components like tags or chips follow a slightly reduced radius (4px) to ensure they do not appear too "bubbly" or informal.

## Components

### Buttons
Primary buttons use a solid **Amber (#f59e0b)** background with black text for maximum contrast. Secondary buttons use a ghost style: a #262626 border with #fafafa text. All buttons feature an 8px radius and a height of 40px for a standard desktop feel.

### Cards
Cards are the primary organizational unit. They use the #141414 surface color and a #262626 border. Padding is generous (typically 24px) to emphasize the "premium whitespace" philosophy.

### Input Fields
Inputs are dark and recessed. Use the #0a0a0a background (matching the page) with a #262626 border. On focus, the border transitions to Amber. Labels are always positioned above the input using the `label-caps` typography style.

### Data Displays (Analyst Aesthetic)
Metrics should be grouped in "Metric Clusters." Use Lucide icons (size 18px) in muted gray next to Space Grotesk values. Progress is visualized with thin, 4px-high progress bars using the Status Green color.

### Sidebar
The sidebar is a solid #0a0a0a or #141414 surface with a right-hand border separator. Nav items use 14px Inter text. The active state is indicated by an Amber vertical pillar (2px wide) on the far left of the nav item.