# Installation & Setup Guide

## Prerequisites

- Odoo 19.0
- Python 3.10+
- PostgreSQL 12+
- Administrative access to Odoo

---

## Step-by-Step Installation

### 1. Download Module Files

Copy the `hr_holidays_modern` folder to your Odoo addons directory:

```bash
# If using standard Odoo installation
cp -r hr_holidays_modern /opt/odoo/addons/

# If using containerized Odoo
docker cp hr_holidays_modern odoo_container:/opt/odoo/addons/

# If using custom addons path
cp -r hr_holidays_modern /your/custom/addons/path/
```

### 2. Update Odoo Configuration

Edit your Odoo config file (`odoo.conf`):

```ini
# Ensure custom addons path is included
addons_path = /opt/odoo/addons,/your/custom/addons/path

# Optional: Enable debugging for development
debug_mode = True
```

### 3. Restart Odoo Service

```bash
# If using systemd
sudo systemctl restart odoo

# If using manual service
killall python3
python3 -m odoo.bin -c /etc/odoo/odoo.conf

# If using Docker
docker restart odoo_container
```

### 4. Update Module List

In Odoo Web Interface:

1. Go to **Apps** → **Update Apps List**
   - Or press `Ctrl+R` to refresh

2. Search for "HR Holidays Modern UI"

3. Click the module to see details:
   - Name: HR Holidays Modern UI
   - Version: 19.0.1.0.0
   - Category: Human Resources
   - Depends on: hr_holidays

4. Click **Install**

### 5. Activate the Module

After installation:

1. Navigate to: **HR** → **Time Off**

2. Click on **Holidays by Employee** (or similar in your language)

3. The modern UI should now be visible

---

## Verification Checklist

After installation, verify each item:

```
[ ] Module installed successfully
[ ] No error messages in browser console
[ ] HR Holidays page shows modern design
[ ] Header displays with icon and title
[ ] Filter section is visible and sticky
[ ] KPI cards display with icons
[ ] Pivot table has modern styling
[ ] Search functionality works
[ ] Responsive layout works on mobile
[ ] Dark mode works (if enabled)
[ ] No CSS style conflicts
[ ] All animations are smooth (60 FPS)
```

---

## Troubleshooting

### Issue: Module doesn't appear in Apps list

**Solution:**

1. Clear browser cache: `Ctrl+Shift+Delete`
2. Restart Odoo service
3. Re-login to Odoo
4. Go to **Apps** → **Update Apps List**

### Issue: Styles not applied

**Solution:**

1. Check browser developer console (F12):
   - Look for CSS loading errors
   - Check Network tab for CSS file (should be 200 OK)

2. Clear Odoo assets:

   ```python
   # In Odoo shell
   python3 manage.py shell
   >>> from odoo import api, SUPERUSER_ID
   >>> with api.Environment.manage():
   ...     env = api.Environment(cr, SUPERUSER_ID, {})
   ...     env['ir.qweb'].clear_cache()
   ```

3. Hard refresh browser: `Ctrl+Shift+R`

### Issue: JavaScript errors in console

**Solution:**

1. Check for "Uncaught" errors in console
2. Verify Odoo jQuery version compatibility
3. Check if other modules conflict
4. Restart browser and Odoo service

### Issue: KPI values show "-"

**Solution:**

1. This is normal on first load
2. Values populate when pivot data loads
3. Refresh page: `F5`
4. Check browser console for calculation errors

### Issue: Responsive design not working on mobile

**Solution:**

1. Check device zoom level (should be 100%)
2. Clear browser cache
3. Verify viewport meta tag:
   - In browser DevTools, check that viewport is set correctly
4. Test in mobile browser DevTools (F12 → Toggle device toolbar)

---

## Advanced Configuration

### Custom Colors

Edit `static/src/css/hr_holidays_modern.css`:

```css
:root {
  --color-primary: #7c3aed; /* Change primary color */
  --color-secondary: #667eea; /* Change secondary color */
  --color-success: #10b981; /* Change success color */
  /* ... etc ... */
}
```

Then restart Odoo and hard-refresh browser.

### Custom Breakpoints

Edit responsive breakpoints in CSS:

```css
/* Tablet breakpoint */
@media (max-width: 1024px) {
  /* Your customizations */
}

/* Mobile breakpoint */
@media (max-width: 640px) {
  /* Your customizations */
}
```

### Disable Dark Mode

In `static/src/css/hr_holidays_modern.css`, comment out:

```css
/* html.dark-mode {
    ...
} */
```

### Add Custom KPI Cards

Edit `views/hr_holidays_views.xml`:

```xml
<div class="o_kpi_card">
    <div class="o_kpi_icon o_kpi_icon_5">
        <i class="fa fa-your-icon"></i>
    </div>
    <div class="o_kpi_content">
        <p class="o_kpi_label">Your Label</p>
        <p class="o_kpi_value" data-value="your_value">-</p>
        <p class="o_kpi_meta">Your Meta</p>
    </div>
</div>
```

Add corresponding CSS in `hr_holidays_modern.css`:

```css
.o_kpi_icon_5 {
  background: linear-gradient(135deg, #color1 0%, #color2 100%);
}
```

---

## Performance Optimization

### 1. Enable Gzip Compression

In Nginx:

```nginx
gzip on;
gzip_types text/css application/javascript;
```

In Apache:

```apache
<IfModule mod_deflate.c>
    AddOutputFilterByType DEFLATE text/css application/javascript
</IfModule>
```

### 2. Enable CSS/JS Minification

Odoo automatically minifies assets in production.

### 3. Browser Caching

Configure your web server to cache assets:

```nginx
location ~* \.(css|js|png|jpg|jpeg|gif)$ {
    expires 30d;
    add_header Cache-Control "public, immutable";
}
```

### 4. CDN Integration

For large deployments, use a CDN for static assets.

---

## Multi-Language Support

The module uses Odoo's translation system. To add translations:

1. Create `i18n` directory:

   ```bash
   mkdir -p hr_holidays_modern/i18n
   ```

2. Extract translatable strings:

   ```bash
   cd hr_holidays_modern
   python3 -m odoo.tools.translate --help
   ```

3. Add translation files:
   - `i18n/fr_FR.po` (French)
   - `i18n/es_ES.po` (Spanish)
   - etc.

---

## Development Mode Setup

For development and customization:

```bash
# Clone or download module
cd /opt/odoo/addons
git clone <repo_url> hr_holidays_modern

# Install in development mode
odoo-bin -d your_db -i hr_holidays_modern --dev=all

# Watch for CSS/JS changes
npm run watch  # If using npm

# Or use Odoo's built-in file watcher
odoo-bin --dev=reload,qweb,werkzeug
```

---

## Database Backup Before Installation

Always backup your database before installing new modules:

```bash
# PostgreSQL backup
pg_dump your_db_name > backup_before_install.sql

# Or use Odoo's backup function:
# Settings → Databases → Backup
```

---

## Rollback / Uninstallation

If you need to remove the module:

### Via Odoo UI:

1. Go to **Apps** → Search "HR Holidays Modern UI"
2. Click the module
3. Click **Uninstall**
4. Confirm

### Via Command Line:

```bash
odoo-bin -d your_db -u hr_holidays_modern --stop-after-init
```

---

## Support & Documentation

- Check README.md for feature documentation
- Review code comments in CSS and JS files
- Check Odoo logs: `tail -f /var/log/odoo/odoo.log`
- Browser DevTools for debugging

---

## Next Steps

After successful installation:

1. ✅ Verify the modern UI is displaying
2. ✅ Test all features (search, filters, KPIs)
3. ✅ Test on mobile devices
4. ✅ Customize colors if needed
5. ✅ Train users on new interface
6. ✅ Monitor performance and adjust as needed

---

**Installation complete! Enjoy your modern HR Holidays dashboard.** 🎉
