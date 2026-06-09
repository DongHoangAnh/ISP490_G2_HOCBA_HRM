FROM odoo:19

# Copy custom addons to ODOO addons directory
COPY custom-addons /mnt/extra-addons

EXPOSE 8069
