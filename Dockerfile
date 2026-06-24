FROM odoo:19

# Install pymysql for CMS MySQL integration
RUN pip install pymysql --break-system-packages

# Copy custom addons to ODOO addons directory
COPY custom-addons /mnt/extra-addons

EXPOSE 8069
