from sqlalchemy import Boolean, CheckConstraint, Column, Float, ForeignKey, Integer, JSON, String, Table

from core.db import metadata


truck_racks = Table('truck_racks', metadata,
    Column('code', String(64), primary_key=True),
    Column('rack_type', String(160), nullable=False),
    Column('bay_count', Integer, nullable=False),
    Column('workshop_kg', Float, nullable=False),
    Column('strap_mark', String(160), nullable=True),
    Column('strap_cycle', String(160), nullable=True),
    Column('inspection', String(160), nullable=False),
    CheckConstraint('bay_count BETWEEN 1 AND 24'),
    CheckConstraint('workshop_kg > 0'),
    CheckConstraint("inspection IN ('待检','有效','已撤销')"),
)
