"""Initial schema - complete WildosVPN database structure

Revision ID: 001_initial_schema
Revises: 
Create Date: 2025-01-09 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text
import os


# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Admins table
    op.create_table('admins',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=32), nullable=True),
        sa.Column('hashed_password', sa.String(length=128), nullable=True),
        sa.Column('enabled', sa.Boolean(), server_default=sa.text('(1)'), nullable=False),
        sa.Column('all_services_access', sa.Boolean(), server_default=sa.text('(0)'), nullable=False),
        sa.Column('modify_users_access', sa.Boolean(), server_default=sa.text('(1)'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('is_sudo', sa.Boolean(), nullable=True),
        sa.Column('password_reset_at', sa.DateTime(), nullable=True),
        sa.Column('subscription_url_prefix', sa.String(length=256), server_default=sa.text("''"), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('admins', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_admins_username'), ['username'], unique=True)

    # Services table
    op.create_table('services',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=64), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # System table
    op.create_table('system',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uplink', sa.BigInteger(), nullable=True),
        sa.Column('downlink', sa.BigInteger(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # JWT table
    op.create_table('jwt',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('secret_key', sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Insert initial JWT secret key
    jwt_secret = os.urandom(32).hex()
    op.execute(f"INSERT INTO jwt (id, secret_key) VALUES (1, '{jwt_secret}')")

    # TLS table
    op.create_table('tls',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(length=4096), nullable=False),
        sa.Column('certificate', sa.String(length=2048), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Settings table
    op.create_table('settings',
        sa.Column('id', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column('subscription', sa.JSON(), nullable=False),
        sa.Column('telegram', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Nodes table
    op.create_table('nodes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=256), nullable=True),
        sa.Column('connection_backend', sa.String(length=32), nullable=True),
        sa.Column('address', sa.String(length=256), nullable=True),
        sa.Column('port', sa.Integer(), nullable=True),
        sa.Column('xray_version', sa.String(length=32), nullable=True),
        sa.Column('status', sa.Enum('unhealthy', 'healthy', 'disabled', name='nodestatus'), nullable=False),
        sa.Column('last_status_change', sa.DateTime(), nullable=True),
        sa.Column('message', sa.String(length=1024), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('uplink', sa.BigInteger(), nullable=True),
        sa.Column('downlink', sa.BigInteger(), nullable=True),
        sa.Column('usage_coefficient', sa.Float(), server_default=sa.text('1.0'), nullable=False),
        sa.Column('certificate', sa.Text(), nullable=True),
        sa.Column('private_key', sa.Text(), nullable=True),
        sa.Column('cert_created_at', sa.DateTime(), nullable=True),
        sa.Column('cert_expires_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('address', 'port'),
        sa.UniqueConstraint('name')
    )

    # Users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=32), nullable=True),
        sa.Column('key', sa.String(length=64), nullable=True),
        sa.Column('activated', sa.Boolean(), nullable=False),
        sa.Column('enabled', sa.Boolean(), server_default=sa.text('(1)'), nullable=False),
        sa.Column('removed', sa.Boolean(), server_default=sa.text('(0)'), nullable=False),
        sa.Column('used_traffic', sa.BigInteger(), nullable=True),
        sa.Column('lifetime_used_traffic', sa.BigInteger(), server_default='0', nullable=False),
        sa.Column('traffic_reset_at', sa.DateTime(), nullable=True),
        sa.Column('data_limit', sa.BigInteger(), nullable=True),
        sa.Column('data_limit_reset_strategy', sa.Enum('no_reset', 'day', 'week', 'month', 'year', name='userdatausageresetstrategy'), nullable=False),
        sa.Column('ip_limit', sa.Integer(), nullable=False),
        sa.Column('settings', sa.String(length=1024), nullable=True),
        sa.Column('expire_strategy', sa.Enum('never', 'fixed_date', 'start_on_first_use', name='userexpirestrategy'), nullable=False),
        sa.Column('expire_date', sa.DateTime(), nullable=True),
        sa.Column('usage_duration', sa.BigInteger(), nullable=True),
        sa.Column('activation_deadline', sa.DateTime(), nullable=True),
        sa.Column('admin_id', sa.Integer(), nullable=True),
        sa.Column('sub_updated_at', sa.DateTime(), nullable=True),
        sa.Column('sub_last_user_agent', sa.String(length=512), nullable=True),
        sa.Column('sub_revoked_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('note', sa.String(length=500), nullable=True),
        sa.Column('online_at', sa.DateTime(), nullable=True),
        sa.Column('edit_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['admin_id'], ['admins.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key'),
        sa.UniqueConstraint('username')
    )
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_users_username'), ['username'], unique=False)

    # Backends table
    op.create_table('backends',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=64), nullable=False),
        sa.Column('node_id', sa.Integer(), nullable=True),
        sa.Column('backend_type', sa.String(length=32), nullable=False),
        sa.Column('version', sa.String(length=32), nullable=True),
        sa.Column('running', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['node_id'], ['nodes.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('backends', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_backends_node_id'), ['node_id'], unique=False)

    # Inbounds table
    op.create_table('inbounds',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('protocol', sa.Enum('vmess', 'vless', 'trojan', 'shadowsocks', 'shadowsocks2022', 'hysteria2', 'wireguard', 'tuic', 'shadowtls', name='proxytypes'), nullable=True),
        sa.Column('tag', sa.String(length=256), nullable=False),
        sa.Column('config', sa.String(length=512), nullable=False),
        sa.Column('node_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['node_id'], ['nodes.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('node_id', 'tag')
    )
    with op.batch_alter_table('inbounds', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_inbounds_node_id'), ['node_id'], unique=False)

    # Node tokens table
    op.create_table('node_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('node_id', sa.Integer(), nullable=False),
        sa.Column('token_hash', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('last_used', sa.DateTime(), nullable=True),
        sa.Column('usage_count', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['node_id'], ['nodes.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('node_id', 'token_hash')
    )

    # Failed auth attempts table
    op.create_table('failed_auth_attempts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('node_id', sa.Integer(), nullable=False),
        sa.Column('attempted_at', sa.DateTime(), nullable=False),
        sa.Column('reason', sa.String(length=512), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.ForeignKeyConstraint(['node_id'], ['nodes.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Node user usages table
    op.create_table('node_user_usages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('node_id', sa.Integer(), nullable=True),
        sa.Column('used_traffic', sa.BigInteger(), nullable=True),
        sa.ForeignKeyConstraint(['node_id'], ['nodes.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('created_at', 'user_id', 'node_id')
    )

    # Node usages table
    op.create_table('node_usages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('node_id', sa.Integer(), nullable=True),
        sa.Column('uplink', sa.BigInteger(), nullable=True),
        sa.Column('downlink', sa.BigInteger(), nullable=True),
        sa.ForeignKeyConstraint(['node_id'], ['nodes.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('created_at', 'node_id')
    )

    # Hosts table (InboundHost)
    op.create_table('hosts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('remark', sa.String(length=256), nullable=False),
        sa.Column('address', sa.String(length=256), nullable=False),
        sa.Column('host_protocol', sa.String(length=32), nullable=True),
        sa.Column('host_network', sa.String(length=32), nullable=True),
        sa.Column('uuid', sa.String(length=36), nullable=True),
        sa.Column('password', sa.String(length=128), nullable=True),
        sa.Column('port', sa.Integer(), nullable=True),
        sa.Column('path', sa.String(length=256), nullable=True),
        sa.Column('sni', sa.String(length=1024), nullable=True),
        sa.Column('host', sa.String(length=1024), nullable=True),
        sa.Column('security', sa.Enum('inbound_default', 'none', 'tls', name='inboundhostsecurity'), nullable=False),
        sa.Column('alpn', sa.String(length=32), server_default=sa.text('NULL'), nullable=True),
        sa.Column('fingerprint', sa.Enum('none', 'chrome', 'firefox', 'safari', 'ios', 'android', 'edge', '360', 'qq', 'random', 'randomized', name='inboundhostfingerprint'), server_default=sa.text("'none'"), nullable=False),
        sa.Column('fragment', sa.JSON(), nullable=True),
        sa.Column('udp_noises', sa.JSON(), nullable=True),
        sa.Column('http_headers', sa.JSON(), nullable=True),
        sa.Column('dns_servers', sa.String(length=128), nullable=True),
        sa.Column('mtu', sa.Integer(), nullable=True),
        sa.Column('allowed_ips', sa.Text(), nullable=True),
        sa.Column('header_type', sa.String(length=32), nullable=True),
        sa.Column('reality_public_key', sa.String(length=128), nullable=True),
        sa.Column('reality_short_ids', sa.JSON(), nullable=True),
        sa.Column('flow', sa.String(length=32), nullable=True),
        sa.Column('shadowtls_version', sa.Integer(), nullable=True),
        sa.Column('shadowsocks_method', sa.String(length=32), nullable=True),
        sa.Column('splithttp_settings', sa.JSON(), nullable=True),
        sa.Column('mux_settings', sa.JSON(), nullable=True),
        sa.Column('early_data', sa.Integer(), nullable=True),
        sa.Column('inbound_id', sa.Integer(), nullable=True),
        sa.Column('allowinsecure', sa.Boolean(), nullable=True),
        sa.Column('is_disabled', sa.Boolean(), nullable=True),
        sa.Column('weight', sa.Integer(), server_default='1', nullable=False),
        sa.Column('universal', sa.Boolean(), server_default=sa.text('(0)'), nullable=False),
        sa.ForeignKeyConstraint(['inbound_id'], ['inbounds.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Host chains table
    op.create_table('host_chains',
        sa.Column('host_id', sa.Integer(), nullable=False),
        sa.Column('chained_host_id', sa.Integer(), nullable=True),
        sa.Column('seq', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['chained_host_id'], ['hosts.id'], ),
        sa.ForeignKeyConstraint(['host_id'], ['hosts.id'], ),
        sa.PrimaryKeyConstraint('host_id', 'seq')
    )

    # Junction tables
    op.create_table('admins_services',
        sa.Column('admin_id', sa.Integer(), nullable=False),
        sa.Column('service_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['admin_id'], ['admins.id'], ),
        sa.ForeignKeyConstraint(['service_id'], ['services.id'], ),
        sa.PrimaryKeyConstraint('admin_id', 'service_id')
    )

    op.create_table('inbounds_services',
        sa.Column('inbound_id', sa.Integer(), nullable=False),
        sa.Column('service_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['inbound_id'], ['inbounds.id'], ),
        sa.ForeignKeyConstraint(['service_id'], ['services.id'], ),
        sa.PrimaryKeyConstraint('inbound_id', 'service_id')
    )

    op.create_table('users_services',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('service_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['service_id'], ['services.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('user_id', 'service_id')
    )

    op.create_table('hosts_services',
        sa.Column('host_id', sa.Integer(), nullable=False),
        sa.Column('service_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['host_id'], ['hosts.id'], ),
        sa.ForeignKeyConstraint(['service_id'], ['services.id'], ),
        sa.PrimaryKeyConstraint('host_id', 'service_id')
    )


def downgrade():
    # Drop junction tables first
    op.drop_table('hosts_services')
    op.drop_table('users_services')
    op.drop_table('inbounds_services')
    op.drop_table('admins_services')
    
    # Drop dependent tables
    op.drop_table('host_chains')
    op.drop_table('hosts')
    op.drop_table('node_usages')
    op.drop_table('node_user_usages')
    op.drop_table('failed_auth_attempts')
    op.drop_table('node_tokens')
    op.drop_table('inbounds')
    op.drop_table('backends')
    op.drop_table('users')
    op.drop_table('nodes')
    op.drop_table('settings')
    op.drop_table('tls')
    op.drop_table('jwt')
    op.drop_table('system')
    op.drop_table('services')
    op.drop_table('admins')