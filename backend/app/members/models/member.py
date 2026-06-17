from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import EmailStr
from sqlalchemy import JSON
from sqlmodel import Field, Relationship, select
from sqlmodel.sql._expression_select_cls import SelectOfScalar
from starlette.requests import Request

from app.auth.models import User, UserBasic, UserType
from app.common.fields import EnumField, FKField, UTCDatetimeField
from app.common.models import AppModel
from app.core.database import DBSession


class DeliveryMode(str, Enum):
    """How a member delivers tuition."""

    ONLINE = 'online'
    IN_PERSON = 'in_person'
    BOTH = 'both'


class VerificationStatus(str, Enum):
    """Whether staff have verified the member's identity/eligibility."""

    PROCESSING = 'processing'
    VERIFIED = 'verified'


class ComplianceRAG(str, Enum):
    """Compliance traffic light, computed from DBS / references / safeguarding (see issue #13)."""

    RED = 'red'
    AMBER = 'amber'
    GREEN = 'green'


class _Member(AppModel):
    """Shared, user-settable profile fields for a member.

    A member is a ``User`` of type ``MEMBER``; this profile holds the membership-specific data
    keyed 1:1 to that user. Name/email live on the ``User``, not here. Relations to Company,
    DBS, Membership, Tag, Reference and AuditEntry arrive with their own issues (#6–#12).
    """

    # Contact
    phone: Optional[str] = None
    whatsapp: Optional[str] = None
    # Home address
    address_line_1: Optional[str] = None
    address_line_2: Optional[str] = None
    city: Optional[str] = None
    postcode: Optional[str] = None
    country: Optional[str] = None
    # Business address (the member's tutoring business — separate from home)
    business_address_line_1: Optional[str] = None
    business_address_line_2: Optional[str] = None
    business_city: Optional[str] = None
    business_postcode: Optional[str] = None
    business_country: Optional[str] = None
    about: Optional[str] = None
    photo: Optional[str] = Field(default=None, description='URL or path to the profile photo')
    show_profile_publicly: bool = Field(default=False, description='Opt-in to the future public directory')

    # Tuition / specialisation. Flexible types until TTA confirms the taxonomies (issue #5 note).
    tuition_type: Optional[str] = None
    subject_specialisms: list[str] = Field(default_factory=list, sa_type=JSON)
    tuition_levels: list[str] = Field(default_factory=list, sa_type=JSON)
    qualification_levels: list[str] = Field(default_factory=list, sa_type=JSON)
    qualifications: Optional[str] = None
    delivery_mode: Optional[DeliveryMode] = EnumField(DeliveryMode, default=None)

    # Consents — each: agreed flag + timestamp + the policy version agreed to.
    code_of_practice_agreed: bool = False
    code_of_practice_agreed_dt: Optional[datetime] = UTCDatetimeField(default=None)
    code_of_practice_version: Optional[str] = None
    contractual_rules_agreed: bool = False
    contractual_rules_agreed_dt: Optional[datetime] = UTCDatetimeField(default=None)
    contractual_rules_version: Optional[str] = None
    dbs_policy_agreed: bool = False
    dbs_policy_agreed_dt: Optional[datetime] = UTCDatetimeField(default=None)
    dbs_policy_version: Optional[str] = None
    privacy_policy_agreed: bool = False
    privacy_policy_agreed_dt: Optional[datetime] = UTCDatetimeField(default=None)
    privacy_policy_version: Optional[str] = None
    level_eligibility_accepted: bool = False
    level_eligibility_accepted_dt: Optional[datetime] = UTCDatetimeField(default=None)
    level_eligibility_version: Optional[str] = None

    # Additional
    cpd_platform_username: Optional[str] = None
    referral_source: Optional[str] = None
    admin_notes: Optional[str] = Field(default=None, description='Staff-only notes / bespoke arrangements')

    # Status & compliance
    verification_status: VerificationStatus = EnumField(VerificationStatus, default=VerificationStatus.PROCESSING)
    safeguarding_completion_date: Optional[datetime] = UTCDatetimeField(default=None)

    # Email preferences (drive Mailchimp groups; wired in the Mailchimp integration issue)
    email_workflow_updates: bool = True
    email_event_announcements: bool = True
    email_blasts: bool = True


class Member(_Member, table=True):
    """A member's profile, 1:1 with its ``User`` (which carries identity + auth)."""

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = FKField('user.id', ondelete='CASCADE', unique=True)
    member_number: Optional[str] = Field(
        default=None, unique=True, index=True, description='Generated on create, e.g. TTA-000123'
    )
    created_dt: datetime = UTCDatetimeField(now_add=True, index=True)
    updated_dt: Optional[datetime] = UTCDatetimeField(auto_now=True)

    user: User = Relationship()

    @property
    def compliance_rag(self) -> ComplianceRAG:
        """Compliance traffic light — placeholder until #13 computes it from DBS/references/safeguarding."""
        return ComplianceRAG.GREEN

    @classmethod
    def request_query(cls, request: Request, db: DBSession = None) -> SelectOfScalar['Member']:  # ty:ignore[invalid-parameter-default]
        """Members visible to staff: every non-deleted member. Single-tenant — staff see all."""
        return select(Member).join(User).where(User.deleted_dt == None, User.user_type == UserType.MEMBER)  # noqa: E711


class MemberBasic(_Member):
    """Member response shape — the profile plus its joined user identity and computed RAG."""

    id: int
    member_number: str
    created_dt: datetime
    updated_dt: Optional[datetime]
    compliance_rag: ComplianceRAG
    user: UserBasic


class MemberCreate(_Member):
    """Create-member request: the user identity (creates the ``User(MEMBER)``) plus profile fields."""

    first_name: Optional[str] = None
    last_name: str
    email: EmailStr


class MemberUpdate(_Member):
    """Partial update — every field optional; apply with ``model_dump(exclude_unset=True)``."""

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
