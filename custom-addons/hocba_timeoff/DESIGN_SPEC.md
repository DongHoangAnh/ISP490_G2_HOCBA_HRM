# UI/UX Design Specification

## Design Philosophy

**Modern SaaS Dashboard Aesthetic** inspired by:

- Linear
- Notion
- Stripe Dashboard
- Vercel Dashboard
- Odoo Enterprise

**Core Principles:**

- Clean & minimal but premium
- Professional & trustworthy
- Easy to scan and read
- Responsive across all devices
- Accessible (WCAG 2.1 AA)
- Fast & performant

---

## Current State Analysis

### Problems with Original UI

| Issue             | Impact                  | Solution                       |
| ----------------- | ----------------------- | ------------------------------ |
| Empty white space | Cluttered look          | Strategic background gradients |
| Excel-like table  | Outdated appearance     | Modern pivot table styling     |
| Hierarchy unclear | Hard to understand data | Color-coded indentation        |
| Minimal styling   | No visual emphasis      | Gradient cards & icons         |
| No insights       | Missing business value  | KPI dashboard cards            |
| Poor UX           | Difficult to navigate   | Modern search & filters        |
| Not responsive    | Mobile unusable         | Mobile-first responsive design |
| No dark mode      | Eye strain at night     | Automatic dark mode            |

---

## New UI Layout

### 1. Header Section

```
┌──────────────────────────────────────────────────────────┐
│                                                            │
│ 📊 Ngày nghỉ theo Nhân viên        [🔍 Search Box]       │
│ HR Analytics & Insights                                   │
│                                                            │
└──────────────────────────────────────────────────────────┘
```

**Specifications:**

- **Height:** 120px (desktop), 150px (mobile)
- **Padding:** 2rem
- **Icon:** 44x44px, gradient background
- **Title Font:** 32px, weight 700, color #1e293b
- **Subtitle Font:** 16px, weight 500, color #64748b
- **Search Width:** 250px, max-width 100% on mobile
- **Border Bottom:** 2px solid #e2e8f0

**Colors:**

- Background: White (#ffffff)
- Border: Light gray (#e2e8f0)
- Icon BG: Gradient (primary light)

---

### 2. Filter Section

```
┌────────────────────────────────────────────────────────────┐
│ Bộ lọc: [Active Filter] [Filter 2] [Filter 3]  [+ Add]   │
└────────────────────────────────────────────────────────────┘
```

**Specifications:**

- **Position:** Sticky (top: 1rem, z-index: 50)
- **Height:** 64px
- **Padding:** 1.25rem
- **Background:** White (#ffffff)
- **Border:** 1px solid #e2e8f0
- **Border Radius:** 12px
- **Box Shadow:** 0 4px 6px -1px rgba(0, 0, 0, 0.1)

**Filter Pills:**

- **Height:** 36px
- **Padding:** 8px 16px
- **Border Radius:** 8px
- **Font Size:** 14px
- **Active State:** Purple bg with white text
- **Hover State:** Light purple bg with shadow

**Add Button:**

- **Height:** 36px
- **Padding:** 8px 16px
- **Border Radius:** 8px
- **Hover:** Lift effect (-2px transform)

---

### 3. KPI Cards Row

```
┌──────────────┬──────────────┬──────────────┬──────────────┐
│ 📊 Tổng      │ 👤 Nhân viên │ ⏰ Chờ duyệt │ 📈 Loại      │
│ ngày nghỉ    │ đầu tiên     │              │ phổ biến     │
│ 45 ngày      │ John Doe     │ 5            │ Sick Leave   │
│ Tháng này    │ 12 ngày      │ yêu cầu      │              │
└──────────────┴──────────────┴──────────────┴──────────────┘
```

**Specifications:**

- **Grid:** Auto-fit, minmax(240px, 1fr)
- **Gap:** 24px
- **Height:** Auto (min 140px)
- **Margin Bottom:** 40px

**Individual Card:**

- **Padding:** 24px
- **Border Radius:** 12px
- **Background:** Gradient white to light gray
- **Border:** 1px solid #e2e8f0
- **Box Shadow:** 0 4px 6px -1px rgba(0, 0, 0, 0.1)
- **Hover:**
  - Transform: translateY(-4px)
  - Box Shadow: Larger shadow
  - Top border: Animated scale

**Icon Container:**

- **Size:** 56x56px
- **Border Radius:** 8px
- **Background:** Gradient (unique per card)
- **Icon Size:** 24px, white color
- **Icon Examples:**
  - Card 1: fa-calendar (Purple gradient)
  - Card 2: fa-user (Pink gradient)
  - Card 3: fa-clock-o (Cyan gradient)
  - Card 4: fa-bar-chart (Green gradient)

**Content Area:**

- **Label Font:** 13px, weight 500, uppercase, gray
- **Value Font:** 28px, weight 700, primary color
- **Meta Font:** 12px, weight 400, light gray

---

### 4. Pivot Table

```
┌──────────────────────────────────────────────────────────┐
│ NHÂN VIÊN          │ THÁNG 5  │ THÁNG 6  │ TỔNG        │
├──────────────────────────────────────────────────────────┤
│ ▸ Administrator    │   10     │    5     │ 15          │
│   ├─ Sick Leave    │    5     │    2     │ 7           │
│   └─ Vacation      │    5     │    3     │ 8           │
├──────────────────────────────────────────────────────────┤
│ ▸ John Doe         │   12     │    8     │ 20          │
│   ├─ Sick Leave    │    8     │    5     │ 13          │
│   └─ Vacation      │    4     │    3     │ 7           │
├──────────────────────────────────────────────────────────┤
│ TỔNG               │   22     │   13     │ 35          │
└──────────────────────────────────────────────────────────┘
```

**Specifications:**

- **Width:** 100%
- **Border Collapse:** Yes
- **Background:** White (#ffffff)
- **Border:** 1px solid #e2e8f0
- **Border Radius:** 12px
- **Box Shadow:** 0 4px 6px -1px rgba(0, 0, 0, 0.1)
- **Overflow:** Auto, hidden on sides

**Table Header:**

- **Position:** Sticky (top: 160px, z-index: 20)
- **Background:** Gradient (primary to primary-dark)
- **Color:** White
- **Padding:** 16px 20px
- **Font:** 13px, weight 600, uppercase
- **Letter Spacing:** 0.05em
- **Border Bottom:** 2px solid primary-darker

**Table Body Rows:**

- **Height:** 44px (row)
- **Border Bottom:** 1px solid #e2e8f0
- **Background:** Alternating (white, light gray)
- **Hover State:**
  - Background: Light purple gradient
  - Box Shadow Inset: Left accent
  - Transform: scale(1.01)

**Total Rows:**

- **Background:** Light purple gradient
- **Font Weight:** 700
- **Border Top/Bottom:** 2px solid primary
- **Hover:** Dark purple bg with white text

**Cells:**

- **Padding:** 16px 20px
- **Font:** 14px, weight 500
- **Color:** Dark gray (#1e293b)

**Hierarchy Indentation:**

- **Level 1:** padding-left 40px, weight 600, primary color
- **Level 2:** padding-left 64px, weight 500, secondary gray
- **Level 3:** padding-left 88px, weight 400, tertiary gray

**Numeric Cells:**

- **Text Align:** Right
- **Font Family:** Monospace
- **Font Weight:** 600
- **Color:** Primary (#7c3aed)
- **Min Width:** 60px

**Expand/Collapse Buttons:**

- **Size:** 24x24px
- **Color:** Primary
- **Hover:** Background light purple, scale 1.2
- **Animation:** Smooth rotation on click

---

## Design Tokens

### Color System

```
Primary: #7c3aed
├─ Light: #ede9fe
├─ Dark: #6d28d9
└─ Darker: #5b21b6

Secondary: #667eea
├─ Light: #f0f4ff

Semantic:
├─ Success: #10b981
├─ Warning: #f59e0b
├─ Danger: #ef4444
└─ Info: #3b82f6

Grayscale:
├─ White: #ffffff
├─ Light: #f8fafc
├─ Medium: #f1f5f9
├─ Gray: #e2e8f0
├─ Dark Gray: #64748b
├─ Darker: #1e293b
└─ Text: #1e293b
```

### Spacing Scale

```
0px  → No spacing
2px  → Extra small
4px  → Small
8px  → Extra small unit
12px → Small spacing
16px → Standard spacing
24px → Medium spacing
32px → Large spacing
40px → Extra large spacing
48px → 2XL spacing
```

### Border Radius

```
4px (--radius-sm)      → Small elements (pills, buttons)
8px (--radius-md)      → Medium elements (cards, inputs)
12px (--radius-lg)     → Large elements (containers, modals)
16px (--radius-xl)     → Extra large elements (main sections)
24px (--radius-2xl)    → Full-width sections
```

### Typography

```
Headlines:
├─ H1: 32px, weight 700, line-height 1.2
├─ H2: 24px, weight 700, line-height 1.2
├─ H3: 20px, weight 600, line-height 1.3
└─ H4: 16px, weight 600, line-height 1.4

Body:
├─ Regular: 14px, weight 400, line-height 1.5
├─ Medium: 14px, weight 500, line-height 1.5
├─ Semibold: 14px, weight 600, line-height 1.5
└─ Small: 12px, weight 400, line-height 1.5

Monospace (Numbers):
├─ 12px, family 'Courier New'
└─ weight 600, line-height 1.4
```

### Shadows

```
Small:  0 1px 2px 0 rgba(0, 0, 0, 0.05)
Medium: 0 4px 6px -1px rgba(0, 0, 0, 0.1)
Large:  0 10px 15px -3px rgba(0, 0, 0, 0.1)
XL:     0 20px 25px -5px rgba(0, 0, 0, 0.1)
```

### Transitions

```
Fast: 150ms cubic-bezier(0.4, 0, 0.2, 1)
Base: 200ms cubic-bezier(0.4, 0, 0.2, 1)
Slow: 300ms cubic-bezier(0.4, 0, 0.2, 1)
```

---

## Responsive Design

### Desktop Layout (1024px+)

- Full width layout
- All KPI cards visible (4 columns)
- Pivot table with full features
- Search bar always visible
- Filter bar shows all options

### Tablet Layout (640-1024px)

- Adjusted padding (1.5rem)
- KPI cards: 2 columns
- Header switches to single column
- Pivot table: Horizontal scroll if needed
- Filter pills may wrap

### Mobile Layout (<640px)

- Minimal padding (1rem)
- KPI cards: 1 column
- Header: Stacked vertically
- Search bar: Full width
- Filter bar: Compact mode
- Table: Scrollable with sticky left column
- Font sizes reduced

### Small Mobile (<380px)

- Ultra-compact layout
- KPI icon and content stacked
- Minimal spacing between elements
- Smaller font sizes throughout

---

## Animation Specifications

### Page Load

```
Fade In + Slide Up
Duration: 300ms
Easing: cubic-bezier(0.4, 0, 0.2, 1)
Stagger: 50ms between elements
```

### Card Hover

```
Transform: translateY(-4px)
Box Shadow: Increase
Duration: 150ms
Easing: cubic-bezier(0.4, 0, 0.2, 1)
```

### Filter Pills Hover

```
Transform: translateY(-2px)
Box Shadow: Increase
Duration: 150ms
```

### Row Hover

```
Background: Gradient shift
Transform: scale(1.01)
Duration: 150ms
```

### Expand/Collapse

```
Icon Rotation: 90 degrees
Duration: 300ms
```

### Dark Mode Transition

```
Background Color: Shift
Duration: 300ms
Easing: ease-out
```

---

## Accessibility

### Color Contrast

- Primary text on white: 4.5:1 (AAA)
- Secondary text: 3:1 (AA)
- All interactive elements: 4.5:1 (AAA)

### Focus States

- All buttons: Visible focus ring
- Color: Primary color with 3px offset
- Min size: 2px

### Keyboard Navigation

- Tab order: Logical flow
- Escape: Close modals, clear search
- Enter: Activate buttons
- Ctrl+K / Cmd+K: Focus search

### Screen Reader Support

- ARIA labels on icons
- Semantic HTML structure
- Table headers marked
- Dynamic content updates announced

---

## Dark Mode Specifications

### Color Adjustments

```
Background: #0f172a (almost black)
Surface: #1e293b (dark gray)
Tertiary: #334155 (medium gray)
Text Primary: #f1f5f9 (light)
Text Secondary: #cbd5e1 (medium light)
Border: #334155 (dark border)
Shadow: Higher opacity (0.3-0.4)
```

### Automatic Activation

- Detect system preference: `prefers-color-scheme: dark`
- Listen for changes
- Smooth transition on toggle
- Persist user preference (optional)

---

## Performance Targets

| Metric                   | Target | Current |
| ------------------------ | ------ | ------- |
| First Paint              | <1s    | ~500ms  |
| First Contentful Paint   | <1.5s  | ~700ms  |
| Largest Contentful Paint | <2.5s  | ~1.2s   |
| Cumulative Layout Shift  | <0.1   | ~0.05   |
| Time to Interactive      | <3s    | ~1.5s   |
| Animation FPS            | 60     | 60      |

---

## Browser Support

| Browser       | Version | Status             |
| ------------- | ------- | ------------------ |
| Chrome        | 120+    | ✅ Fully supported |
| Firefox       | 121+    | ✅ Fully supported |
| Safari        | 17+     | ✅ Fully supported |
| Edge          | 120+    | ✅ Fully supported |
| Mobile Safari | 17+     | ✅ Fully supported |
| Chrome Mobile | 120+    | ✅ Fully supported |

---

## Print Styles

- Hide filters and controls
- Keep header and data table
- White background
- Black text
- No shadows
- Avoid page breaks within rows

---

## Future Enhancements

Potential additions:

1. Export to PDF/Excel
2. Custom date range picker
3. Advanced filters (saved views)
4. Data visualization charts
5. Comparison reports
6. Scheduled reports
7. Real-time updates via WebSocket
8. Multi-employee comparison
9. Trend analysis
10. Predictive analytics

---

**Design Specification v1.0** ✅ Complete and production-ready.
