"""Add default settings from marzneshin

Revision ID: 003_add_default_settings  
Revises: 002_add_missing_schema
Create Date: 2025-01-09 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
import json

# revision identifiers, used by Alembic.
revision = '003_add_default_settings'
down_revision = '002_add_missing_schema'
branch_labels = None
depends_on = None

# Default settings from marzneshin
DEFAULT_SETTINGS = {
    "telegram": None,
    "subscription": {
        "template_on_acceptance": True,
        "profile_title": "Support",
        "support_link": "t.me/support", 
        "update_interval": 12,
        "rules": [
            {
                "pattern": "^([Cc]lash-verge|[Cc]lash-?[Mm]eta)",
                "result": "clash-meta"
            },
            {
                "pattern": "^([Cc]lash|[Ss]tash)",
                "result": "clash"
            },
            {
                "pattern": "^(SFA|SFI|SFM|SFT|[Kk]aring|[Hh]iddify[Nn]ext)",
                "result": "sing-box"
            },
            {
                "pattern": "^v2rayN/(?:6\\.(?:[5-9]\\d+|4[1-9])|[7-9]\\d*\\.\\d+)",
                "result": "xray"
            },
            {
                "pattern": "^v2rayN/",
                "result": "base64-links"
            },
            {
                "pattern": "^v2rayNG/([2-9]|1\\.(9|\\d{2,})|1\\.8\\.(1[7-9]|[2-9]\\d|\\d{3,}))",
                "result": "xray"
            },
            {
                "pattern": "^v2rayNG/",
                "result": "base64-links"
            },
            {
                "pattern": "^[Ss]treisand",
                "result": "xray"
            },
            {
                "pattern": ".*",
                "result": "base64-links"
            }
        ]
    }
}

def upgrade():
    """Insert default settings if settings table is empty"""
    
    # Check if settings table exists and is empty
    connection = op.get_bind()
    
    # Check if settings table has any records
    result = connection.execute(sa.text("SELECT COUNT(*) FROM settings")).fetchone()
    settings_count = result[0] if result else 0
    
    if settings_count == 0:
        # Insert default settings
        subscription_json = json.dumps(DEFAULT_SETTINGS["subscription"])
        telegram_json = json.dumps(DEFAULT_SETTINGS["telegram"]) if DEFAULT_SETTINGS["telegram"] else None
        
        if telegram_json:
            connection.execute(
                sa.text("INSERT INTO settings (id, subscription, telegram) VALUES (0, :subscription, :telegram)"),
                {"subscription": subscription_json, "telegram": telegram_json}
            )
        else:
            connection.execute(
                sa.text("INSERT INTO settings (id, subscription, telegram) VALUES (0, :subscription, NULL)"),
                {"subscription": subscription_json}
            )
    
    # Initialize system stats if empty
    result = connection.execute(sa.text("SELECT COUNT(*) FROM system")).fetchone()
    system_count = result[0] if result else 0
    
    if system_count == 0:
        # Insert default system stats
        connection.execute(
            sa.text("INSERT INTO system (id, uplink, downlink) VALUES (1, 0, 0)")
        )
    
    # Create TLS certificate if empty
    result = connection.execute(sa.text("SELECT COUNT(*) FROM tls")).fetchone()
    tls_count = result[0] if result else 0
    
    if tls_count == 0:
        # Generate TLS certificate using crypto utility
        from app.utils.crypto import generate_certificate
        cert_data = generate_certificate()
        
        connection.execute(
            sa.text("INSERT INTO tls (id, certificate, key) VALUES (1, :certificate, :key)"),
            {"certificate": cert_data["cert"], "key": cert_data["key"]}
        )


def downgrade():
    """Remove default settings"""
    connection = op.get_bind()
    
    # Remove default settings
    connection.execute(sa.text("DELETE FROM settings WHERE id = 0"))
    
    # Remove default system stats
    connection.execute(sa.text("DELETE FROM system WHERE id = 1"))