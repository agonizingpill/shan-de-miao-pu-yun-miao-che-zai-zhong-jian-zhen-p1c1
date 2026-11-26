from sqlalchemy import Boolean, CheckConstraint, Column, Float, ForeignKey, Integer, JSON, String, Table

from core.db import metadata


road_observations = Table('road_observations', metadata,
    Column('code', String(64), primary_key=True),
    Column('route', String(160), nullable=False),
    Column('rack_type', String(160), nullable=False),
    Column('load_kg', Float, nullable=False),
    Column('rms', Float, nullable=False),
    Column('sensor_ref', String(160), nullable=False, unique=True),
    Column('verified', Boolean, nullable=False),
    CheckConstraint('load_kg >= 0'),
    CheckConstraint('rms >= 0'),
)
