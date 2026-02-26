from datetime import timezone, datetime
from sqlalchemy import String, Integer, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base

class Document(Base):
    __tablename__= "documents"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    document_type_id: Mapped[int] = mapped_column(Integer, ForeignKey("document_types.id", ondelete="SET NULL"), nullable=True)
    filename: Mapped[str] = mapped_column(String, nullable=False)
    file_path: Mapped[str] = mapped_column(String, nullable=False)
    # Progress: extracting => analyzing => completed
    ai_progress: Mapped[str] = mapped_column(String, nullable=False, default="pending")
    summary: Mapped[str] = mapped_column(String, nullable=True)
    risk_level: Mapped[str] = mapped_column(String, nullable=True)
    risk_reasoning: Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))

    document_type = relationship("DocumentType", back_populates="documents")