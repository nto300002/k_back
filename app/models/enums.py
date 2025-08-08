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

class StaffRole(enum.Enum):
    employee = 'employee'
    manager = 'manager'
    service_administrator = 'service_administrator'
    general_user = 'general_user' # test用のロール

class OfficeType(enum.Enum):
    transition_to_employment = 'transition_to_employment'
    type_B_office = 'type_B_office'
    type_A_office = 'type_A_office'

class RequestStatus(enum.Enum):
   pending = 'pending'
   approved = 'approved'
   rejected = 'rejected'

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

class BillingStatus(enum.Enum):
    free = 'free'          
    active = 'active'       
    past_due = 'past_due'   
    canceled = 'canceled'   