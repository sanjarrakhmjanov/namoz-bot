from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from bot.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String(64))
    full_name: Mapped[str | None] = mapped_column(String(128))
    lang: Mapped[str] = mapped_column(String(8), default="uz", nullable=False)

    city: Mapped[str | None] = mapped_column(String(64))
    lat: Mapped[float | None] = mapped_column(Float)
    lon: Mapped[float | None] = mapped_column(Float)
    timezone: Mapped[str | None] = mapped_column(String(64))

    time_offset_min: Mapped[int] = mapped_column(Integer, default=0)
    silent_start: Mapped[str | None] = mapped_column(String(5))
    silent_end: Mapped[str | None] = mapped_column(String(5))
    hijri_reminder_on: Mapped[bool] = mapped_column(Boolean, default=False)
    last_hijri_month: Mapped[int | None] = mapped_column(Integer)
    last_hijri_year: Mapped[int | None] = mapped_column(Integer)
    ramadan_on: Mapped[bool] = mapped_column(Boolean, default=False)
    suhoor_offset_min: Mapped[int] = mapped_column(Integer, default=-30)
    iftar_offset_min: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_active_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    reminders: Mapped["Reminder"] = relationship(back_populates="user", uselist=False)
    tasbeh: Mapped["Tasbeh"] = relationship(back_populates="user", uselist=False)
    reminder_events: Mapped[list["ReminderEvent"]] = relationship(back_populates="user")


class Reminder(Base):
    __tablename__ = "reminders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)

    fajr_on: Mapped[bool] = mapped_column(Boolean, default=False)
    dhuhr_on: Mapped[bool] = mapped_column(Boolean, default=False)
    asr_on: Mapped[bool] = mapped_column(Boolean, default=False)
    maghrib_on: Mapped[bool] = mapped_column(Boolean, default=False)
    isha_on: Mapped[bool] = mapped_column(Boolean, default=False)

    offset_min: Mapped[int] = mapped_column(Integer, default=10)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped[User] = relationship(back_populates="reminders")


class Tasbeh(Base):
    __tablename__ = "tasbeh"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)

    count: Mapped[int] = mapped_column(Integer, default=0)
    goal: Mapped[int] = mapped_column(Integer, default=33)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped[User] = relationship(back_populates="tasbeh")


class ReminderEvent(Base):
    __tablename__ = "reminder_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(24))
    prayer_key: Mapped[str | None] = mapped_column(String(16))
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship(back_populates="reminder_events")
