from typing import List
from dataclasses import dataclass

from sqlalchemy import UniqueConstraint, ForeignKey
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped, relationship


@dataclass(frozen=True)
class GetUsersStreamer:
    id: str
    name: str

    def __hash__(self):
        return hash((self.id, self.name))


class Base(DeclarativeBase):
    pass


class Guild(Base):
    __tablename__ = 'guilds'
    guild_id: Mapped[str] = mapped_column(primary_key=True)
    notification_channel_id: Mapped[str]
    user_subscriptions: Mapped[List["UserSubscription"]] = relationship(back_populates='guild',
                                                                        passive_deletes=True,
                                                                        cascade='all, delete-orphan')
    notification_mode: Mapped[str]
    is_censored: Mapped[bool] = mapped_column(default=False)


class Streamer(Base):
    __tablename__ = 'streamers'
    streamer_id: Mapped[str] = mapped_column(primary_key=True)
    streamer_name: Mapped[str]
    topic_sub_id: Mapped[str]
    user_subscriptions: Mapped[List["UserSubscription"]] = relationship(back_populates='streamer')


class UserSubscription(Base):
    __tablename__ = 'user_subscriptions'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(nullable=False)
    guild_id: Mapped[str] = mapped_column(ForeignKey('guilds.guild_id', ondelete='CASCADE'))
    streamer_id: Mapped[str] = mapped_column(ForeignKey('streamers.streamer_id'))
    __table_args__ = (
        UniqueConstraint('user_id', 'guild_id', 'streamer_id', name='uix_1'),
    )
    guild: Mapped["Guild"] = relationship(back_populates="user_subscriptions")
    streamer: Mapped["Streamer"] = relationship(back_populates="user_subscriptions")
