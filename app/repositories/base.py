from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Optional

from app.repositories.models import Institution, RefreshToken, User


class AuthRepository(ABC):
    @abstractmethod
    def get_user_by_email(self, email: str) -> Optional[User]: ...

    @abstractmethod
    def get_user_by_id(self, user_id: str) -> Optional[User]: ...

    @abstractmethod
    def get_student_by_roll(self, institution_id: str, roll_number: str) -> Optional[User]: ...

    @abstractmethod
    def save_user(self, user: User) -> None: ...

    @abstractmethod
    def get_institution(self, institution_id: str) -> Optional[Institution]: ...

    @abstractmethod
    def get_institution_by_code(self, code: str) -> Optional[Institution]: ...

    @abstractmethod
    def create_institution_with_admin(self, institution: Institution, user: User) -> None: ...

    @abstractmethod
    def add_refresh(self, token: RefreshToken) -> None: ...

    @abstractmethod
    def save_refresh(self, token: RefreshToken) -> None: ...

    @abstractmethod
    def get_refresh_by_hash(self, token_hash: str) -> Optional[RefreshToken]: ...

    @abstractmethod
    def revoke_family(self, family_id: str, now: datetime) -> None: ...

    @abstractmethod
    def revoke_all_for_user(self, user_id: str, now: datetime, except_family: Optional[str] = None) -> None: ...

    @abstractmethod
    def add_audit(
        self,
        action: str,
        institution_id: Optional[str] = None,
        user_id: Optional[str] = None,
        ip: Optional[str] = None,
        meta: Optional[dict[str, Any]] = None,
    ) -> None: ...
