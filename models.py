from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped


class Base(DeclarativeBase):
    pass


class Guild(Base):
    __tablename__ = 'guilds'
    id: Mapped[int] = mapped_column(primary_key=True)
    guild_id: Mapped[str] = mapped_column(unique=True)
    notification_channel_id: Mapped[str]


class UserSubscriptions(Base):
    __tablename__ = 'user_subscriptions'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str]
    guild_id: Mapped[str]
    streamer_id: Mapped[str]
    __table_args__ = (
        UniqueConstraint('user_id', 'guild_id', 'streamer_id', name='uix_1'),
    )
