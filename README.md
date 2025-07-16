# k_back

## 要件定義
はい、承知いたしました。
アプリケーション「ケイカくん」のバックエンド（FastAPI）について、これまでの議論を全て統合し、最終的な詳細設計として出力します。

---

### **バックエンド詳細設計書: ケイカくん**

**1. バックエンドにおける各層の責務定義**

品質と保守性の高いコードを維持するため、各層の役割を以下のように厳格に定義する。

*   **`api` 層 (エンドポイント)**
    *   **責務**: HTTPリクエストの受付とレスポンスの返却。認証・認可（`Depends`）、リクエスト内容の検証。対応する`services`層のメソッドを呼び出す。
    *   **禁止事項**: ビジネスロジックの実装、`crud`層の直接呼び出し。

*   **`services` 層 (ビジネスロジック)**
    *   **責務**: アプリケーション固有のユースケースを実装する。複数の`crud`処理を組み合わせ、一連のビジネスプロセスを構成する。トランザクション管理。
    *   **禁止事項**: データベースのテーブル構造に直接依存した処理。

*   **`crud` 層 (データベースアクセス)**
    *   **責務**: **単一のモデル（テーブル）に対する**、基本的なCRUD（作成, 読込, 更新, 削除）操作のみを提供する。
    *   **禁止事項**: ビジネスロジックの実装、複数のモデルにまたがる複雑な更新。

*   **`schemas` 層 (データ構造定義)**
    *   **責務**: APIの入出力や層間でデータをやり取りするための厳格なデータ構造（DTO）をPydanticを用いて定義する。
    *   **禁止事項**: バリデーション以外のロジックの実装。

**2. インポート規約**

*   **一方向の依存**: `api` → `services` → `crud`という一方向の依存関係を徹底する。逆方向のインポートは禁止する。
*   **`crud`層の呼び出し**: `services`層から`crud`層のメソッドを呼び出す際は、必ず`from app import crud`としてトップレベルのパッケージをインポートし、`crud.crud_オブジェクト名.メソッド()`の形式で呼び出す。

---

### **3. APIエンドポイント一覧 (v1)**

| リソース | エンドポイントURL | HTTPメソッド | 機能概要 |
| :--- | :--- | :--- | :--- |
| **認証 (Auth)** | `/api/v1/auth/login` | `POST` | メール/パスワードでログインしトークン取得 |
| | `/api/v1/auth/signup-admin` | `POST` | Service Administratorとして新規登録 |
| **スタッフ (Staff)** | `/api/v1/staff/me` | `GET`, `PATCH` | 自身のプロフィール情報を取得・更新 |
| | `/api/v1/staff/invite` | `POST` | スタッフを事業所に招待 |
| **事業所 (Office)**| `/api/v1/offices` | `POST` | Service Administratorが最初の事業所を作成 |
| **ダッシュボード**| `/api/v1/dashboard` | `GET` | ダッシュボード情報を一括取得 |
| **利用者 (Recipient)**| `/api/v1/recipients` | `POST` | 新規利用者を作成し、最初の計画サイクルを生成 |
| | `/api/v1/recipients/{recipient_id}` | `GET`, `PATCH`, `DELETE`| 特定利用者の情報を取得・更新・削除 |
| **計画 (Plan)**| `/api/v1/recipients/{recipient_id}/plans`| `GET` | 特定利用者の全計画サイクル情報を取得 |
| **成果物 (Deliverable)**| `/api/v1/plan-deliverables` | `POST` | 計画の成果物(PDF)をアップロード |
| | `/api/v1/assessment-sheets` | `POST` | アセスメントシート(PDF)をアップロード |
| | `/api/v1/recipients/{id}/documents`| `GET` | 全ての成果物PDFのプレビューURLを取得 |
| **申請 (Request)**| `/api/v1/requests/role-change` | `POST` | 自身の権限変更を申請 |
| | `/api/v1/requests/approval` | `POST` | `employee`が各種操作の承認を申請 |
| **通知 (Notice)**| `/api/v1/notices` | `GET` | 自身宛の通知（受信リクエスト）一覧を取得 |
| | `/api/v1/notices/{notice_id}/approve`| `PATCH` | 受け取ったリクエストを承認 |
| **決済 (Stripe)**| `/api/v1/stripe/create-checkout-session`| `POST` | Stripe Checkoutセッションを作成 |
| | `/api/v1/stripe/create-customer-portal-session`| `POST` | Stripeカスタマーポータルセッションを作成 |
| | `/api/v1/stripe/webhook` | `POST` | StripeからのWebhookイベントを受信 |
| **MFA** | `/api/v1/mfa/enroll` | `POST` | MFAの有効化プロセスを開始 |

---

### **4. バックエンドのルーティング (`main.py`と`api.py`)**

アプリケーションのルーティングは、`main.py`と`app/api/v1/api.py`で管理します。

#### **ファイル: `app/main.py`** (アプリケーションのエントリーポイント)

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.api import api_router
from app.core.config import settings

app = FastAPI(title=settings.PROJECT_NAME)

# CORSミドルウェアの設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# APIルーターをインクルード
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
def read_root():
    return {"message": "Welcome to Keikakun API"}```

#### **ファイル: `app/api/v1/api.py`** (v1 APIの集約ルーター)

from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth, staff, offices, dashboard, recipients, support_plan,
    assessment, documents, requests, notices, stripe, mfa
)

api_router = APIRouter()

# 各エンドポイントのルーターを登録
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(staff.router, prefix="/staff", tags=["Staff"])
api_router.include_router(offices.router, prefix="/offices", tags=["Offices"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(recipients.router, prefix="/recipients", tags=["Recipients"])
api_router.include_router(support_plan.router, tags=["Support Plan"])
api_router.include_router(assessment.router, tags=["Assessment"])
api_router.include_router(documents.router, tags=["Documents"])
api_router.include_router(requests.router, prefix="/requests", tags=["Requests"])
api_router.include_router(notices.router, prefix="/notices", tags=["Notices"])
api_router.include_router(stripe.router, prefix="/stripe", tags=["Stripe"])
api_router.include_router(mfa.router, prefix="/mfa", tags=["MFA"])
```
*`support_plan.router`には`/plan-deliverables`のようなエンドポイントが含まれるため、プレフィックスなしで登録します。*
## model
python

```py
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
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)

# --- Enum定義 ---
# Pythonのenumを定義し、SQLのENUM型と連携させるのがベストプラクティスです
class StaffRole(enum.Enum):
    employee = 'employee'
    manager = 'manager'
    service_administrator = 'service_administrator'

class OfficeType(enum.Enum):
    transition_to_employment = 'transition_to_employment'
    type_B_office = 'type_B_office'
    type_A_office = 'type_A_office'

class GenderType(enum.Enum):
    male = 'male'
    female = 'female'
    other = 'other'

class SupportPlanStep(enum.Enum):
    assessment = 'assessment'
    draft_plan = 'draft_plan'
    staff_meeting = 'staff_meeting'
    final_plan_signed = 'final_plan_signed'
    monitoring = 'monitoring'

class DeliverableType(enum.Enum):
    assessment_sheet = 'assessment_sheet'
    draft_plan_pdf = 'draft_plan_pdf'
    staff_meeting_minutes = 'staff_meeting_minutes'
    final_plan_signed_pdf = 'final_plan_signed_pdf'
    monitoring_report_pdf = 'monitoring_report_pdf'

class AssessmentSheetType(enum.Enum):
    """アセスメントシートの種類"""
    basic_info = '1-1.基本情報'
    employment_info = '1-2.就労関係'
    issue_analysis = '2.課題分析'

# --- Baseクラスの定義 ---
class Base(DeclarativeBase):
    pass

# --- モデル定義 ---

class Staff(Base):
    """スタッフ"""
    __tablename__ = 'staffs'
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    name: Mapped[str] = mapped_column(String(255))
    role: Mapped[StaffRole] = mapped_column(SQLAlchemyEnum(StaffRole), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Staff -> OfficeStaff (one-to-many)
    office_associations: Mapped[List["OfficeStaff"]] = relationship(back_populates="staff")

class Office(Base):
    """事業所"""
    __tablename__ = 'offices'
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    name: Mapped[str] = mapped_column(String(255))
    is_group: Mapped[bool] = mapped_column(Boolean, default=False)
    type: Mapped[OfficeType] = mapped_column(SQLAlchemyEnum(OfficeType))
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey('staffs.id'))
    last_modified_by: Mapped[uuid.UUID] = mapped_column(ForeignKey('staffs.id'))
    billing_status: Mapped[BillingStatus] = mapped_column(
        SQLAlchemyEnum(BillingStatus), default=BillingStatus.free, nullable=False
    )
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True)
    stripe_subscription_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True)
    deactivated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Office -> OfficeStaff (one-to-many)
    staff_associations: Mapped[List["OfficeStaff"]] = relationship(back_populates="office")
    
    # Office -> office_welfare_recipients (one-to-many)
    recipient_associations: Mapped[List["OfficeWelfareRecipient"]] = relationship(back_populates="office")

class OfficeStaff(Base):
    """スタッフと事業所の中間テーブル"""
    __tablename__ = 'office_staffs'
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    staff_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('staffs.id'))
    office_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('offices.id'))
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False) # メインの所属か
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # OfficeStaff -> Staff (many-to-one)
    staff: Mapped["Staff"] = relationship(back_populates="office_associations")
    # OfficeStaff -> Office (many-to-one)
    office: Mapped["Office"] = relationship(back_populates="staff_associations")

class WelfareRecipient(Base):
    """受給者"""
    __tablename__ = 'welfare_recipients'
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    first_name: Mapped[str] = mapped_column(String(255))
    last_name: Mapped[str] = mapped_column(String(255))
    furigana: Mapped[str] = mapped_column(String(255))
    birth_day: Mapped[datetime.date]
    gender: Mapped[GenderType] = mapped_column(SQLAlchemyEnum(GenderType))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # WelfareRecipient -> OfficeWelfareRecipient (one-to-many)
    office_associations: Mapped[List["OfficeWelfareRecipient"]] = relationship(back_populates="welfare_recipient")
    # WelfareRecipient -> SupportPlanCycle (one-to-many)
    support_plan_cycles: Mapped[List["SupportPlanCycle"]] = relationship(back_populates="welfare_recipient")
    assessment_sheets: Mapped[List["AssessmentSheetDeliverable"]] = relationship(back_populates="welfare_recipient")


class OfficeWelfareRecipient(Base):
    """事業所と受給者の中間テーブル"""
    __tablename__ = 'office_welfare_recipients'
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    welfare_recipient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('welfare_recipients.id'))
    office_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('offices.id'))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # OfficeWelfareRecipient -> WelfareRecipient (many-to-one)
    welfare_recipient: Mapped["WelfareRecipient"] = relationship(back_populates="office_associations")
    # OfficeWelfareRecipient -> Office (many-to-one)
    office: Mapped["Office"] = relationship(back_populates="recipient_associations")

class SupportPlanCycle(Base):
    """個別支援計画の1サイクル（約6ヶ月）"""
    __tablename__ = 'support_plan_cycles'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    welfare_recipient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('welfare_recipients.id'))
    plan_cycle_start_date: Mapped[datetime.date]
    final_plan_signed_date: Mapped[Optional[datetime.date]]
    next_renewal_deadline: Mapped[Optional[datetime.date]]
    is_latest_cycle: Mapped[bool] = mapped_column(Boolean, default=True)
    google_calendar_id: Mapped[Optional[str]] = mapped_column(Text)
    google_event_id: Mapped[Optional[str]] = mapped_column(Text)
    google_event_url: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # SupportPlanCycle -> WelfareRecipient (many-to-one)
    welfare_recipient: Mapped["WelfareRecipient"] = relationship(back_populates="support_plan_cycles")
    # SupportPlanCycle -> SupportPlanStatus (one-to-many)
    statuses: Mapped[List["SupportPlanStatus"]] = relationship(back_populates="plan_cycle")
    # SupportPlanCycle -> PlanDeliverable (one-to-many)
    deliverables: Mapped[List["PlanDeliverable"]] = relationship(back_populates="plan_cycle")

class SupportPlanStatus(Base):
    """計画サイクル内の各ステップの進捗"""
    __tablename__ = 'support_plan_statuses'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plan_cycle_id: Mapped[int] = mapped_column(ForeignKey('support_plan_cycles.id'))
    step_type: Mapped[SupportPlanStep] = mapped_column(SQLAlchemyEnum(SupportPlanStep))
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    completed_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True))
    completed_by: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey('staffs.id'))
    monitoring_deadline: Mapped[Optional[int]] # default = 7
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # SupportPlanStatus -> SupportPlanCycle (many-to-one)
    plan_cycle: Mapped["SupportPlanCycle"] = relationship(back_populates="statuses")

class PlanDeliverable(Base):
    """計画サイクルに関連する成果物"""
    __tablename__ = 'plan_deliverables'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plan_cycle_id: Mapped[int] = mapped_column(ForeignKey('support_plan_cycles.id'))
    deliverable_type: Mapped[DeliverableType] = mapped_column(SQLAlchemyEnum(DeliverableType))
    file_path: Mapped[str] = mapped_column(Text)
    original_filename: Mapped[str] = mapped_column(Text)
    uploaded_by: Mapped[uuid.UUID] = mapped_column(ForeignKey('staffs.id'))
    uploaded_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # PlanDeliverable -> SupportPlanCycle (many-to-one)
    plan_cycle: Mapped["SupportPlanCycle"] = relationship(back_populates="deliverables")

class AssessmentSheetDeliverable(Base):
    """アセスメントシートの成果物（アップロードされたファイル）"""
    __tablename__ = 'assessment_sheet_deliverables'

    id: Mapped[int] = mapped_column(primary_key=True)
    welfare_recipient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('welfare_recipients.id'))
    assessment_type: Mapped[AssessmentSheetType] = mapped_column(SQLAlchemyEnum(AssessmentSheetType), nullable=False)
    
    file_path: Mapped[str] = mapped_column(Text)
    original_filename: Mapped[str] = mapped_column(Text)
    uploaded_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('staffs.id'))
    uploaded_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # 関係性: AssessmentSheetDeliverable -> WelfareRecipient (多対一)
    welfare_recipient: Mapped["WelfareRecipient"] = relationship(back_populates="assessment_sheets")

# Noticeは他の多くのテーブルと関連するため最後に定義
class Notice(Base):
    """お知らせ"""
    __tablename__ = 'notices'
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    recipient_staff_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('staffs.id')) # 通知の受信者
    office_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('offices.id'))
    type: Mapped[str] = mapped_column(String(50))
    title: Mapped[str] = mapped_column(String(255))
    content: Mapped[Optional[str]] = mapped_column(Text)
    link_url: Mapped[Optional[str]] = mapped_column(String(255))
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())



class RequestStatus(enum.Enum):
    pending = 'pending'
    approved = 'approved'
    rejected = 'rejected'

class RoleChangeRequest(Base):
    """権限変更の申請"""
    __tablename__ = 'role_change_requests'
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    requester_staff_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('staffs.id'))
    office_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('offices.id'))
    requested_role: Mapped[StaffRole] = mapped_column(SQLAlchemyEnum(StaffRole), nullable=False)
    status: Mapped[RequestStatus] = mapped_column(SQLAlchemyEnum(RequestStatus), default=RequestStatus.pending)
    request_notes: Mapped[Optional[str]] = mapped_column(Text)
    reviewed_by_staff_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey('staffs.id'))
    reviewed_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True))
    reviewer_notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 関係性を定義
    requester: Mapped["Staff"] = relationship(foreign_keys=[requester_staff_id])
    reviewer: Mapped[Optional["Staff"]] = relationship(foreign_keys=[reviewed_by_staff_id])
```


---
## 以下 not MVP

```py
## 1-1 アセスメントシート 基本情報

import datetime
import enum
import uuid
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SQLAlchemyEnum,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)

# 既存のBaseクラスを想定
class Base(DeclarativeBase):
    pass

# --- Enum定義 ---

class FormOfResidence(enum.Enum):
    at_home_with_family = 'at_home_with_family'
    alone_at_home = 'alone_at_home'
    hospital = 'hospital'
    support_facilities_for_the_disabled = 'support_facilities_for_the_disabled'
    no_nursing_care_in_a_group_home = 'no_nursing_care_in_a_group_home'
    group_home_with_nursing_care = 'group_home_with_nursing_care'
    other_option = 'other_option'

class MeansOfTransportation(enum.Enum):
    train = 'train'
    bus = 'bus'
    bicycle = 'bicycle'
    other_option = 'other_option'

class Household(enum.Enum):
    same = 'same'
    living_apart = 'living_apart'

class LivelihoodProtection(enum.Enum):
    yes_with_stranger_care_fee = 'yes_with_stranger_care_fee'
    yes_no_stranger_care_fee = 'yes_no_stranger_care_fee'
    no = 'no'

class DisabilityCategory(enum.Enum):
    physical_handicap_certificate = 'physical_handicap_certificate'
    rehabilitation_certificate = 'rehabilitation_certificate'
    mental_disability_welfare_certificate = 'mental_disability_welfare_certificate'
    basic_disability_pension = 'basic_disability_pension'
    other_disability_pension = 'other_disability_pension'
    other_handicap_or_disease = 'other_handicap_or_disease'

class PhysicalDisabilityType(enum.Enum):
    visual_impairment = 'visual_impairment'
    hearing_impairment = 'hearing_impairment'
    physical_disability = 'physical_disability'
    internal_disorder = 'internal_disorder'
    other_option = 'other_option'

class ApplicationStatus(enum.Enum):
    not_applicable = 'not_applicable'
    pending = 'pending'
    in_progress = 'in_progress'
    scheduled = 'scheduled'
    completed = 'completed'

class MedicalCareInsurance(enum.Enum):
    national_health_insurance = 'national_health_insurance'
    mutual_aid = 'mutual_aid'
    social_security = 'social_security'
    other_option = 'other_option'

class AidingType(enum.Enum):
    independence_support = 'independence_support'
    subsidy_for_the_severely_physically_and_mentally_handicapped = 'subsidy_for_the_severely_physically_and_mentally_handicapped'
    specific_diseases = 'specific_diseases'
    geriatrics = 'geriatrics'

class WorkConditions(enum.Enum):
    regular_work = 'regular_work'
    part_time_job = 'part_time_job'
    labor_transition_support = 'labor_transition_support'
    support_for_continuous_employment_A_B = 'support_for_continuous_employment_A_B'
    not_yet_employed = 'not_yet_employed'
    other_option = 'other_option'

class WorkOutsideFacility(enum.Enum):
    i_wish_to = 'i_wish_to'
    i_dont_want_to = 'i_dont_want_to'

# --- モデル定義 ---

class ServiceRecipientDetail(Base):
    """受給者の詳細情報 (基本情報)"""
    __tablename__ = 'service_recipient_details'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    welfare_recipient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('welfare_recipients.id'), unique=True)
    address: Mapped[str] = mapped_column(Text)
    form_of_residence: Mapped[FormOfResidence] = mapped_column(SQLAlchemyEnum(FormOfResidence))
    form_of_residence_other_text: Mapped[Optional[str]] = mapped_column(Text)
    means_of_transportation: Mapped[MeansOfTransportation] = mapped_column(SQLAlchemyEnum(MeansOfTransportation))
    means_of_transportation_other_text: Mapped[Optional[str]] = mapped_column(Text)
    tel: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 関係性: ServiceRecipientDetail -> WelfareRecipient (one-to-oneの逆側)
    welfare_recipient: Mapped["WelfareRecipient"] = relationship(back_populates="detail")
    # 関係性: ServiceRecipientDetail -> EmergencyContact (one-to-many)
    emergency_contacts: Mapped[List["EmergencyContact"]] = relationship(back_populates="service_recipient_detail")

class EmergencyContact(Base):
    """緊急連絡先"""
    __tablename__ = 'emergency_contacts'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    service_recipient_detail_id: Mapped[int] = mapped_column(ForeignKey('service_recipient_details.id'))
    address: Mapped[str] = mapped_column(Text)
    name: Mapped[str] = mapped_column(Text)
    relation: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 関係性: EmergencyContact -> ServiceRecipientDetail (many-to-one)
    service_recipient_detail: Mapped["ServiceRecipientDetail"] = relationship(back_populates="emergency_contacts")

class FamilyOfServiceRecipients(Base):
    """家族構成"""
    __tablename__ = 'family_of_service_recipients'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    welfare_recipient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('welfare_recipients.id'))
    name: Mapped[str] = mapped_column(Text)
    relationship: Mapped[str] = mapped_column(Text)
    household: Mapped[Household] = mapped_column(SQLAlchemyEnum(Household))
    ones_health: Mapped[str] = mapped_column(Text)
    remarks: Mapped[Optional[str]] = mapped_column(Text)
    family_structure_chart: Mapped[Optional[str]] = mapped_column(Text) # URL or path
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 関係性: FamilyOfServiceRecipients -> WelfareRecipient (many-to-one)
    welfare_recipient: Mapped["WelfareRecipient"] = relationship(back_populates="family_members")

class DisabilityStatus(Base):
    """障害についての基本情報"""
    __tablename__ = 'disability_statuses'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    welfare_recipient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('welfare_recipients.id'), unique=True)
    disability_or_disease_name: Mapped[str] = mapped_column(Text)
    livelihood_protection: Mapped[LivelihoodProtection] = mapped_column(SQLAlchemyEnum(LivelihoodProtection))
    special_remarks: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 関係性: DisabilityStatus -> WelfareRecipient (one-to-oneの逆側)
    welfare_recipient: Mapped["WelfareRecipient"] = relationship(back_populates="disability_status")
    # 関係性: DisabilityStatus -> DisabilityDetail (one-to-many)
    details: Mapped[List["DisabilityDetail"]] = relationship(back_populates="disability_status")

class DisabilityDetail(Base):
    """個別の障害・手帳・年金の詳細"""
    __tablename__ = 'disability_details'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    disability_status_id: Mapped[int] = mapped_column(ForeignKey('disability_statuses.id'))
    category: Mapped[DisabilityCategory] = mapped_column(SQLAlchemyEnum(DisabilityCategory))
    grade_or_level: Mapped[Optional[str]] = mapped_column(Text)
    physical_disability_type: Mapped[Optional[PhysicalDisabilityType]] = mapped_column(SQLAlchemyEnum(PhysicalDisabilityType))
    physical_disability_type_other_text: Mapped[Optional[str]] = mapped_column(Text)
    application_status: Mapped[ApplicationStatus] = mapped_column(SQLAlchemyEnum(ApplicationStatus))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 関係性: DisabilityDetail -> DisabilityStatus (many-to-one)
    disability_status: Mapped["DisabilityStatus"] = relationship(back_populates="details")

class WelfareServicesUsed(Base):
    """過去のサービス利用歴"""
    __tablename__ = 'welfare_services_used'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    welfare_recipient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('welfare_recipients.id'))
    office_name: Mapped[str] = mapped_column(Text)
    starting_day: Mapped[datetime.date]
    amount_used: Mapped[str] = mapped_column(Text)
    service_name: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 関係性: WelfareServicesUsed -> WelfareRecipient (many-to-one)
    welfare_recipient: Mapped["WelfareRecipient"] = relationship(back_populates="service_history")

class MedicalMatters(Base):
    """医療に関する基本情報"""
    __tablename__ = 'medical_matters'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    welfare_recipient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('welfare_recipients.id'), unique=True)
    medical_care_insurance: Mapped[MedicalCareInsurance] = mapped_column(SQLAlchemyEnum(MedicalCareInsurance))
    medical_care_insurance_other_text: Mapped[Optional[str]] = mapped_column(Text)
    aiding: Mapped[AidingType] = mapped_column(SQLAlchemyEnum(AidingType))
    history_of_hospitalization_in_the_past_2_years: Mapped[bool] = mapped_column(Boolean)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 関係性: MedicalMatters -> WelfareRecipient (one-to-oneの逆側)
    welfare_recipient: Mapped["WelfareRecipient"] = relationship(back_populates="medical_matters")
    # 関係性: MedicalMatters -> HistoryOfHospitalVisits (one-to-many)
    hospital_visits: Mapped[List["HistoryOfHospitalVisits"]] = relationship(back_populates="medical_matters")

class HistoryOfHospitalVisits(Base):
    """通院歴"""
    __tablename__ = 'history_of_hospital_visits'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    medical_matters_id: Mapped[int] = mapped_column(ForeignKey('medical_matters.id'))
    disease: Mapped[str] = mapped_column(Text)
    frequency_of_hospital_visits: Mapped[str] = mapped_column(Text)
    symptoms: Mapped[str] = mapped_column(Text)
    medical_institution: Mapped[str] = mapped_column(Text)
    doctor: Mapped[str] = mapped_column(Text)
    tel: Mapped[str] = mapped_column(Text)
    taking_medicine: Mapped[bool] = mapped_column(Boolean)
    date_started: Mapped[Optional[datetime.date]]
    date_ended: Mapped[Optional[datetime.date]]
    special_remarks: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 関係性: HistoryOfHospitalVisits -> MedicalMatters (many-to-one)
    medical_matters: Mapped["MedicalMatters"] = relationship(back_populates="hospital_visits")

class EmploymentRelated(Base):
    """就労関係"""
    __tablename__ = 'employment_related'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    welfare_recipient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('welfare_recipients.id'), unique=True)
    created_by_staff_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('staffs.id'))
    work_conditions: Mapped[WorkConditions] = mapped_column(SQLAlchemyEnum(WorkConditions))
    regular_or_part_time_job: Mapped[bool]
    employment_support: Mapped[bool]
    work_experience_in_the_past_year: Mapped[bool]
    suspension_of_work: Mapped[bool]
    qualifications: Mapped[Optional[str]] = mapped_column(Text)
    main_places_of_employment: Mapped[Optional[str]] = mapped_column(Text)
    general_employment_request: Mapped[bool]
    desired_job: Mapped[Optional[str]] = mapped_column(Text)
    special_remarks: Mapped[Optional[str]] = mapped_column(Text)
    work_outside_the_facility: Mapped[WorkOutsideFacility] = mapped_column(SQLAlchemyEnum(WorkOutsideFacility))
    special_note_about_working_outside_the_facility: Mapped[Optional[str]] = mapped_column(Text)

    # 関係性
    welfare_recipient: Mapped["WelfareRecipient"] = relationship(back_populates="employment_related")

class IssueAnalysis(Base):
    """課題分析"""
    __tablename__ = 'issue_analyses'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    welfare_recipient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('welfare_recipients.id'), unique=True)
    created_by_staff_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('staffs.id'))
    what_i_like_to_do: Mapped[Optional[str]] = mapped_column(Text)
    im_not_good_at: Mapped[Optional[str]] = mapped_column(Text)
    the_life_i_want: Mapped[Optional[str]] = mapped_column(Text)
    the_support_i_want: Mapped[Optional[str]] = mapped_column(Text)
    points_to_keep_in_mind_when_providing_support: Mapped[Optional[str]] = mapped_column(Text)
    future_dreams: Mapped[Optional[str]] = mapped_column(Text)
    other: Mapped[Optional[str]] = mapped_column(Text)

    # 関係性
    welfare_recipient: Mapped["WelfareRecipient"] = relationship(back_populates="issue_analysis")

# --- 既存モデルへのリレーションシップ追加 ---
# 上記のモデルと連携するために、既存の`WelfareRecipient`モデルに
# `relationship`を追加する必要があります。

class WelfareRecipient(Base):
    """
    受給者 (アセスメントシート関連のrelationshipを追加)
    ※既存の定義に以下を追加・統合してください
    """
    __tablename__ = 'welfare_recipients'
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    # ... 既存のカラム定義 ...

    # --- アセスメントシート関連の新しいリレーションシップ ---
    detail: Mapped[Optional["ServiceRecipientDetail"]] = relationship(back_populates="welfare_recipient", cascade="all, delete-orphan")
    family_members: Mapped[List["FamilyOfServiceRecipients"]] = relationship(back_populates="welfare_recipient", cascade="all, delete-orphan")
    disability_status: Mapped[Optional["DisabilityStatus"]] = relationship(back_populates="welfare_recipient", cascade="all, delete-orphan")
    service_history: Mapped[List["WelfareServicesUsed"]] = relationship(back_populates="welfare_recipient", cascade="all, delete-orphan")
    medical_matters: Mapped[Optional["MedicalMatters"]] = relationship(back_populates="welfare_recipient", cascade="all, delete-orphan")
    employment_related: Mapped[Optional["EmploymentRelated"]] = relationship(back_populates="welfare_recipient", cascade="all, delete-orphan")
    issue_analysis: Mapped[Optional["IssueAnalysis"]] = relationship(back_populates="welfare_recipient", cascade="all, delete-orphan")

    # ... 既存のリレーションシップ定義 ...
```