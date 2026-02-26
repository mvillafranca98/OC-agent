from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

try:
    import duckdb
except ImportError:  # pragma: no cover - depends on optional install state
    duckdb = None


class DuckDBStore:
    def __init__(self, database_path: Path) -> None:
        if duckdb is None:
            raise RuntimeError("duckdb is not installed. Add duckdb to dependencies.")
        self.database_path = database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)

    def write_dataframe(self, table_name: str, frame: pd.DataFrame) -> None:
        if duckdb is None:
            raise RuntimeError("duckdb is not installed. Add duckdb to dependencies.")

        safe_table_name = re.sub(r"[^a-zA-Z0-9_]", "_", table_name)
        with duckdb.connect(str(self.database_path)) as connection:
            connection.register("incoming_frame", frame)
            connection.execute(
                f"CREATE OR REPLACE TABLE {safe_table_name} AS SELECT * FROM incoming_frame"
            )
            connection.unregister("incoming_frame")

