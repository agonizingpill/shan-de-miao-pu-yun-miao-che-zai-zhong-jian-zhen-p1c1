"""Small additive migrations for workbench databases created before versioning."""
from sqlalchemy import inspect, text
from sqlalchemy.schema import CreateColumn

from core.db import engine, metadata
# Importing routers registers every Table on metadata for standalone execution.
from domain import routes as _domain_routes  # noqa: F401


def ensure_new_columns():
    inspector = inspect(engine)
    existing = set(inspector.get_table_names())
    with engine.begin() as conn:
        for table in metadata.sorted_tables:
            if table.name not in existing:
                continue
            present = {column['name'] for column in inspector.get_columns(table.name)}
            for column in table.columns:
                if column.name in present:
                    continue
                column_ddl = str(CreateColumn(column).compile(dialect=engine.dialect))
                conn.execute(text(f'ALTER TABLE {table.name} ADD COLUMN {column_ddl}'))

        if 'load_advisories' in existing:
            conn.execute(text(
                "UPDATE load_advisories SET current = true WHERE current IS NULL"))
            conn.execute(text(
                "UPDATE load_advisories SET is_current = true WHERE is_current IS NULL"))
            conn.execute(text(
                "UPDATE load_advisories SET active = true WHERE active IS NULL"))
            conn.execute(text(
                "UPDATE load_advisories SET status = '现行' WHERE status IS NULL OR status = ''"))
            conn.execute(text(
                "UPDATE load_advisories SET state = 'current' WHERE state IS NULL OR state = ''"))
            conn.execute(text(
                "UPDATE load_advisories SET lifecycle = 'current' WHERE lifecycle IS NULL OR lifecycle = ''"))
            conn.execute(text(
                "UPDATE load_advisories SET version = 1 WHERE version IS NULL"))
            conn.execute(text(
                "UPDATE load_advisories SET revision = version WHERE revision IS NULL"))

            if engine.dialect.name == 'postgresql':
                conn.execute(text(
                    'ALTER TABLE load_advisories ALTER COLUMN token DROP NOT NULL'))


if __name__ == '__main__':
    ensure_new_columns()
    print('schema checked')
