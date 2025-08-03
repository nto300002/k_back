import pytest
from pydantic import ValidationError

from app.schemas.token import Token
from app.schemas.staff import LoginRequest, AdminSignupRequest, StaffInviteRequest
from app.schemas.office import OfficeCreate
from app.models.enums import StaffRole, OfficeType

# --- Token Schema Tests ---
def test_valid_token_schema():
    """正常系: Tokenスキーマが正しく作成される"""
    data = {
        "access_token": "access_token_string",
        "refresh_token": "refresh_token_string",
        "token_type": "bearer"
    }
    token = Token(**data)
    assert token.access_token == data["access_token"]
    assert token.token_type == "bearer"

def test_token_schema_missing_field():
    """異常系: Tokenスキーマで必須フィールドが欠落している"""
    with pytest.raises(ValidationError, match="access_token"):
        Token(refresh_token="some_token", token_type="bearer")


# --- LoginRequest Schema Tests ---
def test_valid_login_request():
    """正常系: LoginRequestスキーマが正しく作成される"""
    data = {"email": "test@example.com", "password": "password123"}
    req = LoginRequest(**data)
    assert req.email == data["email"]

def test_login_request_invalid_email():
    """異常系: LoginRequestでメールアドレスの形式が不正"""
    with pytest.raises(ValidationError, match="email"):
        LoginRequest(email="invalid-email", password="password123")


# --- AdminSignupRequest Schema Tests ---
def test_valid_admin_signup_request():
    """正常系: AdminSignupRequestスキーマが正しく作成される"""
    data = {"name": "管理者", "email": "admin@example.com", "password": "password123"}
    req = AdminSignupRequest(**data)
    assert req.name == data["name"]

def test_admin_signup_request_missing_name():
    """異常系: AdminSignupRequestで名前が欠落している"""
    with pytest.raises(ValidationError, match="name"):
        AdminSignupRequest(email="admin@example.com", password="password123")


# --- StaffInviteRequest Schema Tests ---
def test_valid_staff_invite_request():
    """正常系: StaffInviteRequestスキーマが正しく作成される"""
    data = {"email": "new_staff@example.com", "role": StaffRole.employee}
    req = StaffInviteRequest(**data)
    assert req.role == StaffRole.employee

def test_staff_invite_request_invalid_role():
    """異常系: StaffInviteRequestでroleが不正な値"""
    with pytest.raises(ValidationError, match="role"):
        StaffInviteRequest(email="new_staff@example.com", role="invalid_role")


# --- OfficeCreate Schema Tests ---
def test_valid_office_create_request():
    """正常系: OfficeCreateスキーマが正しく作成される"""
    data = {"name": "新しい事業所", "office_type": "type_A_office", "created_by": "123e4567-e89b-12d3-a456-426614174000", "last_modified_by": "123e4567-e89b-12d3-a456-426614174000"}
    req = OfficeCreate(**data)
    assert req.name == data["name"]
    assert req.office_type == OfficeType.type_A_office

def test_office_create_request_missing_name():
    """異常系: OfficeCreateで名前が欠落している"""
    with pytest.raises(ValidationError, match="name"):
        OfficeCreate(office_type="type_A_office")

def test_office_create_request_missing_office_type():
    """異常系: OfficeCreateでoffice_typeが欠落している"""
    with pytest.raises(ValidationError, match="office_type"):
        OfficeCreate(name="新しい事業所")