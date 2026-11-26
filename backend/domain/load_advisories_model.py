from sqlalchemy import Boolean, CheckConstraint, Column, Float, ForeignKey, Integer, JSON, String, Table

from core.db import metadata


load_advisories = Table('load_advisories', metadata,
    Column('code', String(64), primary_key=True),
    Column('truck', String(160), ForeignKey('truck_racks.code'), nullable=False),
    Column('route', String(160), nullable=False),
    Column('cycle', String(160), nullable=False),
    Column('rms_goal', Float, nullable=False),
    Column('ceiling_kg', Float, nullable=False),
    Column('slope', Float, nullable=False),
    Column('validation_mae', Float, nullable=False),
    Column('exclusion_count', Integer, nullable=False),
    Column('evidence_span', String(160), nullable=False),
    Column('token', String(64), nullable=False, unique=True),
    CheckConstraint('ceiling_kg >= 0'),
    CheckConstraint('slope > 0'),
    CheckConstraint('validation_mae >= 0'),
)
