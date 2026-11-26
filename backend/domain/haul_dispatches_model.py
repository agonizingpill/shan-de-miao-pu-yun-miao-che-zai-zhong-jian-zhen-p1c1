from sqlalchemy import Boolean, CheckConstraint, Column, Float, ForeignKey, Integer, JSON, String, Table

from core.db import metadata


haul_dispatches = Table('haul_dispatches', metadata,
    Column('code', String(64), primary_key=True),
    Column('truck', String(160), ForeignKey('truck_racks.code'), nullable=False),
    Column('advisory', String(160), ForeignKey('load_advisories.code'), nullable=False),
    Column('lot', String(160), ForeignKey('plant_trays.code'), nullable=False, unique=True),
    Column('strap_snapshot', String(160), nullable=False),
    Column('stage', String(160), nullable=False),
    Column('receipt', String(160), nullable=True, unique=True),
    CheckConstraint("stage IN ('已派车','卸苗回签')"),
)
