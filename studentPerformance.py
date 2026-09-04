# ============================================================
# Author: Student ID: F416013
# Date: 12-01-2026
# ============================================================

# ------------------------------------------------------------
# studentPerformance.py
# Analyse a student's performance on each question of any test
# ------------------------------------------------------------

import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText

TEST_CODE = False #Change this to True if you would like to run the test code

# ============================================================
# QUESTION PERFORMANCE ANALYSER
# (Handles database access, question extraction, statistics, plotting)
# ============================================================

class QuestionPerformanceAnalyser:
    """
    Provides a unified set of tools for analysing a student's
    performance in any assessment. This includes
    loading test data, identifying question columns, computing
    absolute and relative scores, and generating visual summaries.
    """

    TEST_TABLES = {
        "Mock Test": "Formative_Mock_Test_Clean",
        "Formative Test 1": "Formative_Test_1_Clean",
        "Formative Test 2": "Formative_Test_2_Clean",
        "Formative Test 3": "Formative_Test_3_Clean",
        "Formative Test 4": "Formative_Test_4_Clean",
        "Summative Test": "SumTest_Clean"
    }

    def __init__(self, db_path="Resultdatabase.db"):
        self.db_path = db_path

    # ---------------------- Database Utilities ----------------------

    def _load_table(self, test_name):
        """
        Loads the full dataset for a selected test. The method
        retrieves the corresponding table from the SQLite database
        and returns it as a DataFrame.
        """
        table = self.TEST_TABLES[test_name]
        with sqlite3.connect(self.db_path) as conn:
            return pd.read_sql(f"SELECT * FROM {table}", conn)

    def _find_student_row(self, df, student_id):
        """
        Locates the row corresponding to the given Student_ID.
        Returns None if the student does not appear in the dataset.
        """
        match = df[df["Student_ID"].astype(str) == str(student_id)]
        return None if match.empty else match.iloc[0]

    # ---------------------- Question Extraction ----------------------

    def _get_question_columns(self, df):
        """
        Identifies numeric question columns by excluding Student_ID
        and Grade. This ensures that only question-level percentage
        columns are analysed.
        """
        excluded = ["Student_ID", "Grade"]
        numeric_cols = df.select_dtypes(include=["float", "int"]).columns.tolist()
        return [col for col in numeric_cols if col not in excluded]

    # ---------------------- Performance Calculations ----------------------

    def compute_performance(self, df, student_id):
        """
        Computes the student's absolute and relative performance for
        each question. Absolute performance reflects the student's
        percentage score, while relative performance compares the
        student to the class mean.
        """
        question_cols = self._get_question_columns(df)
        student_row = self._find_student_row(df, student_id)

        if student_row is None:
            return None, None, None

        abs_scores = student_row[question_cols].astype(float)
        class_means = df[question_cols].mean()
        rel_scores = abs_scores - class_means

        return abs_scores, rel_scores, question_cols

    # ---------------------- Plotting ----------------------

    def plot_performance(self, abs_scores, rel_scores, question_cols, student_id, test_name):
        """
        Produces a two-part figure showing absolute performance and
        relative performance (student minus class mean). This visual
        summary helps identify strengths and weaknesses across the
        assessment.
        """
        fig, axes = plt.subplots(2, 1, figsize=(10, 8))

        # Absolute performance
        axes[0].bar(question_cols, abs_scores, color="#4C72B0")
        axes[0].set_title(f"Absolute Performance for Student {student_id} – {test_name}")
        axes[0].set_ylabel("Percentage (%)")
        axes[0].set_ylim(0, 100)
        axes[0].grid(True, linestyle="--", alpha=0.6)
        axes[0].tick_params(axis="x", rotation=45)

        # Relative performance
        rel_colours = ["#55A868" if v >= 0 else "#C44E52" for v in rel_scores]
        axes[1].bar(question_cols, rel_scores, color=rel_colours)
        axes[1].axhline(0, color="black", linewidth=1)
        axes[1].set_title("Relative Performance (Student – Class Mean)")
        axes[1].set_ylabel("Difference")
        axes[1].grid(True, linestyle="--", alpha=0.6)
        axes[1].tick_params(axis="x", rotation=45)

        plt.tight_layout()
        return fig


# ============================================================
# GUI APPLICATION
# ============================================================

class StudentPerformanceGUI:
    """
    Tkinter interface for analysing question-level performance.
    The GUI delegates all analytical work to QuestionPerformanceAnalyser.
    """

    def __init__(self, db_path="Resultdatabase.db"):
        self.analyser = QuestionPerformanceAnalyser(db_path)

        self.root = tk.Tk()
        self.root.title("Question-Level Student Performance")
        self.root.geometry("1200x1100")
        self.root.resizable(True, True)

        self._build_ui()
        self.root.bind("<Return>", lambda event: self.show_results())

    # ---------------------- UI Construction ----------------------

    def _build_ui(self):
        instructions = (
            "Welcome to the Question-Level Performance Analyser.\n\n"
            "To begin:\n"
            "1. Enter a valid Student ID.\n"
            "2. Select a test.\n"
            "3. Click 'Analyse Performance'.\n"
        )

        tk.Label(
            self.root,
            text=instructions,
            font=("Arial", 12),
            justify="left"
        ).pack(pady=10, anchor="w", padx=10)

        top_frame = tk.Frame(self.root)
        top_frame.pack(pady=5, padx=10, fill=tk.X)

        # Input frame
        input_frame = tk.LabelFrame(top_frame, text="Input", font=("Arial", 11, "bold"))
        input_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        tk.Label(input_frame, text="Enter Student ID:", font=("Arial", 12, "bold")).grid(
            row=0, column=0, padx=10, pady=5, sticky="e"
        )
        self.student_entry = tk.Entry(input_frame, font=("Arial", 12), width=12)
        self.student_entry.grid(row=0, column=1, padx=10, pady=5, sticky="w")

        tk.Label(input_frame, text="Select Test:", font=("Arial", 12, "bold")).grid(
            row=1, column=0, padx=10, pady=5, sticky="e"
        )

        test_options = list(self.analyser.TEST_TABLES.keys())
        self.test_var = tk.StringVar(master=self.root, value=test_options[0])
        self.test_dropdown = ttk.Combobox(
            input_frame,
            textvariable=self.test_var,
            values=test_options,
            font=("Arial", 12),
            state="readonly",
            width=18
        )
        self.test_dropdown.grid(row=1, column=1, padx=10, pady=5, sticky="w")

        # Action buttons
        button_frame = tk.LabelFrame(top_frame, text="Actions", font=("Arial", 11, "bold"))
        button_frame.pack(side=tk.RIGHT, fill=tk.X, expand=True)

        tk.Button(
            button_frame,
            text="Analyse Performance",
            font=("Arial", 12, "bold"),
            command=self.show_results,
            width=22
        ).pack(pady=8, padx=10)

        tk.Button(
            button_frame,
            text="Descriptive Statistics & Feedback",
            font=("Arial", 12),
            command=self.show_descriptive_statistics,
            width=26
        ).pack(pady=5, padx=10)

        tk.Button(
            button_frame,
            text="Exit Program",
            command=self.confirm_exit,
            font=("Arial", 12, "bold"),
            width=18
        ).pack(pady=10, padx=10)

        # Plot frame
        self.plot_frame = tk.Frame(self.root, height=400, bd=2, relief="groove")
        self.plot_frame.pack(fill=tk.BOTH, expand=False, padx=10, pady=10)

        # Summary box
        self.summary_box = ScrolledText(self.root, height=12, wrap=tk.WORD, font=("Arial", 11))
        self.summary_box.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.summary_box.config(state="normal")
        self.summary_box.insert(tk.END, "Analysis of a student's performance will appear here.\n")
        self.summary_box.config(state="disabled")

    # ============================================================
    # MAIN CALLBACK — ANALYSE PERFORMANCE
    # ============================================================

    def show_results(self):
        student_id = self.student_entry.get().strip()
        test_name = self.test_var.get()

        if not student_id.isdigit() or len(student_id) > 3:
            messagebox.showerror("Invalid Student ID", "Student ID must be 1 to 3 digits long.")
            return

        df = self.analyser._load_table(test_name)
        abs_scores, rel_scores, question_cols = self.analyser.compute_performance(df, student_id)

        if abs_scores is None:
            messagebox.showerror("Error", "Student ID not found in this test.")
            return

        fig = self.analyser.plot_performance(abs_scores, rel_scores, question_cols, student_id, test_name)

        for widget in self.plot_frame.winfo_children():
            widget.destroy()

        canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.summary_box.config(state="normal")
        self.summary_box.delete("1.0", tk.END)

        self.summary_box.insert(tk.END, f"=== Student {student_id} – {test_name} ===\n\n")
        self.summary_box.insert(tk.END, "Absolute Performance (%):\n")
        for q, v in abs_scores.items():
            self.summary_box.insert(tk.END, f"{q}: {round(v, 2)}%\n")

        self.summary_box.insert(tk.END, "\nRelative Performance (Student – Class Mean):\n")
        for q, v in rel_scores.items():
            direction = "ABOVE" if v >= 0 else "BELOW"
            self.summary_box.insert(tk.END, f"{q}: {round(v, 2)} ({direction} class mean)\n")

        self.summary_box.config(state="disabled")

    # ============================================================
    # POPUP: DESCRIPTIVE STATISTICS & FEEDBACK
    # ============================================================

    def show_descriptive_statistics(self):
        student_id = self.student_entry.get().strip()
        test_name = self.test_var.get()

        if not student_id.isdigit() or len(student_id) > 3:
            messagebox.showerror("Invalid Student ID", "Student ID must be 1 to 3 digits long.")
            return

        df = self.analyser._load_table(test_name)
        abs_scores, rel_scores, question_cols = self.analyser.compute_performance(df, student_id)

        if abs_scores is None:
            messagebox.showerror("Error", "Student ID not found in this test.")
            return

        stats_window = tk.Toplevel(self.root)
        stats_window.title("Descriptive Statistics & Feedback")
        stats_window.geometry("700x800")

        text = ScrolledText(stats_window, wrap=tk.WORD, font=("Arial", 11))
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        class_stats = df[question_cols].describe().T

        text.insert(tk.END, f"=== Descriptive Statistics for {test_name} ===\n\n")
        text.insert(tk.END, class_stats.to_string())
        text.insert(tk.END, "\n\n")

        text.insert(tk.END, f"=== Student {student_id} vs Class ===\n\n")
        for q in question_cols:
            student_val = abs_scores[q]
            class_mean = df[q].mean()
            diff = student_val - class_mean
            direction = "above" if diff >= 0 else "below"
            text.insert(tk.END, f"{q}: {round(student_val, 2)}% ({round(diff, 2)} {direction} class mean)\n")

        text.insert(tk.END, "\n=== Strengths & Weaknesses ===\n\n")

        strongest = rel_scores.sort_values(ascending=False).head(3)
        weakest = rel_scores.sort_values().head(3)

        text.insert(tk.END, "Strongest Questions:\n")
        for q, v in strongest.items():
            text.insert(tk.END, f"  {q}: {round(v, 2)} above class mean\n")

        text.insert(tk.END, "\nWeakest Questions:\n")
        for q, v in weakest.items():
            text.insert(tk.END, f"  {q}: {round(v, 2)} below class mean\n")

        text.insert(tk.END, "\n=== Explanation of Statistics ===\n\n")
        text.insert(tk.END, "• Mean: The average score.\n")
        text.insert(tk.END, "• Median: The middle score.\n")
        text.insert(tk.END, "• Mode: The most common score.\n")
        text.insert(tk.END, "• Range: Highest minus lowest.\n")
        text.insert(tk.END, "• Standard Deviation: How spread out scores are.\n\n")

        text.insert(tk.END, "These statistics help identify how the student compares to the class.\n")

        text.config(state="disabled")

    # ============================================================
    # EXIT FUNCTION
    # ============================================================

    def confirm_exit(self):
        if messagebox.askokcancel("Exit", "Do you really want to quit?"):
            self.root.destroy()

    # ============================================================
    # MAIN LOOP
    # ============================================================

    def run(self):
        self.root.mainloop()


# ============================================================
# MAIN PROGRAM
# ============================================================

if __name__ == "__main__" and not TEST_CODE:
    app = StudentPerformanceGUI()
    app.run()

# ============================================================
# TEST CODE
# ============================================================

if TEST_CODE:
    import unittest
    from unittest import mock
    import os

    # Use a non-interactive backend so matplotlib doesn't try to open windows
    plt.switch_backend("Agg")

    def build_test_database(db_path):
        """
        Creates a small SQLite database for testing question-level analysis.
        Includes question columns so the analyser can compute absolute and
        relative performance.
        """
        if os.path.exists(db_path):
            os.remove(db_path)

        conn = sqlite3.connect(db_path)

        # Example dataset with question-level percentages
        table_definitions = {
            "Formative_Mock_Test_Clean": [
                ("101", 50, 80, 60, 70),
                ("102", 60, 70, 65, 75),
                ("103", 70, 90, 85, 95)
            ],
            "Formative_Test_1_Clean": [
                ("101", 55, 78, 62, 71),
                ("102", 65, 68, 66, 74),
                ("103", 75, 92, 88, 96)
            ],
            "Formative_Test_2_Clean": [
                ("101", 58, 79, 63, 72),
                ("102", 68, 69, 67, 76),
                ("103", 78, 93, 89, 97)
            ],
            "Formative_Test_3_Clean": [
                ("101", 62, 81, 64, 73),
                ("102", 72, 71, 68, 77),
                ("103", 82, 94, 90, 98)
            ],
            "Formative_Test_4_Clean": [
                ("101", 64, 82, 65, 74),
                ("102", 74, 72, 69, 78),
                ("103", 84, 95, 91, 99)
            ],
            "SumTest_Clean": [
                ("101", 70, 85, 70, 80),
                ("102", 80, 75, 72, 82),
                ("103", 90, 98, 95, 100)
            ]
        }

        for table_name, rows in table_definitions.items():
            df = pd.DataFrame(rows, columns=["Student_ID", "Grade", "Q1", "Q2", "Q3"])
            df.to_sql(table_name, conn, index=False, if_exists="replace")

        conn.close()


    # ============================================================
    # ANALYSER TESTS
    # ============================================================

    class TestQuestionPerformanceAnalyser(unittest.TestCase):
        """
        Tests for the analytical component of the question-level performance tool.
        """

        @classmethod
        def setUpClass(cls):
            cls.test_db_path = "Resultdatabase_test2.db"
            build_test_database(cls.test_db_path)
            cls.analyser = QuestionPerformanceAnalyser(db_path=cls.test_db_path)

        @classmethod
        def tearDownClass(cls):
            if os.path.exists(cls.test_db_path):
                os.remove(cls.test_db_path)

        def test_load_table_returns_dataframe(self):
            df = self.analyser._load_table("Mock Test")
            self.assertFalse(df.empty)
            self.assertIn("Student_ID", df.columns)
            self.assertIn("Q1", df.columns)

        def test_find_student_row_existing(self):
            df = self.analyser._load_table("Mock Test")
            row = self.analyser._find_student_row(df, "101")
            self.assertIsNotNone(row)
            self.assertEqual(row["Student_ID"], "101")

        def test_find_student_row_missing(self):
            df = self.analyser._load_table("Mock Test")
            row = self.analyser._find_student_row(df, "999")
            self.assertIsNone(row)

        def test_get_question_columns(self):
            df = self.analyser._load_table("Mock Test")
            cols = self.analyser._get_question_columns(df)
            self.assertEqual(cols, ["Q1", "Q2", "Q3"])

        def test_compute_performance_existing_student(self):
            df = self.analyser._load_table("Mock Test")
            abs_scores, rel_scores, cols = self.analyser.compute_performance(df, "101")
            self.assertIsNotNone(abs_scores)
            self.assertEqual(list(cols), ["Q1", "Q2", "Q3"])

        def test_compute_performance_missing_student(self):
            df = self.analyser._load_table("Mock Test")
            abs_scores, rel_scores, cols = self.analyser.compute_performance(df, "999")
            self.assertIsNone(abs_scores)
            self.assertIsNone(rel_scores)
            self.assertIsNone(cols)

        def test_plot_performance_returns_figure(self):
            df = self.analyser._load_table("Mock Test")
            abs_scores, rel_scores, cols = self.analyser.compute_performance(df, "101")
            fig = self.analyser.plot_performance(abs_scores, rel_scores, cols, "101", "Mock Test")
            self.assertEqual(fig.__class__.__name__, "Figure")


    # ============================================================
    # GUI TESTS
    # ============================================================

    class TestStudentPerformanceGUI(unittest.TestCase):
        """
        Tests for the GUI layer using controlled mocking to avoid real windows.
        """

        @classmethod
        def setUpClass(cls):
            cls.test_db_path = "Resultdatabase_test2.db"
            build_test_database(cls.test_db_path)

        @classmethod
        def tearDownClass(cls):
            if os.path.exists(cls.test_db_path):
                os.remove(cls.test_db_path)

        def setUp(self):
            # Mock Tk() so no real window is created
            self.tk_patcher = mock.patch("tkinter.Tk")
            MockTk = self.tk_patcher.start()
            self.mock_root = MockTk.return_value

            # Create the app using the mocked root
            self.app = StudentPerformanceGUI(db_path=self.test_db_path)

            # Ensure dropdown returns a real test name instead of a MagicMock
            self.app.test_var.get = mock.Mock(return_value="Mock Test")

        def tearDown(self):
            self.tk_patcher.stop()

        def test_gui_initialises_with_analyser(self):
            self.assertIsInstance(self.app.analyser, QuestionPerformanceAnalyser)

        def test_invalid_student_id_shows_error(self):
            self.app.student_entry.get = mock.Mock(return_value="abc")

            with mock.patch.object(messagebox, "showerror") as mock_error:
                self.app.show_results()
                mock_error.assert_called_once()

        def test_missing_student_shows_error(self):
            self.app.student_entry.get = mock.Mock(return_value="999")

            with mock.patch.object(messagebox, "showerror") as mock_error:
                self.app.show_results()
                mock_error.assert_called_once()

        @mock.patch("studentPerformance.FigureCanvasTkAgg")
        def test_valid_student_calls_analyser(self, mock_canvas):
            self.app.student_entry.get = mock.Mock(return_value="101")

            with mock.patch.object(self.app.analyser, "compute_performance",
                                   wraps=self.app.analyser.compute_performance) as mock_compute, \
                 mock.patch.object(self.app.analyser, "plot_performance",
                                   wraps=self.app.analyser.plot_performance) as mock_plot:

                self.app.show_results()

                mock_compute.assert_called_once()
                mock_plot.assert_called_once()
                mock_canvas.assert_called_once()


    # ============================================================
    # RUN TESTS
    # ============================================================

    if __name__ == "__main__":
        unittest.main()
