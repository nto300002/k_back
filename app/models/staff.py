import datetime
import enum
import uuid
from typing import List, Optional

from sqlalchemy import (
    create_engine,
    DateTime,
    ForeignKey,
    String,
    Text,
    func,
    Enum as SQLAlchemyEnum,
    Boolean,
    Integer,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.db.base import Base
from app.models.enums import StaffRole

class Staff(Base):
    """スタッフ"""
    __tablename__ = 'staffs'
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255))
    role: Mapped[StaffRole] = mapped_column(SQLAlchemyEnum(StaffRole, name="staffrole"), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=datetime.datetime.now)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=datetime.datetime.now, onupdate=datetime.datetime.now)
    
    # Staff -> OfficeStaff (one-to-many)
    office_associations: Mapped[List["OfficeStaff"]] = relationship(back_populates="staff")

    offices: Mapped[List["Office"]] = relationship(
        secondary="office_staffs", back_populates="staffs", viewonly=True
    )