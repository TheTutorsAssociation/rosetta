from sqlmodel import SQLModel


class AppModel(SQLModel):
    """Thin base class for all domain models.

    Carries no behaviour of its own — it exists so shared model concerns can be added in one
    place as the schema grows. ``User`` (and any future model) inherits from it.
    """
