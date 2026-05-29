import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import declarative_base
from pgvector.sqlalchemy import Vector

Base = declarative_base()


class Report(Base):
    __tablename__ = "reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    patient_id = Column(String, index=True)
    raw_text = Column(Text, nullable=False)
    parsed_payload = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)


class WorkflowRun(Base):
    __tablename__ = "workflow_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id = Column(String, unique=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    state_snapshot = Column(JSONB)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MemoryEntry(Base):
    __tablename__ = "memory_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    patient_id = Column(String, index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), index=True)
    request_id = Column(String, index=True)
    layer = Column(String, index=True, default="long_term")
    kind = Column(String, index=True, default="workflow_summary")
    scope = Column(String, index=True, default="patient")
    content = Column(JSONB)
    summary = Column(Text)
    embedding = Column(Vector(1024))
    expires_at = Column(DateTime, index=True)
    importance = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    display_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    title = Column(String, nullable=True)
    conversation_metadata = Column("metadata", JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)


class AgentLog(Base):
    __tablename__ = "agent_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_run_id = Column(UUID(as_uuid=True), ForeignKey("workflow_runs.id"), index=True)
    agent_name = Column(String, index=True)
    input_payload = Column(JSONB)
    output_payload = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)


class ValidationHistory(Base):
    __tablename__ = "validation_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_run_id = Column(UUID(as_uuid=True), ForeignKey("workflow_runs.id"), index=True)
    request_id = Column(String, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    patient_id = Column(String, index=True)
    stage = Column(String, index=True)
    passed = Column(Boolean, default=False)
    score = Column(JSONB)
    issues = Column(JSONB)
    output_payload = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)


class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source = Column(String, index=True)
    source_type = Column(String, index=True)
    chunk_id = Column(String, unique=True, index=True)
    chunk_index = Column(Integer)
    page_number = Column(Integer)
    content_hash = Column(String, index=True)
    content = Column(Text, nullable=False)
    document_metadata = Column("metadata", JSONB)
    embedding = Column(Vector(1024))
    created_at = Column(DateTime, default=datetime.utcnow)
