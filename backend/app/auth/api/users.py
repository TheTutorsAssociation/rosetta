from fastapi import APIRouter, Request

from app.auth.models import UserBasic

router = APIRouter(prefix='/users', tags=['users'])


@router.get('/me', response_model=UserBasic, name='users-me')
def get_current_user(request: Request) -> UserBasic:
    """Return the authenticated user. ``auth_user`` populates ``request.state.user``."""
    return UserBasic.model_validate(request.state.user, from_attributes=True)
