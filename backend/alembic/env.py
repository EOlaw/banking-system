# backend/alembic/env.py
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Import your models
from app.db.session import Base
from app.db.models import User, Account, Transaction
from app.config.settings import settings

# Alembic Config object
config = context.config

# Set the SQLAlchemy URL
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Interpret the config file for Python logging
fileConfig(config.config_file_name)

# Add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata

# Other values from the config, defined by the needs of env.py
config_naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()


# backend/alembic/script.py.mako
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}


def upgrade():
    ${upgrades if upgrades else "pass"}


def downgrade():
    ${downgrades if downgrades else "pass"}


# backend/alembic/versions/initial_migration.py
"""initial migration

Revision ID: a1b2c3d4e5f6
Revises: 
Create Date: 2025-05-04 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create enum types
    account_type = postgresql.ENUM('checking', 'savings', 'credit', 'investment', name='accounttype')
    account_type.create(op.get_bind())
    
    transaction_type = postgresql.ENUM('deposit', 'withdrawal', 'transfer', 'payment', 'fee', 'interest', name='transactiontype')
    transaction_type.create(op.get_bind())
    
    transaction_status = postgresql.ENUM('pending', 'completed', 'failed', 'reversed', name='transactionstatus')
    transaction_status.create(op.get_bind())
    
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('first_name', sa.String(), nullable=True),
        sa.Column('last_name', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_superuser', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    
    # Create accounts table
    op.create_table('accounts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('account_number', sa.String(), nullable=False),
        sa.Column('account_type', sa.Enum('checking', 'savings', 'credit', 'investment', name='accounttype'), nullable=False),
        sa.Column('balance', sa.Float(), nullable=True),
        sa.Column('currency', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('owner_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_accounts_account_number'), 'accounts', ['account_number'], unique=True)
    op.create_index(op.f('ix_accounts_id'), 'accounts', ['id'], unique=False)
    
    # Create transactions table
    op.create_table('transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('transaction_number', sa.String(), nullable=False),
        sa.Column('transaction_type', sa.Enum('deposit', 'withdrawal', 'transfer', 'payment', 'fee', 'interest', name='transactiontype'), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(), nullable=True),
        sa.Column('status', sa.Enum('pending', 'completed', 'failed', 'reversed', name='transactionstatus'), nullable=True),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('source_account_id', sa.Integer(), nullable=True),
        sa.Column('destination_account_id', sa.Integer(), nullable=True),
        sa.Column('sender_id', sa.Integer(), nullable=True),
        sa.Column('receiver_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['destination_account_id'], ['accounts.id'], ),
        sa.ForeignKeyConstraint(['receiver_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['sender_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['source_account_id'], ['accounts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_transactions_id'), 'transactions', ['id'], unique=False)
    op.create_index(op.f('ix_transactions_transaction_number'), 'transactions', ['transaction_number'], unique=True)


def downgrade():
    # Drop tables
    op.drop_index(op.f('ix_transactions_transaction_number'), table_name='transactions')
    op.drop_index(op.f('ix_transactions_id'), table_name='transactions')
    op.drop_table('transactions')
    
    op.drop_index(op.f('ix_accounts_id'), table_name='accounts')
    op.drop_index(op.f('ix_accounts_account_number'), table_name='accounts')
    op.drop_table('accounts')
    
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    
    # Drop enum types
    sa.Enum(name='transactionstatus').drop(op.get_bind(), checkfirst=False)
    sa.Enum(name='transactiontype').drop(op.get_bind(), checkfirst=False)
    sa.Enum(name='accounttype').drop(op.get_bind(), checkfirst=False)


# backend/alembic.ini
# A generic, single database configuration.

[alembic]
# path to migration scripts
script_location = alembic

# template used to generate migration files
file_template = %%(year)d%%(month).2d%%(day).2d_%%(hour).2d%%(minute).2d%%(second).2d_%%(slug)s

# timezone to use when rendering the date
# within the migration file as well as the filename.
# string value is passed to dateutil.tz.gettz()
# leave blank for localtime
# timezone =

# max length of characters to apply to the
# "slug" field
# truncate_slug_length = 40

# set to 'true' to run the environment during
# the 'revision' command, regardless of autogenerate
# revision_environment = false

# set to 'true' to allow .pyc and .pyo files without
# a source .py file to be detected as revisions in the
# versions/ directory
# sourceless = false

# version location specification; this defaults
# to alembic/versions.  When using multiple version
# directories, initial revisions must be specified with --version-path
# version_locations = %(here)s/bar %(here)s/bat alembic/versions

# the output encoding used when revision files
# are written from script.py.mako
# output_encoding = utf-8

sqlalchemy.url = postgresql://postgres:postgres@localhost/banking_db

[post_write_hooks]
# post_write_hooks defines scripts or Python functions that are run
# on newly generated revision scripts.  See the documentation for further
# detail and examples

# format using "black" - use the console_scripts runner, against the "black" entrypoint
# hooks=black
# black.type=console_scripts
# black.entrypoint=black
# black.options=-l 79

# Logging configuration
[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S