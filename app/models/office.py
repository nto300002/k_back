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
from app.models.enums import OfficeType, BillingStatus

class Office(Base):
    """事業所"""
    __tablename__ = 'offices'
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255))
    is_group: Mapped[bool] = mapped_column(Boolean, default=False)
    office_type: Mapped[OfficeType] = mapped_column(SQLAlchemyEnum(OfficeType, name="officetype"))
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey('staffs.id'))
    last_modified_by: Mapped[uuid.UUID] = mapped_column(ForeignKey('staffs.id'))
    billing_status: Mapped[BillingStatus] = mapped_column(
        SQLAlchemyEnum(BillingStatus, name="billingstatus"), default=BillingStatus.free, nullable=False
    )
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True)
    stripe_subscription_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True)
    deactivated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=datetime.datetime.now, onupdate=datetime.datetime.now)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=datetime.datetime.now)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=datetime.datetime.now, onupdate=datetime.datetime.now)

    # Office -> OfficeStaff (one-to-many)
    staff_associations: Mapped[List["OfficeStaff"]] = relationship(back_populates="office")

    staffs: Mapped[List["Staff"]] = relationship(
        secondary="office_staffs", back_populates="offices", viewonly=True
    )
    
    # Office -> office_welfare_recipients (one-to-many)
    # recipient_associations: Mapped[List["OfficeWelfareRecipient"]] = relationship(back_populates="office")

class OfficeStaff(Base):
    """スタッフと事業所の中間テーブル"""
    __tablename__ = 'office_staffs'
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    staff_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('staffs.id'))
    office_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('offices.id'))
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False) # メインの所属か
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=datetime.datetime.now)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=datetime.datetime.now, onupdate=datetime.datetime.now)

    # OfficeStaff -> Staff (many-to-one)
    staff: Mapped["Staff"] = relationship(back_populates="office_associations")
    # OfficeStaff -> Office (many-to-one)
    office: Mapped["Office"] = relationship(back_populates="staff_associations")