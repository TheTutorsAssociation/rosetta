from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from app.core.database import DBSession
from app.members.models.member import Member, VerificationStatus
from tests.conftest import AuthenticatedTestClient, count_queries
from tests.members.factories import MemberProfileFactory


def _create_payload(**overrides) -> dict:
    """A minimal create-member payload (last_name + email required)."""
    return {'first_name': 'Ada', 'last_name': 'Lovelace', 'email': 'ada@example.com', **overrides}


class TestCreateMember:
    def test_create_returns_the_full_member_shape(self, auth_client: AuthenticatedTestClient, db: DBSession):
        """Creating a member returns the profile + the joined user identity + a generated number."""
        r = auth_client.post(
            auth_client.app.url_path_for('members-create'),
            json=_create_payload(phone='07123', show_profile_publicly=True),
        )
        assert r.status_code == 201
        data = r.json()
        assert data == {
            'id': data['id'],
            'member_number': f'TTA-{data["id"]:06d}',
            'phone': '07123',
            'whatsapp': None,
            'address_line_1': None,
            'address_line_2': None,
            'city': None,
            'postcode': None,
            'country': None,
            'business_address_line_1': None,
            'business_address_line_2': None,
            'business_city': None,
            'business_postcode': None,
            'business_country': None,
            'about': None,
            'photo': None,
            'show_profile_publicly': True,
            'tuition_type': None,
            'subject_specialisms': [],
            'tuition_levels': [],
            'qualification_levels': [],
            'qualifications': None,
            'delivery_mode': None,
            'code_of_practice_agreed': False,
            'code_of_practice_agreed_dt': None,
            'code_of_practice_version': None,
            'contractual_rules_agreed': False,
            'contractual_rules_agreed_dt': None,
            'contractual_rules_version': None,
            'dbs_policy_agreed': False,
            'dbs_policy_agreed_dt': None,
            'dbs_policy_version': None,
            'privacy_policy_agreed': False,
            'privacy_policy_agreed_dt': None,
            'privacy_policy_version': None,
            'level_eligibility_accepted': False,
            'level_eligibility_accepted_dt': None,
            'level_eligibility_version': None,
            'cpd_platform_username': None,
            'referral_source': None,
            'admin_notes': None,
            'verification_status': 'processing',
            'safeguarding_completion_date': None,
            'email_workflow_updates': True,
            'email_event_announcements': True,
            'email_blasts': True,
            'created_dt': data['created_dt'],
            'updated_dt': data['updated_dt'],
            'compliance_rag': 'green',
            'user': {
                'id': data['user']['id'],
                'first_name': 'Ada',
                'last_name': 'Lovelace',
                'email': 'ada@example.com',
                'user_type': 'member',
                'is_superadmin': False,
                'created_dt': data['user']['created_dt'],
                'updated_dt': data['user']['updated_dt'],
            },
        }

    def test_create_accepts_profile_fields(self, auth_client: AuthenticatedTestClient, db: DBSession):
        """Profile fields (incl. JSON lists and enums) round-trip through create."""
        r = auth_client.post(
            auth_client.app.url_path_for('members-create'),
            json=_create_payload(subject_specialisms=['Maths', 'Physics'], delivery_mode='both'),
        )
        assert r.status_code == 201
        assert r.json()['subject_specialisms'] == ['Maths', 'Physics']
        assert r.json()['delivery_mode'] == 'both'

    def test_create_rejects_duplicate_email(self, auth_client: AuthenticatedTestClient, db: DBSession):
        """A second member with an existing email is rejected with 409."""
        MemberProfileFactory.create_with_db(db, email='taken@example.com')
        r = auth_client.post(
            auth_client.app.url_path_for('members-create'), json=_create_payload(email='taken@example.com')
        )
        assert r.status_code == 409
        assert r.json() == {'detail': 'A user with this email already exists'}

    def test_create_validates_email(self, auth_client: AuthenticatedTestClient, db: DBSession):
        """An invalid email is rejected by validation before any row is created."""
        r = auth_client.post(auth_client.app.url_path_for('members-create'), json=_create_payload(email='not-an-email'))
        assert r.status_code == 422

    def test_created_member_cannot_log_in(
        self, auth_client: AuthenticatedTestClient, client: TestClient, db: DBSession
    ):
        """A staff-created member has an unusable password and cannot authenticate."""
        auth_client.post(
            auth_client.app.url_path_for('members-create'), json=_create_payload(email='nomore@example.com')
        )
        r = client.post(client.app.url_path_for('login'), json={'email': 'nomore@example.com', 'password': 'anything'})
        assert r.status_code == 401
        assert r.json() == {'detail': 'Incorrect email or password'}


class TestListMembers:
    def test_empty_list(self, auth_client: AuthenticatedTestClient, db: DBSession):
        """With no members the list is an empty, well-formed page."""
        r = auth_client.get(auth_client.app.url_path_for('members-list'))
        assert r.status_code == 200
        assert r.json() == {'items': [], 'total': 0, 'page': 1, 'page_size': 50}

    def test_lists_members_with_their_user(self, auth_client: AuthenticatedTestClient, db: DBSession):
        """A listed member carries its number, compliance RAG and joined user identity."""
        member = MemberProfileFactory.create_with_db(db, first_name='Grace', last_name='Hopper')
        r = auth_client.get(auth_client.app.url_path_for('members-list'))
        assert r.status_code == 200
        body = r.json()
        assert body['total'] == 1
        item = body['items'][0]
        assert item['member_number'] == member.member_number
        assert item['compliance_rag'] == 'green'
        assert item['user']['last_name'] == 'Hopper'

    def test_filter_by_status(self, auth_client: AuthenticatedTestClient, db: DBSession):
        """The status filter returns only members in the requested verification status."""
        MemberProfileFactory.create_with_db(db, verification_status=VerificationStatus.PROCESSING)
        MemberProfileFactory.create_with_db(db, verification_status=VerificationStatus.VERIFIED)
        r = auth_client.get(auth_client.app.url_path_for('members-list'), params={'status': 'verified'})
        assert r.status_code == 200
        assert [m['verification_status'] for m in r.json()['items']] == ['verified']

    def test_search_matches_name_email_and_number(self, auth_client: AuthenticatedTestClient, db: DBSession):
        """Search matches across the user's name/email and the member number."""
        MemberProfileFactory.create_with_db(db, last_name='Findme', email='findme@example.com')
        MemberProfileFactory.create_with_db(db, last_name='Other', email='other@example.com')
        r = auth_client.get(auth_client.app.url_path_for('members-list'), params={'search': 'findme'})
        assert r.status_code == 200
        assert [m['user']['last_name'] for m in r.json()['items']] == ['Findme']

    def test_filter_new_in_days(self, auth_client: AuthenticatedTestClient, db: DBSession):
        """new_in_days returns only members created within the window."""
        recent = MemberProfileFactory.create_with_db(db)
        old = MemberProfileFactory.create_with_db(db)
        old.created_dt = datetime.now(UTC) - timedelta(days=40)
        db.add(old)
        db.commit()
        r = auth_client.get(auth_client.app.url_path_for('members-list'), params={'new_in_days': 7})
        assert r.status_code == 200
        assert [m['id'] for m in r.json()['items']] == [recent.id]

    def test_order_by_last_name_ascending(self, auth_client: AuthenticatedTestClient, db: DBSession):
        """Ordering by the joined user's last_name ascending sorts members A→Z."""
        MemberProfileFactory.create_with_db(db, last_name='Zeta')
        MemberProfileFactory.create_with_db(db, last_name='Alpha')
        r = auth_client.get(
            auth_client.app.url_path_for('members-list'),
            params={'order_by': 'last_name', 'order_direction': 'asc'},
        )
        assert [m['user']['last_name'] for m in r.json()['items']] == ['Alpha', 'Zeta']

    def test_pagination_slices_results(self, auth_client: AuthenticatedTestClient, db: DBSession):
        """page/page_size return the requested slice with the full total."""
        for _ in range(3):
            MemberProfileFactory.create_with_db(db)
        r = auth_client.get(auth_client.app.url_path_for('members-list'), params={'page': 2, 'page_size': 1})
        body = r.json()
        assert body['total'] == 3
        assert body['page'] == 2
        assert len(body['items']) == 1

    def test_soft_deleted_members_are_excluded(self, auth_client: AuthenticatedTestClient, db: DBSession):
        """A soft-deleted member (deleted user) drops out of the list."""
        member = MemberProfileFactory.create_with_db(db)
        member.user.deleted_dt = datetime.now(UTC)
        db.add(member.user)
        db.commit()
        r = auth_client.get(auth_client.app.url_path_for('members-list'))
        assert r.json() == {'items': [], 'total': 0, 'page': 1, 'page_size': 50}

    def test_list_has_no_n_plus_one(self, auth_client: AuthenticatedTestClient, db: DBSession):
        """Query count is identical at page_size=1 and page_size=200 (paginate-then-fetch)."""
        for _ in range(5):
            MemberProfileFactory.create_with_db(db)
        with count_queries(db) as small:
            auth_client.get(auth_client.app.url_path_for('members-list'), params={'page_size': 1})
        with count_queries(db) as large:
            auth_client.get(auth_client.app.url_path_for('members-list'), params={'page_size': 200})
        assert small.count == large.count


class TestMemberOptions:
    def test_options_exposes_filters_and_ordering(self, auth_client: AuthenticatedTestClient, db: DBSession):
        """The OPTIONS route advertises the available filters and order fields."""
        r = auth_client.options(auth_client.app.url_path_for('members-list-options'))
        assert r.status_code == 200
        body = r.json()
        assert set(body) == {'status', 'search', 'new_in_days', 'order_by', 'order_direction'}
        assert body['status']['choices'] == [
            {'id': 'processing', 'name': 'processing'},
            {'id': 'verified', 'name': 'verified'},
        ]


class TestMemberDetail:
    def test_returns_a_member(self, auth_client: AuthenticatedTestClient, db: DBSession):
        """The detail route returns the member with its joined user."""
        member = MemberProfileFactory.create_with_db(db, last_name='Curie')
        r = auth_client.get(auth_client.app.url_path_for('members-detail', member_id=member.id))
        assert r.status_code == 200
        assert r.json()['id'] == member.id
        assert r.json()['user']['last_name'] == 'Curie'

    def test_missing_member_is_404(self, auth_client: AuthenticatedTestClient, db: DBSession):
        """An unknown member id returns 404."""
        r = auth_client.get(auth_client.app.url_path_for('members-detail', member_id=999999))
        assert r.status_code == 404
        assert r.json() == {'detail': 'Member not found'}


class TestUpdateMember:
    def test_updates_identity_and_profile(self, auth_client: AuthenticatedTestClient, db: DBSession):
        """PATCH applies both user-identity fields and profile fields."""
        member = MemberProfileFactory.create_with_db(db, last_name='Old')
        r = auth_client.patch(
            auth_client.app.url_path_for('members-update', member_id=member.id),
            json={'last_name': 'New', 'phone': '07999', 'verification_status': 'verified'},
        )
        assert r.status_code == 200
        data = r.json()
        assert data['user']['last_name'] == 'New'
        assert data['phone'] == '07999'
        assert data['verification_status'] == 'verified'

    def test_missing_member_is_404(self, auth_client: AuthenticatedTestClient, db: DBSession):
        """Updating an unknown member returns 404."""
        r = auth_client.patch(auth_client.app.url_path_for('members-update', member_id=999999), json={'phone': '1'})
        assert r.status_code == 404


class TestDeleteMember:
    def test_soft_deletes_the_member(self, auth_client: AuthenticatedTestClient, db: DBSession):
        """DELETE soft-deletes (sets the user's deleted_dt) and drops the member from the list."""
        member = MemberProfileFactory.create_with_db(db)
        r = auth_client.delete(auth_client.app.url_path_for('members-delete', member_id=member.id))
        assert r.status_code == 204
        db.refresh(member.user)
        assert member.user.deleted_dt is not None
        listed = auth_client.get(auth_client.app.url_path_for('members-list'))
        assert listed.json()['total'] == 0

    def test_missing_member_is_404(self, auth_client: AuthenticatedTestClient, db: DBSession):
        """Deleting an unknown member returns 404."""
        r = auth_client.delete(auth_client.app.url_path_for('members-delete', member_id=999999))
        assert r.status_code == 404


class TestMemberPermissions:
    def test_non_admin_cannot_create(self, member_client: AuthenticatedTestClient, db: DBSession):
        """A logged-in non-admin (member) is forbidden from the member admin API."""
        r = member_client.post(member_client.app.url_path_for('members-create'), json=_create_payload())
        assert r.status_code == 403

    def test_non_admin_cannot_list(self, member_client: AuthenticatedTestClient, db: DBSession):
        """Member admin reads are staff-only too — a member gets 403."""
        r = member_client.get(member_client.app.url_path_for('members-list'))
        assert r.status_code == 403

    def test_unauthenticated_is_rejected(self, client: TestClient, db: DBSession):
        """An unauthenticated request to the member admin API is rejected with 401."""
        r = client.get(client.app.url_path_for('members-list'))
        assert r.status_code == 401


class TestMemberModel:
    def test_compliance_rag_placeholder(self, db: DBSession):
        """compliance_rag is a GREEN placeholder until the compliance issue computes it."""
        member = MemberProfileFactory.create_with_db(db)
        assert member.compliance_rag.value == 'green'

    def test_request_query_excludes_non_members_and_deleted(self, db: DBSession):
        """request_query returns only non-deleted member users."""
        live = MemberProfileFactory.create_with_db(db)
        deleted = MemberProfileFactory.create_with_db(db)
        deleted.user.deleted_dt = datetime.now(UTC)
        db.add(deleted.user)
        db.commit()
        rows = db.exec(Member.request_query(None)).all()
        assert [m.id for m in rows] == [live.id]
