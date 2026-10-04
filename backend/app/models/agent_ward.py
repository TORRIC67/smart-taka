"""agent_wards table - a field agent (Role.AGENT) can be assigned several streets/mitaa
within their own zone. They only see and register customers whose ward matches one of
these rows."""
from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AgentWard(Base):
    __tablename__ = "agent_wards"
    __table_args__ = (UniqueConstraint("user_id", "ward", name="uq_agent_ward"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    ward: Mapped[str] = mapped_column(String(80))
