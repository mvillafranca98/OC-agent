from __future__ import annotations

from pathlib import Path
from typing import Iterable, Mapping

import pandas as pd


class CSVStore:
    def write_rows(
        self, rows: Iterable[Mapping[str, object]], output_path: Path
    ) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        frame = pd.DataFrame(list(rows))
        frame.to_csv(output_path, index=False)
        return output_path

