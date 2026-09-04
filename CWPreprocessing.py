# ============================================================
# Author: Student ID: F416013
# Date: 12-01-2026
# ============================================================

# ------------------------------------------------------------
# CWPreprocessing.py
# Cleans raw CSV test files and stores them in SQLite databases.
# ------------------------------------------------------------

import re
import sqlite3
from pathlib import Path
import tempfile

import pandas as pd


# ============================================================
# SCORE PROCESSOR
# ============================================================

class ScoreProcessor:
    """
    Provides utilities for interpreting question headers, converting
    question-level marks to percentages, and recalculating overall
    grades. This ensures consistency across tests that may use
    different scoring formats.
    """

    def extract_denominator(self, col_name: str) -> float | None:
        match = re.search(r"(?i)(?:/|of)\s*(\d+)", col_name or "")
        return float(match.group(1)) if match else None

    def find_question_columns(self, columns: list[str]) -> list[str]:
        return [
            c for c in columns
            if re.match(r"(?i)^\s*Q\s*\d+", c or "")
        ]

    def detect_value_mode(self, series: pd.Series, denom: float | None) -> str:
        s = pd.to_numeric(series, errors="coerce").dropna()
        if s.empty:
            return "unknown"

        max_v = float(s.max())

        if 90.0 <= max_v <= 100.0:
            return "percentage"

        if denom and denom > 0:
            scaled_full = denom / 100.0
            if 0.9 * scaled_full <= max_v <= 1.1 * scaled_full:
                return "scaled_proportion"

        if max_v <= 1.0:
            return "proportion"

        return "points"

    def to_percentage(self, series: pd.Series, denom: float | None) -> pd.Series:
        s = pd.to_numeric(series, errors="coerce").fillna(0.0)
        mode = self.detect_value_mode(s, denom)

        if mode == "percentage":
            return s

        if mode == "proportion":
            return s * 100.0

        if mode == "scaled_proportion":
            scaled_full = (denom or 100.0) / 100.0
            return (s / scaled_full) * 100.0

        if denom and denom > 0:
            return (s / denom) * 100.0

        max_points = float(s.max())
        return (s / max_points) * 100.0 if max_points > 0 else s * 0.0

    def standardise_questions(self, df: pd.DataFrame):
        dfc = df.copy()
        dfc.columns = [c.strip() for c in dfc.columns]

        qcols = self.find_question_columns(list(dfc.columns))

        earned_points = pd.Series(0.0, index=dfc.index)
        total_possible = 0.0

        for i, col in enumerate(qcols, start=1):
            denom = self.extract_denominator(col)
            dfc[f"Q{i}"] = self.to_percentage(dfc[col], denom).round(2)

            s = pd.to_numeric(dfc[col], errors="coerce").fillna(0.0)
            mode = self.detect_value_mode(s, denom)

            if denom and denom > 0:
                if mode == "percentage":
                    earned_points += (s / 100.0) * denom
                elif mode == "proportion":
                    earned_points += s * denom
                elif mode == "scaled_proportion":
                    earned_points += s * 100.0
                elif mode == "points":
                    earned_points += s
                total_possible += denom

        return dfc, earned_points, total_possible

    def recalc_grade(self, dfc, earned_points, total_possible):
        grade_cols = [c for c in dfc.columns if re.match(r"(?i)grade", c)]

        if grade_cols:
            gcol = grade_cols[0]
            denom = self.extract_denominator(gcol)
            s = pd.to_numeric(dfc[gcol], errors="coerce").fillna(0.0)

            if denom and denom > 0:
                dfc["Grade"] = (s / (denom / 100.0)) * 100.0
            else:
                dfc["Grade"] = s
        else:
            if total_possible > 0:
                dfc["Grade"] = (earned_points / total_possible) * 100.0
            else:
                dfc["Grade"] = 0.0

        dfc["Grade"] = dfc["Grade"].round(2)
        return dfc


# ============================================================
# FILE PROCESSOR
# ============================================================

class FileProcessor:
    """
    Processes individual CSV files: loading, standardising question
    columns, recalculating grades, and preparing cleaned DataFrames.
    """

    def __init__(self, score_processor: ScoreProcessor):
        self.score_processor = score_processor
    def process_single_file(self, csv_path: Path):
        original_df = pd.read_csv(csv_path)
        original_df.columns = [c.strip().lower() for c in original_df.columns]

        dfc, earned, total = self.score_processor.standardise_questions(original_df)
        dfc = self.score_processor.recalc_grade(dfc, earned, total)

        rename_map = {
            "research id": "Student_ID",
            "started on": "DateTime_Started",
            "completed": "Date_Time_Completed",
            "time taken": "Time_Taken",
        }
        dfc.rename(columns=rename_map, inplace=True)

        clean_df = self._build_clean_dataframe(dfc)

        if "Student_ID" in clean_df.columns:
            clean_df = (
                clean_df.sort_values("Grade", ascending=False)
                .drop_duplicates(subset=["Student_ID"], keep="first")
            )

        clean_df = clean_df.fillna(0)
        return original_df, clean_df

    def _build_clean_dataframe(self, dfc):
        keep_cols = []

        for c in [
            "Student_ID",
            "DateTime_Started",
            "Date_Time_Completed",
            "Time_Taken",
            "Grade",
        ]:
            if c in dfc.columns:
                keep_cols.append(c)

        qpct_cols = [c for c in dfc.columns if re.match(r"^Q\d+$", c)]
        keep_cols.extend(qpct_cols)

        return dfc[keep_cols].copy()


# ============================================================
# SQLITE WRITER
# ============================================================

class SQLiteWriter:
    """
    Writes DataFrames to SQLite databases with appropriate column
    types. Supports both the main database and the cleaned results
    database.
    """

    # A static method is used here because the function is logically
    # related to the class, but does not require access to 'self' or
    # any instance-specific data.
    @staticmethod
    def map_sqlite_types(df: pd.DataFrame) -> dict:
        dtype_map = {}

        for col, dt in df.dtypes.items():
            if pd.api.types.is_integer_dtype(dt):
                dtype_map[col] = "INTEGER"
            elif pd.api.types.is_float_dtype(dt):
                dtype_map[col] = "REAL"
            else:
                dtype_map[col] = "TEXT"

        return dtype_map

    def store_dataframes_to_sqlite(self, db_path: Path, named_frames):
        conn = sqlite3.connect(str(db_path))

        try:
            for table_name, df in named_frames:
                dtypes = self.map_sqlite_types(df)
                df.to_sql(
                    table_name,
                    conn,
                    if_exists="replace",
                    index=False,
                    dtype=dtypes,
                )
        finally:
            conn.close()


# ============================================================
# PREPROCESSING PIPELINE
# ============================================================

class PreprocessingPipeline:
    """
    Coordinates the full preprocessing workflow: locating CSV files,
    processing each file, and writing both original and cleaned data
    to SQLite databases.
    """

    def __init__(self, data_dir="TestResult", db_path="Resultdatabase.db"):
        self.data_dir = Path(data_dir)
        self.db_path = Path(db_path)
        self.result_db_path = Path("Resultdatabase.db")

        self.score_processor = ScoreProcessor()
        self.file_processor = FileProcessor(self.score_processor)
        self.sqlite_writer = SQLiteWriter()

    def run(self):
        self._print_intro()
        csv_paths = self._get_csv_paths()

        original_frames = []
        clean_frames = []

        for csv in csv_paths:
            base = csv.stem
            original_df, clean_df = self.file_processor.process_single_file(csv)

            original_frames.append((f"{base}_Original", original_df))
            clean_frames.append((f"{base}_Clean", clean_df))

        all_frames = original_frames + clean_frames
        self.sqlite_writer.store_dataframes_to_sqlite(self.db_path, all_frames)
        self._print_main_db_summary(csv_paths, all_frames)

        self.sqlite_writer.store_dataframes_to_sqlite(self.result_db_path, clean_frames)
        self._print_result_db_summary(clean_frames)

    def _print_intro(self):
        print("Looking for CSV files in folder: TestResult")
        print("Ensure your CSV files are placed in this folder.\n")

    def _get_csv_paths(self):
        if not self.data_dir.exists():
            raise FileNotFoundError(
                f"Data directory not found: {self.data_dir}. "
                "Place your CSV files in this folder."
            )

        csv_paths = sorted(self.data_dir.glob("*.csv"))
        if not csv_paths:
            raise FileNotFoundError(
                f"No CSV files found in {self.data_dir}"
            )

        return csv_paths

    def _print_main_db_summary(self, csv_paths, all_frames):
        print(f"\nProcessed {len(csv_paths)} file(s).")
        print(f"Database created at: {self.db_path.resolve()}")
        print("Tables written:")
        for name, _ in all_frames:
            print(f" - {name}")

    def _print_result_db_summary(self, clean_frames):
        print(
            "\nResultdatabase.db created at: "
            f"{self.result_db_path.resolve()}"
        )
        print("Contains the following cleaned tables:")
        for name, _ in clean_frames:
            print(f" - {name}")


# ============================================================
# MAIN ENTRY POINT
# ============================================================

def main():
    pipeline = PreprocessingPipeline()
    pipeline.run()


# ============================================================
# TEST CODE
# ============================================================

def _test_score_processor():
    sp = ScoreProcessor()

    assert sp.extract_denominator("Q1 /100") == 100.0
    assert sp.extract_denominator("Grade of 20") == 20.0
    assert sp.extract_denominator("No denom") is None

    cols = ["Q1 /100", "Q2 of 50", "grade", "Student_ID"]
    qcols = sp.find_question_columns(cols)
    assert "Q1 /100" in qcols and "Q2 of 50" in qcols

    s_perc = pd.Series([95, 100, 80])
    assert sp.detect_value_mode(s_perc, 100.0) == "percentage"

    s_prop = pd.Series([0.2, 0.5, 0.9])
    assert sp.detect_value_mode(s_prop, 10.0) == "proportion"

    s_points = pd.Series([10, 15, 20])
    assert sp.detect_value_mode(s_points, 20.0) == "points"


def _test_file_processor():
    sp = ScoreProcessor()
    fp = FileProcessor(sp)

    tmp_dir = tempfile.TemporaryDirectory()
    try:
        csv_path = Path(tmp_dir.name) / "test.csv"

        df = pd.DataFrame(
            {
                "research id": [1, 1, 2],
                "started on": ["2024-01-01", "2024-01-01", "2024-01-02"],
                "completed": ["2024-01-01", "2024-01-01", "2024-01-02"],
                "time taken": ["10m", "12m", "9m"],
                "q1 /10": [5, 7, 9],
                "q2 of 20": [10, 15, 18],
            }
        )
        df.to_csv(csv_path, index=False)

        original_df, clean_df = fp.process_single_file(csv_path)

        assert not original_df.empty
        assert not clean_df.empty
        assert "Grade" in clean_df.columns
        assert "Student_ID" in clean_df.columns
        assert clean_df["Student_ID"].nunique() == 2
    finally:
        tmp_dir.cleanup()


def _test_sqlite_writer():
    writer = SQLiteWriter()

    df1 = pd.DataFrame({"a": [1, 2], "b": [0.5, 0.7]})
    df2 = pd.DataFrame({"x": ["a", "b"], "y": [10, 20]})

    conn = sqlite3.connect(":memory:")
    try:
        for name, df in [("T1", df1), ("T2", df2)]:
            dtypes = writer.map_sqlite_types(df)
            df.to_sql(
                name,
                conn,
                if_exists="replace",
                index=False,
                dtype=dtypes,
            )

        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cur.fetchall()}
        assert "T1" in tables and "T2" in tables
    finally:
        conn.close()


def _test_pipeline_smoke():
    tmp_dir = tempfile.TemporaryDirectory()
    try:
        data_dir = Path(tmp_dir.name) / "TestResult"
        data_dir.mkdir()

        csv_path = data_dir / "Formative_Test_1.csv"
        df = pd.DataFrame(
            {
                "research id": [1, 2],
                "started on": ["2024-01-01", "2024-01-02"],
                "completed": ["2024-01-01", "2024-01-02"],
                "time taken": ["10m", "12m"],
                "q1 /10": [7, 8],
                "q2 of 20": [15, 16],
            }
        )
        df.to_csv(csv_path, index=False)

        db_path = Path(tmp_dir.name) / "Resultdatabase.db"
        result_db_path = Path(tmp_dir.name) / "Resultdatabase.db"

        pipeline = PreprocessingPipeline(
            data_dir=str(data_dir),
            db_path=str(db_path),
        )
        pipeline.result_db_path = result_db_path

        pipeline.run()

        assert db_path.exists()
        assert result_db_path.exists()
    finally:
        tmp_dir.cleanup()


def run_tests():
    _test_score_processor()
    _test_file_processor()
    _test_sqlite_writer()
    _test_pipeline_smoke()


RUN_TESTS = False #Change this to True if you would like to run the tests

if __name__ == "__main__":
    if RUN_TESTS:
        run_tests()
    else:
        main()
