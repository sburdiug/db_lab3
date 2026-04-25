import enum
from datetime import datetime, time

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, Text, Time
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class WindDirection(str, enum.Enum):
    N = "N"
    NNE = "NNE"
    NE = "NE"
    ENE = "ENE"
    E = "E"
    ESE = "ESE"
    SE = "SE"
    SSE = "SSE"
    S = "S"
    SSW = "SSW"
    SW = "SW"
    WSW = "WSW"
    W = "W"
    WNW = "WNW"
    NW = "NW"
    NNW = "NNW"


class WeatherRaw(Base):
    __tablename__ = "weather_raw"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    country: Mapped[str] = mapped_column(Text, nullable=False)
    location_name: Mapped[str] = mapped_column(Text, nullable=False)
    last_updated: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    temperature_celsius: Mapped[float] = mapped_column(Float, nullable=False)

    wind_degree: Mapped[int] = mapped_column(Integer, nullable=False)
    wind_kph: Mapped[float] = mapped_column(Float, nullable=False)
    wind_direction: Mapped[WindDirection] = mapped_column(
        Enum(WindDirection, name="wind_direction_enum"), nullable=False
    )

    sunrise: Mapped[time] = mapped_column(Time, nullable=False)
    sunset: Mapped[time] = mapped_column(Time, nullable=False)
    moonrise: Mapped[time | None] = mapped_column(Time, nullable=True)
    moonset: Mapped[time | None] = mapped_column(Time, nullable=True)
    moon_phase: Mapped[str] = mapped_column(Text, nullable=False)
    moon_illumination: Mapped[int] = mapped_column(Integer, nullable=False)


class WeatherRecord(Base):
    __tablename__ = "weather_record"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    country: Mapped[str] = mapped_column(Text, nullable=False)
    location_name: Mapped[str] = mapped_column(Text, nullable=False)
    last_updated: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    temperature_celsius: Mapped[float] = mapped_column(Float, nullable=False)

    wind_degree: Mapped[int] = mapped_column(Integer, nullable=False)
    wind_kph: Mapped[float] = mapped_column(Float, nullable=False)
    wind_direction: Mapped[WindDirection] = mapped_column(
        Enum(WindDirection, name="wind_direction_enum"), nullable=False
    )
    should_go_outside: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    astronomy_info: Mapped["AstronomyInfo | None"] = relationship(
        back_populates="weather_record", uselist=False
    )


class AstronomyInfo(Base):
    __tablename__ = "astronomy_info"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    weather_record_id: Mapped[int] = mapped_column(
        ForeignKey("weather_record.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    sunrise: Mapped[time] = mapped_column(Time, nullable=False)
    sunset: Mapped[time] = mapped_column(Time, nullable=False)
    moonrise: Mapped[time | None] = mapped_column(Time, nullable=True)
    moonset: Mapped[time | None] = mapped_column(Time, nullable=True)
    moon_phase: Mapped[str] = mapped_column(Text, nullable=False)
    moon_illumination: Mapped[int] = mapped_column(Integer, nullable=False)

    weather_record: Mapped[WeatherRecord] = relationship(back_populates="astronomy_info")
