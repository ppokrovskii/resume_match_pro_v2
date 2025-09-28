"""Initial schema - Document Service only

Revision ID: 001
Revises: 
Create Date: 2024-01-01 10:00:00.000000

Following microservice boundaries:
- Document service only owns document and upload_session data
- User and organization data comes from identity provider (Auth0) or user service
- user_id and organization_id are foreign references without FK constraints
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable required extensions
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    
    # Create documents table - core entity owned by document service
    op.create_table(
        'documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),  # Reference to user in identity service
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True),  # Reference to organization in identity service
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('file_type', sa.String(20), nullable=True),
        sa.Column('content_type', sa.String(100), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('storage_path', sa.Text(), nullable=False),
        sa.Column('text_content', sa.Text(), nullable=True),
        sa.Column('role', sa.String(255), nullable=True),  # Added by AI microservices via PUT endpoint
        sa.Column('doc_metadata', postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column('processing_status', sa.String(20), nullable=False, server_default='completed'),
        sa.Column('processing_error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("file_type IS NULL OR file_type IN ('cv', 'job_description')", name='check_document_file_type'),
        sa.CheckConstraint("file_size > 0", name='check_document_file_size'),
        sa.CheckConstraint("processing_status IN ('pending', 'processing', 'completed', 'failed')", name='check_processing_status'),
    )
    
    # Create upload_sessions table for tracking bulk uploads
    op.create_table(
        'upload_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),  # Reference to user in identity service
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True),  # Reference to organization in identity service
        sa.Column('session_type', sa.String(20), nullable=False),
        sa.Column('total_files', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('processed_files', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('failed_files', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('session_metadata', postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("session_type IN ('single', 'bulk')", name='check_session_type'),
        sa.CheckConstraint("status IN ('pending', 'processing', 'completed', 'failed')", name='check_upload_status'),
    )
    
    # Create indexes for performance
    op.create_index('idx_documents_user_id', 'documents', ['user_id'])
    op.create_index('idx_documents_organization_id', 'documents', ['organization_id'])
    op.create_index('idx_documents_file_type', 'documents', ['file_type'])
    op.create_index('idx_documents_created_at', 'documents', ['created_at'])
    op.create_index('idx_upload_sessions_user_id', 'upload_sessions', ['user_id'])
    op.create_index('idx_upload_sessions_status', 'upload_sessions', ['status'])
    
    # Create update triggers for updated_at columns
    op.execute('''
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    ''')
    
    op.execute('CREATE TRIGGER update_documents_updated_at BEFORE UPDATE ON documents FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()')
    op.execute('CREATE TRIGGER update_upload_sessions_updated_at BEFORE UPDATE ON upload_sessions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()')


def downgrade() -> None:
    # Drop triggers
    op.execute('DROP TRIGGER IF EXISTS update_upload_sessions_updated_at ON upload_sessions')
    op.execute('DROP TRIGGER IF EXISTS update_documents_updated_at ON documents')
    op.execute('DROP FUNCTION IF EXISTS update_updated_at_column()')
    
    # Drop indexes
    op.drop_index('idx_upload_sessions_status', 'upload_sessions')
    op.drop_index('idx_upload_sessions_user_id', 'upload_sessions')
    op.drop_index('idx_documents_created_at', 'documents')
    op.drop_index('idx_documents_file_type', 'documents')
    op.drop_index('idx_documents_organization_id', 'documents')
    op.drop_index('idx_documents_user_id', 'documents')
    
    # Drop tables
    op.drop_table('upload_sessions')
    op.drop_table('documents')