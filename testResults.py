
# ------------------------------------------------------------
# testResults.py
# View a student's performance across all assessments.
# ------------------------------------------------------------

import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText

RUN_TESTS = False #Change this to True if you would like to run the tests

# ============================================================
# PERFORMANCE ANALYSER
# (Handles database access, statistics, and plotting)
# ============================================================

class PerformanceAnalyser:
    """
    Provides a unified interface for retrieving student results,
    computing descriptive statistics, and generating performance
    plots. This class consolidates the core analytical tasks so
    that the GUI can focus solely on user interaction.
    """

    def __init__(self, db_path="Resultdatabase.db"):
        self.db_path = db_path

        # Mapping between cleaned table names and user-friendly labels
        self.table_map = {
            "Formative_Mock_Test_Clean": "Mock Test",
            "Formative_Test_1_Clean": "Formative Test 1",
            "Formative_Test_2_Clean": "Formative Test 2",
            "Formative_Test_3_Clean": "Formative Test 3",
            "Formative_Test_4_Clean": "Formative Test 4",
            "SumTest_Clean": "Summative Test"
        }

        # Reverse lookup for retrieving raw table names
        self.reverse_map = {v: k for k, v in self.table_map.items()}

    # ---------------------- Database Utilities ----------------------

    def _read_table(self, table_name):
        """Internal helper to read a table from the SQLite database."""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
        conn.close()
        return df

    def get_student_scores(self, student_id):
        """
        Retrieves all available grades for a given student across
        the different assessment tables. Returns a dictionary
        mapping test names to grades.
        """
        scores = {}
        for table, friendly in self.table_map.items():
            df = self._read_table(table)
            match = df[df["Student_ID"].astype(str) == str(student_id)]
            if not match.empty:
                scores[friendly] = match["Grade"].values[0]
        return scores

    def get_test_scores(self, test_name):
        """
        Retrieves the full set of grades for a particular test.
        This is used to compute class-level statistics.
        """
        raw_table = self.reverse_map[test_name]
        return self._read_table(raw_table)

    # ---------------------- Statistics Generation ----------------------

    def generate_summary(self, student_id):
        """
        Produces a structured textual summary of the student's
        performance, including overall mean, class comparisons,
        and descriptive statistics for each test taken.
        """
        scores = self.get_student_scores(student_id)

        if not scores:
            return None

        student_mean = round(np.mean(list(scores.values())), 2)

        class_means = []
        for test_name in scores.keys():
            df = self.get_test_scores(test_name)
            class_means.append(df["Grade"].mean())

        overall_class_mean = round(np.mean(class_means), 2)

        summary = f"=== OVERALL SUMMARY ===\n"
        summary += f"Overall student mean: {student_mean}\n"
        summary += f"Overall class mean: {overall_class_mean}\n\n"

        summary += "=== TEST-BY-TEST BREAKDOWN ===\n"

        for test_name, student_score in scores.items():
            df = self.get_test_scores(test_name)
            class_scores = df["Grade"]

            summary += f"\n{test_name}:\n"
            summary += f"• Student scored {student_score}\n"
            summary += f"• Class mean = {round(class_scores.mean(), 2)}\n"
            summary += f"• Class median = {round(class_scores.median(), 2)}\n"
            summary += f"• Class mode = {class_scores.mode().iloc[0]}\n"
            summary += f"• Class standard deviation = {round(class_scores.std(), 2)}\n"
            summary += f"• Class range = {class_scores.min()}–{class_scores.max()}\n"

            if student_score > class_scores.mean():
                summary += "• Student is ABOVE the class mean\n"
            elif student_score < class_scores.mean():
                summary += "• Student is BELOW the class mean\n"
            else:
                summary += "• Student scored EXACTLY the class mean\n"

        summary += "\n\n=== HOW TO INTERPRET THESE STATISTICS ===\n"
        summary += "• Mean: the average score.\n"
        summary += "• Median: the middle score.\n"
        summary += "• Mode: the most common score.\n"
        summary += "• Standard Deviation: spread of scores.\n"
        summary += "• Range: lowest to highest score.\n"

        return summary

    # ---------------------- Plotting ----------------------

    def plot_student(self, student_id):
        """
        Generates a bar chart showing the student's performance
        across all tests they have completed.
        """
        scores = self.get_student_scores(student_id)
        if not scores:
            return None

        fig, ax = plt.subplots(figsize=(8, 5))

        colours = ["#4C72B0", "#55A868", "#C44E52",
                   "#8172B2", "#64B5CD", "#8C8C8C"]

        ax.bar(scores.keys(), scores.values(),
               color=colours[:len(scores)])

        ax.set_title(f"Student {student_id} – Performance Across Tests")
        ax.set_xlabel("Assessment")
        ax.set_ylabel("Total Grade")

        plt.xticks(rotation=30, ha="right")
        ax.grid(True, linestyle="--", alpha=0.6)
        plt.tight_layout()

        return fig


# ============================================================
# GUI APPLICATION
# ============================================================

class AssessmentApp:
    """
    Tkinter-based interface for viewing student performance.
    The GUI delegates all analytical work to PerformanceAnalyser.
    """

    def __init__(self, db_path="Resultdatabase.db"):
        self.analyser = PerformanceAnalyser(db_path)

        self.root = tk.Tk()
        self.root.title("Student Assessment Viewer")
        self.root.geometry("1100x800")

        self._build_ui()
        self.root.bind("<Return>", lambda event: self.view_student())

    # ---------------------- UI Construction ----------------------

    def _build_ui(self):
        tk.Label(
            self.root,
            text="Enter a Student ID and click 'View Student Performance'",
            font=("Arial", 12, "bold")
        ).pack(pady=10)

        tk.Label(self.root, text="Student ID:").pack()
        self.student_entry = tk.Entry(self.root)
        self.student_entry.pack(pady=5)

        self.student_entry.insert(0, "e.g. 123")
        self.student_entry.config(fg="grey")

        def clear_placeholder(event):
            if self.student_entry.get() == "e.g. 123":
                self.student_entry.delete(0, tk.END)
                self.student_entry.config(fg="black")

        self.student_entry.bind("<FocusIn>", clear_placeholder)

        ttk.Separator(self.root, orient="horizontal").pack(fill="x", pady=10)

        self.plot_frame = tk.Frame(self.root, height=400)
        self.plot_frame.pack(fill=tk.BOTH, expand=True)

        self.summary_box = ScrolledText(self.root, height=12, wrap=tk.WORD,
                                        font=("Arial", 11))
        self.summary_box.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.summary_box.config(state="normal")
        self.summary_box.insert(tk.END, "Results will appear here...")
        self.summary_box.config(state="disabled")

        tk.Button(
            self.root,
            text="View Student Performance",
            font=("Arial", 12, "bold"),
            command=self.view_student
        ).pack(pady=10)

        tk.Button(
            self.root,
            text="Exit Program",
            command=self.root.destroy,
            font=("Arial", 12, "bold")
        ).pack(pady=20)

    # ---------------------- Main Callback ----------------------

    def view_student(self):
        student_id = self.student_entry.get().strip()

        if not student_id.isdigit() or not (1 <= len(student_id) <= 3):
            messagebox.showerror("Invalid Format", "Student ID must be 1–3 digits.")
            return

        summary = self.analyser.generate_summary(student_id)
        if summary is None:
            messagebox.showerror("Invalid Student ID", "This Student ID does not exist.")
            return

        fig = self.analyser.plot_student(student_id)

        for widget in self.plot_frame.winfo_children():
            widget.destroy()

        canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.summary_box.config(state="normal")
        self.summary_box.delete("1.0", tk.END)
        self.summary_box.insert(tk.END, summary)
        self.summary_box.config(state="disabled")

    def run(self):
        self.root.mainloop()


# ============================================================
# MAIN PROGRAM
# ============================================================

if __name__ == "__main__" and not RUN_TESTS:
    app = AssessmentApp()
    app.run()


# ============================================================
# TEST CODE
# ============================================================

if RUN_TESTS:
    import unittest
    from unittest import mock
    import os

    # Use a non-interactive backend so matplotlib doesn't try to open windows during tests
    plt.switch_backend("Agg")

    def build_test_database(db_path):
        """
        Creates a small SQLite database purely for testing.
        """
        if os.path.exists(db_path):
            os.remove(db_path)

        conn = sqlite3.connect(db_path)

        table_definitions = {
            "Formative_Mock_Test_Clean": [("101", 50), ("102", 60), ("103", 70)],
            "Formative_Test_1_Clean":    [("101", 55), ("102", 65), ("103", 75)],
            "Formative_Test_2_Clean":    [("101", 58), ("102", 68), ("103", 78)],
            "Formative_Test_3_Clean":    [("101", 62), ("102", 72), ("103", 82)],
            "Formative_Test_4_Clean":    [("101", 64), ("102", 74), ("103", 84)],
            "SumTest_Clean":             [("101", 70), ("102", 80), ("103", 90)],
        }

        for table_name, rows in table_definitions.items():
            df = pd.DataFrame(rows, columns=["Student_ID", "Grade"])
            df.to_sql(table_name, conn, index=False, if_exists="replace")

        conn.close()


    # ============================================================
    # ANALYSER TESTS
    # ============================================================

    class TestPerformanceAnalyser(unittest.TestCase):

        @classmethod
        def setUpClass(cls):
            cls.test_db_path = "Resultdatabase_test.db"
            build_test_database(cls.test_db_path)
            cls.analyser = PerformanceAnalyser(db_path=cls.test_db_path)

        @classmethod
        def tearDownClass(cls):
            if os.path.exists(cls.test_db_path):
                os.remove(cls.test_db_path)

        def test_read_table_returns_dataframe(self):
            df = self.analyser._read_table("Formative_Mock_Test_Clean")
            self.assertFalse(df.empty)
            self.assertIn("Student_ID", df.columns)
            self.assertIn("Grade", df.columns)
            self.assertEqual(len(df), 3)

        def test_get_student_scores_existing_student(self):
            scores = self.analyser.get_student_scores("101")
            self.assertEqual(len(scores), len(self.analyser.table_map))
            self.assertIn("Mock Test", scores)
            self.assertEqual(scores["Mock Test"], 50)

        def test_get_student_scores_nonexistent_student(self):
            scores = self.analyser.get_student_scores("999")
            self.assertEqual(scores, {})

        def test_get_test_scores_returns_correct_table(self):
            df = self.analyser.get_test_scores("Mock Test")
            self.assertFalse(df.empty)
            self.assertEqual(len(df), 3)
            self.assertEqual(sorted(df["Student_ID"].tolist()), ["101", "102", "103"])

        def test_generate_summary_existing_student(self):
            summary = self.analyser.generate_summary("101")
            self.assertIsNotNone(summary)
            self.assertIn("=== OVERALL SUMMARY ===", summary)
            self.assertIn("=== TEST-BY-TEST BREAKDOWN ===", summary)
            self.assertIn("Mock Test:", summary)
            self.assertIn("Student scored 50", summary)

        def test_generate_summary_nonexistent_student(self):
            summary = self.analyser.generate_summary("999")
            self.assertIsNone(summary)

        def test_plot_student_returns_figure(self):
            fig = self.analyser.plot_student("101")
            self.assertIsNotNone(fig)
            self.assertEqual(fig.__class__.__name__, "Figure")

        def test_plot_student_nonexistent_student(self):
            fig = self.analyser.plot_student("999")
            self.assertIsNone(fig)


    # ============================================================
    # GUI TESTS
    # ============================================================

    class TestAssessmentApp(unittest.TestCase):

        @classmethod
        def setUpClass(cls):
            cls.test_db_path = "Resultdatabase_test.db"
            build_test_database(cls.test_db_path)

        @classmethod
        def tearDownClass(cls):
            if os.path.exists(cls.test_db_path):
                os.remove(cls.test_db_path)

        def setUp(self):
            self.root_patcher = mock.patch("tkinter.Tk")
            MockTk = self.root_patcher.start()
            self.mock_root = MockTk.return_value

            self.app = AssessmentApp(db_path=self.test_db_path)

        def tearDown(self):
            self.root_patcher.stop()

        def test_app_initialises_with_analyser(self):
            self.assertIsInstance(self.app.analyser, PerformanceAnalyser)
            self.assertEqual(self.app.analyser.db_path, self.test_db_path)

        def test_view_student_invalid_format_shows_error(self):
            self.app.student_entry.get = mock.Mock(return_value="abc")

            with mock.patch.object(messagebox, "showerror") as mock_error:
                self.app.view_student()
                mock_error.assert_called_once()
                args, kwargs = mock_error.call_args
                self.assertIn("Invalid Format", args[0])

        def test_view_student_nonexistent_id_shows_error(self):
            self.app.student_entry.get = mock.Mock(return_value="999")

            with mock.patch.object(messagebox, "showerror") as mock_error:
                self.app.view_student()
                mock_error.assert_called_once()
                args, kwargs = mock_error.call_args
                self.assertIn("Invalid Student ID", args[0])

        @mock.patch("testResults.FigureCanvasTkAgg")
        def test_view_student_valid_id_calls_analyser(self, mock_canvas):
            self.app.student_entry.get = mock.Mock(return_value="101")

            with mock.patch.object(self.app.analyser, "generate_summary",
                                   wraps=self.app.analyser.generate_summary) as mock_summary, \
                 mock.patch.object(self.app.analyser, "plot_student",
                                   wraps=self.app.analyser.plot_student) as mock_plot:

                self.app.view_student()

                mock_summary.assert_called_once_with("101")
                mock_plot.assert_called_once_with("101")
                mock_canvas.assert_called_once()


    # ============================================================
    # RUN TESTS
    # ============================================================

    if __name__ == "__main__":
        unittest.main()
