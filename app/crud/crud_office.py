from typing import List, Optional
import uuid
import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.crud.base import CRUDBase
from app.models.office import Office, OfficeStaff
from app.models.staff import Staff
from app.schemas.office import OfficeCreate, OfficeResponse


class CRUDOffice(CRUDBase[Office, OfficeCreate, OfficeResponse]):
    async def create_with_owner(
        self, db: AsyncSession, *, obj_in: OfficeCreate, user: Staff
    ) -> Office:
        """
        Officeを作成し、作成者をOfficeStaffとして関連付けます。
        """
        # Officeオブジェクトを作成
        db_office = Office(
            name=obj_in.name,
            office_type=obj_in.office_type,
            created_by=user.id,
            last_modified_by=user.id,
        )
        db.add(db_office)
        await db.flush()  # まずOfficeをDBにINSERTし、IDを確定させる

        # OfficeStaff関係を作成
        office_staff = OfficeStaff(
            staff_id=user.id,
            office_id=db_office.id, # 確定したIDを使用
            is_primary=True,
        )
        db.add(office_staff)
        
        await db.commit() # トランザクションをコミット
        await db.refresh(db_office) # 返却するオブジェクトの状態を最新化する

        return db_office

    async def get_with_staff(self, db: AsyncSession, *, office_id: UUID) -> Optional[Office]:
        stmt = (
            select(Office)
            .options(selectinload(Office.staff_associations))
            .where(Office.id == office_id)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_offices_by_staff(self, db: AsyncSession, *, staff_id: UUID) -> List[Office]:
        stmt = (
            select(Office)
            .join(OfficeStaff)
            .where(OfficeStaff.staff_id == staff_id)
        )
        result = await db.execute(stmt)
        return result.scalars().all()


crud_office = CRUDOffice(Office)