# Developer Customization Guide

## Overview

This guide covers how to customize and extend the HR Holidays Modern UI module for your specific needs.

---

## Quick Customizations

### 1. Change Primary Color

**File:** `static/src/css/hr_holidays_modern.css`

Find and update:

```css
:root {
  --color-primary: #7c3aed; /* Change this to your color */
  --color-primary-light: #ede9fe; /* Light variant */
  --color-primary-dark: #6d28d9; /* Dark variant */
  --color-primary-darker: #5b21b6; /* Darker variant */
}
```

**Tip:** Use tools like [ColorShades.io](https://www.colorshades.io) to generate color variants from your base color.

---

### 2. Modify Header Text

**File:** `views/hr_holidays_views.xml`

Find:

```xml
<h1 class="o_header_title">
    <i class="fa fa-calendar-o o_header_icon"></i>
    Ngày nghỉ theo Nhân viên
</h1>
```

Change to:

```xml
<h1 class="o_header_title">
    <i class="fa fa-your-icon o_header_icon"></i>
    Your Custom Title
</h1>
```

---

### 3. Change KPI Card Count

**File:** `views/hr_holidays_views.xml`

To remove or add KPI cards, edit the `o_hr_holidays_kpi_cards` section:

```xml
<!-- Add new card -->
<div class="o_kpi_card">
    <div class="o_kpi_icon o_kpi_icon_5">
        <i class="fa fa-icon-name"></i>
    </div>
    <div class="o_kpi_content">
        <p class="o_kpi_label">Label Text</p>
        <p class="o_kpi_value" data-value="value_key">-</p>
        <p class="o_kpi_meta">Meta Text</p>
    </div>
</div>
```

Then add CSS:

```css
.o_kpi_icon_5 {
  background: linear-gradient(135deg, #yourColor1 0%, #yourColor2 100%);
}
```

And update KPI calculation in JS:

```javascript
this.kpiData = {
  // ... existing ...
  value_key: "Your Value",
};
```

---

### 4. Adjust Responsive Breakpoints

**File:** `static/src/css/hr_holidays_modern.css`

Find the media queries:

```css
/* Tablet (768px) */
@media (max-width: 1024px) {
  /* Your tablet styles */
}

/* Mobile (480px) */
@media (max-width: 640px) {
  /* Your mobile styles */
}
```

Adjust the pixel values:

```css
/* Custom breakpoints */
@media (max-width: 1200px) {
  /* For larger tablets */
}

@media (max-width: 500px) {
  /* For smaller phones */
}
```

---

### 5. Disable Dark Mode

**File:** `static/src/css/hr_holidays_modern.css`

Comment out the dark mode section:

```css
/* Dark Mode Variables - DISABLED */
/* html.dark-mode {
    --color-bg-primary: #0f172a;
    ...
} */
```

Or remove the dark mode detection in JS:

```javascript
// In _setupDarkModeDetection()
// Comment out this section
```

---

## Advanced Customizations

### Add Custom KPI Calculation

**File:** `static/src/js/hr_holidays_modern.js`

Modify the `_calculateKPIs()` function:

```javascript
_calculateKPIs: function () {
    const self = this;

    // Get pivot table data
    const rows = document.querySelectorAll('.o_hr_holidays_modern_table_wrapper tbody tr');

    // Your custom calculations
    let myCustomValue = 0;
    rows.forEach(row => {
        // Process data
        myCustomValue += parseInt(row.cells[2].textContent) || 0;
    });

    this.kpiData = {
        totalDays: myCustomValue,
        // ... other KPIs ...
    };

    this._updateKPIDisplay();
},
```

---

### Extend the Pivot Table Styling

**File:** `static/src/css/hr_holidays_modern.css`

Add custom styles after existing table styles:

```css
/* Custom pivot table enhancements */
.o_hr_holidays_modern_table_wrapper tbody tr.special-row {
  background: linear-gradient(90deg, #f0f4ff 0%, transparent 100%);
  border-left: 4px solid #7c3aed;
}

.o_hr_holidays_modern_table_wrapper tbody tr.special-row td {
  font-weight: 600;
  color: #7c3aed;
}
```

---

### Add Custom Filters

**File:** `views/hr_holidays_views.xml` and `static/src/js/hr_holidays_modern.js`

In XML, add filter pills:

```xml
<div class="o_filter_pills">
    <button class="o_filter_pill" data-filter="active">
        <span>Active Only</span>
        <i class="fa fa-times"></i>
    </button>
    <button class="o_filter_pill" data-filter="recent">
        <span>Recent</span>
        <i class="fa fa-times"></i>
    </button>
</div>
```

In JS, handle filter clicks:

```javascript
_setupFilterInteractions: function () {
    const filterPills = document.querySelectorAll('.o_filter_pill');

    filterPills.forEach(pill => {
        pill.addEventListener('click', (e) => {
            const filterType = pill.dataset.filter;
            this._applyFilter(filterType);
        });
    });
},

_applyFilter: function (filterType) {
    const rows = document.querySelectorAll('.o_hr_holidays_modern_table_wrapper tbody tr');

    rows.forEach(row => {
        let show = true;

        if (filterType === 'active') {
            // Your filter logic
            show = row.textContent.includes('Active');
        }

        row.style.display = show ? '' : 'none';
    });
},
```

---

### Create Custom CSS Theme

**File:** Create `static/src/css/themes/custom-theme.css`

```css
/* Custom Theme - Blue */
:root.theme-blue {
  --color-primary: #3b82f6;
  --color-primary-light: #dbeafe;
  --color-primary-dark: #1d4ed8;
  --color-primary-darker: #1e40af;
}

/* Apply theme */
html.theme-blue .o_header_icon {
  background: linear-gradient(135deg, #dbeafe 0%, rgba(59, 130, 246, 0.1) 100%);
}

/* ... more theme styles ... */
```

Then load it:

```xml
<!-- In views/hr_holidays_views.xml -->
<record id="hr_holidays_report_modern" model="ir.ui.view">
    <!-- ... -->
    <field name="arch" type="xml">
        <data>
            <!-- Add class to container -->
            <div class="o_hr_holidays_modern_container theme-blue">
```

---

### Integrate with Odoo Backend Data

**File:** `models/__init__.py` - Create `models/hr_leave_custom.py`

```python
from odoo import models, fields, api

class HRLeaveCustom(models.Model):
    _inherit = 'hr.leave'

    custom_field = fields.Char('Custom Field')

    @api.model
    def get_kpi_data(self):
        """Get KPI data for dashboard"""
        total_days = sum(self.search([]).mapped('number_of_days_display'))

        return {
            'total_days': total_days,
            'total_leaves': len(self.search([])),
            'pending_count': len(self.search([('state', '=', 'confirm')])),
        }
```

Update `controllers/__init__.py` - Create `controllers/main.py`:

```python
from odoo import http
from odoo.http import request

class HRHolidaysController(http.Controller):
    @http.route('/hr_holidays/kpi_data', type='json', auth='user')
    def get_kpi_data(self):
        """API endpoint for KPI data"""
        kpi = request.env['hr.leave'].get_kpi_data()
        return kpi
```

Then in `static/src/js/hr_holidays_modern.js`, fetch the data:

```javascript
_calculateKPIs: async function () {
    const self = this;

    try {
        // Fetch from server
        const kpiData = await rpc.query({
            route: '/hr_holidays/kpi_data',
            type: 'json',
        });

        this.kpiData = {
            totalDays: kpiData.total_days,
            topEmployee: '-',
            pendingCount: kpiData.pending_count,
            popularType: '-'
        };
    } catch (error) {
        console.error('Error fetching KPI data:', error);
    }

    this._updateKPIDisplay();
},
```

---

### Add Export Functionality

**File:** `static/src/js/hr_holidays_modern.js`

Add export button in XML:

```xml
<button class="o_export_btn" id="export_table">
    <i class="fa fa-download"></i>
    Export to CSV
</button>
```

Add export logic in JS:

```javascript
_setupTableAnimations: function () {
    // ... existing code ...

    const exportBtn = document.querySelector('#export_table');
    if (exportBtn) {
        exportBtn.addEventListener('click', () => {
            this._exportTableToCSV();
        });
    }
},

_exportTableToCSV: function () {
    const table = document.querySelector('.o_hr_holidays_modern_table_wrapper table');
    if (!table) return;

    let csv = [];
    const rows = table.querySelectorAll('tr');

    rows.forEach(row => {
        const cols = row.querySelectorAll('td, th');
        const csvRow = [];
        cols.forEach(col => {
            csvRow.push('"' + col.textContent.trim() + '"');
        });
        csv.push(csvRow.join(','));
    });

    const csvContent = 'data:text/csv;charset=utf-8,' + csv.join('\n');
    const link = document.createElement('a');
    link.setAttribute('href', encodeURI(csvContent));
    link.setAttribute('download', 'holidays_report.csv');
    link.click();
},
```

---

## Performance Optimizations

### 1. Lazy Load Images

```javascript
// In _attachEventHandlers()
const images = document.querySelectorAll("img[data-src]");
const imageObserver = new IntersectionObserver((entries, observer) => {
  entries.forEach((entry) => {
    if (entry.isIntersecting) {
      const img = entry.target;
      img.src = img.dataset.src;
      observer.unobserve(img);
    }
  });
});

images.forEach((img) => imageObserver.observe(img));
```

### 2. Debounce Search

```javascript
_setupSearch: function () {
    const searchInput = document.querySelector('.o_search_input');
    if (!searchInput) return;

    let debounceTimer;
    searchInput.addEventListener('input', (e) => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            const query = e.target.value.toLowerCase();
            this._filterTableBySearch(query);
        }, 300); // Wait 300ms after user stops typing
    });
},
```

### 3. Virtual Scrolling for Large Tables

```javascript
// For tables with 1000+ rows, consider virtual scrolling
// library like: https://github.com/YEXT/virtual-scroll
```

---

## Testing Customizations

### Unit Tests Example

```javascript
describe("HR Holidays Modern UI", function () {
  describe("_calculateKPIs", function () {
    it("should calculate total days correctly", function () {
      const renderer = new ModernPivotRenderer();
      renderer._calculateKPIs();

      expect(renderer.kpiData.totalDays).toBeGreaterThan(0);
    });
  });

  describe("_filterTableBySearch", function () {
    it("should filter rows by search query", function () {
      renderer._filterTableBySearch("John");

      const visibleRows = document.querySelectorAll(
        '.o_hr_holidays_modern_table_wrapper tbody tr:not([style*="display: none"])',
      );

      expect(visibleRows.length).toBeGreaterThan(0);
    });
  });
});
```

---

## Debugging

### Enable Debug Mode

In `__manifest__.py`:

```python
'debug': True,
```

In browser console:

```javascript
// Access renderer instance
const renderer = odoo.define("hr_holidays_modern");
console.log(renderer.kpiData);
```

### Check Console Logs

```javascript
// In _initializeModernUI()
console.log("Modern UI initialized");
console.log("KPI Data:", this.kpiData);
console.log("Animation FPS:", performance.timing);
```

### Profile Performance

```javascript
// Measure function performance
performance.mark("kpi-start");
this._calculateKPIs();
performance.mark("kpi-end");
performance.measure("KPI Calculation", "kpi-start", "kpi-end");
console.log(performance.getEntriesByName("KPI Calculation"));
```

---

## Troubleshooting Custom Changes

| Problem             | Solution                                     |
| ------------------- | -------------------------------------------- |
| Styles not applying | Clear browser cache, restart Odoo            |
| JS errors           | Check console (F12), verify syntax           |
| Colors wrong        | Check CSS variable values                    |
| Responsive broken   | Check media query breakpoints                |
| Animations choppy   | Use `transform` instead of `top/left`        |
| Filter not working  | Verify jQuery selectors are correct          |
| KPI values wrong    | Check calculation logic in \_calculateKPIs() |

---

## Version Control

For git management:

```bash
# Ignore node_modules and build artifacts
echo "node_modules/" > .gitignore
echo ".vscode/" >> .gitignore
echo "__pycache__/" >> .gitignore
echo "*.pyc" >> .gitignore

# Commit changes
git add .
git commit -m "Customize HR Holidays Modern UI - [describe changes]"
git push origin main
```

---

## Migration Guide

### Updating from v0.x to v1.0

1. Backup your database
2. Update CSS variables if you customized colors
3. Update JS if you extended KPI functionality
4. Re-test all features

### Breaking Changes

- None in v1.0 release

---

## Getting Help

1. Check documentation files
2. Review code comments
3. Check browser console for errors
4. Enable debug mode for detailed logging
5. Check Odoo logs: `/var/log/odoo/odoo.log`

---

**Developer Guide v1.0** ✅ Ready for customization.
