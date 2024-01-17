from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped


class Base(DeclarativeBase):
    pass


class Guild(Base):
    __tablename__ = 'guilds'
    id: Mapped[int] = mapped_column(primary_key=True)
    guild_id: Mapped[str] = mapped_column(unique=True)
    notification_channel_id: Mapped[str]
