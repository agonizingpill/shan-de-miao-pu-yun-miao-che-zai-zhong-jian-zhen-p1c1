from sqlalchemy import Boolean, CheckConstraint, Column, Float, ForeignKey, Integer, JSON, String, Table

from core.db import metadata


plant_trays = Table('plant_trays', metadata,
    Column('code', String(64), primary_key=True),
    Column('rack_type', String(160), nullable=False),
    Column('plants', String(160), nullable=False),
    Column('trays', Integer, nullable=False),
    Column('tare_kg', Float, nullable=False),
    Column('stock_kg', Float, nullable=False),
    Column('gross_kg', Float, nullable=False),
    Column('stage', String(160), nullable=False),
    CheckConstraint('trays BETWEEN 1 AND 24'),
    CheckConstraint('tare_kg > 0'),
    CheckConstraint('stock_kg > 0'),
    CheckConstraint('gross_kg > 0'),
    CheckConstraint("stage IN ('待装车','已装车','已交接')"),
)
