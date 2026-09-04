
# ------------------------------------------------------------
# underperformingStudent.py
# Identify underperforming students and visualise their results
# ------------------------------------------------------------

import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText

TEST_CODE = False #Change this to False if you would like to run the test code

# ============================================================
# UNDERPERFORMANCE ANALYSER
# ============================================================

class UnderperformanceAnalyser:
    """
    Provides tools for identifying students whose summative performance
    falls below their average across the formative assessments.
    """

    TEST_TABLES = {
        "Mock Test": "Formative_Mock_Test_Clean",
        "Formative Test 1": "Formative_Test_1_Clean",
        "Formative Test 2": "Formative_Test_2_Clean",
        "Formative Test 3": "Formative_Test_3_Clean",
        "Formative Test 4": "Formative_Test_4_Clean",
        "Summative Test": "SumTest_Clean",
    }

    def __init__(self, db_path="Resultdatabase.db"):
        self.db_path = db_path
        self.formative_tests = list(self.TEST_TABLES.keys())[:-1]
        self.summative_test = "Summative Test"

    # ---------------------- Database Loading ----------------------

    def load_all_results(self):
        merged_df = None
        with sqlite3.connect(self.db_path) as conn:
            for test_name, table_name in self.TEST_TABLES.items():
                df = pd.read_sql(f"SELECT Student_ID, Grade FROM {table_name}", conn)
                df = df.rename(columns={"Grade": test_name})

                if merged_df is None:
                    merged_df = df
                else:
                    merged_df = pd.merge(merged_df, df, on="Student_ID", how="outer")

        return merged_df

    # ---------------------- Underperformance Logic ----------------------

    def compute_underperformers(self, df):
        df = df.copy()

        for col in self.formative_tests + [self.summative_test]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        df["Formative_Avg"] = df[self.formative_tests].mean(axis=1)
        df["Diff_Sum_minus_Form"] = df[self.summative_test] - df["Formative_Avg"]

        under_df = df[df["Diff_Sum_minus_Form"] < 0].copy()

        def lowest_formative(row):
            vals = row[self.formative_tests]
            idx = vals.idxmin()
            return pd.Series({
                "Lowest_Formative_Name": idx,
                "Lowest_Formative_Score": vals[idx],
            })

        under_df = pd.concat([under_df, under_df.apply(lowest_formative, axis=1)], axis=1)

        return under_df.sort_values(by=self.summative_test)

    # ---------------------- Plotting Utilities ----------------------

    def plot_individual(self, row):
        student_id = str(row["Student_ID"])
        tests = self.formative_tests + [self.summative_test]
        scores = [row.get(t, np.nan) for t in tests]

        formative_scores = [row.get(t, np.nan) for t in self.formative_tests]
        weakest_index = int(np.nanargmin(formative_scores))

        colours = []
        for i, t in enumerate(tests):
            if t == self.summative_test:
                colours.append("#4C72B0")
            elif i == weakest_index:
                colours.append("#C44E52")
            else:
                colours.append("#55A868")

        fig, ax = plt.subplots(figsize=(10, 5))
        ax.bar(tests, scores, color=colours)

        ax.set_title(f"Test Results for Student {student_id}")
        ax.set_ylabel("Grade (%)")
        ax.set_ylim(0, 100)
        ax.grid(True, linestyle="--", alpha=0.6)
        ax.tick_params(axis="x", rotation=30)

        plt.tight_layout()
        return fig

    def plot_class_comparison(self, under_df):
        x = under_df[self.summative_test].tolist()
        y = under_df["Formative_Avg"].tolist()
        diffs = under_df["Diff_Sum_minus_Form"].tolist()

        fig, ax = plt.subplots(figsize=(14, 10))

        norm = plt.Normalize(min(diffs), 0)
        cmap = plt.cm.Reds

        scatter = ax.scatter(
            x, y,
            c=cmap(norm(diffs)),
            s=100,
            edgecolor="black",  
            picker=True,
        )

        ax.set_title("Summative vs Formative Average (Underperforming Students)")
        ax.set_xlabel("Summative Grade (%)")
        ax.set_ylabel("Formative Average (%)")
        ax.set_xlim(0, 100)
        ax.set_ylim(0, 100)
        ax.grid(True, linestyle="--", alpha=0.6)

        cbar = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), ax=ax)
        cbar.set_label("Severity of Underperformance (Darker = Larger Drop)")

        fig.tight_layout()
        return fig, ax


# ============================================================
# GUI APPLICATION
# ============================================================

class UnderperformingStudentsGUI:
    """
    Tkinter interface for identifying and visualising students who
    underperform in the summative assessment relative to their
    formative average.
    """

    def __init__(self, db_path="Resultdatabase.db"):
        self.analyser = UnderperformanceAnalyser(db_path)

        self.all_results_df = None
        self.under_df = None

        self.root = tk.Tk()
        self.root.title("Underperforming Students Analyser")
        self.root.geometry("1300x900")
        self.root.resizable(True, True)

        self._build_ui()

    # ---------------------- UI Construction ----------------------

    def _build_ui(self):
        header = (
            "Underperforming Students Analyser\n\n"
            "This tool identifies students whose summative performance "
            "is lower than their average across the formative tests.\n\n"
            "Steps:\n"
            "1. Click 'Identify Underperforming Students'.\n"
            "2. Enter a Student ID or select one from the table.\n"
            "3. Choose a visualisation.\n"
        )

        tk.Label(self.root, text=header, font=("Arial", 12), justify="left").pack(
            pady=10, anchor="w", padx=10
        )

        top_frame = tk.Frame(self.root)
        top_frame.pack(pady=5, padx=10, fill=tk.X)

        input_frame = tk.LabelFrame(top_frame, text="Input", font=("Arial", 11, "bold"))
        input_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # ---------------------- EXPLANATION LABEL ----------------------
        explanation = (
            "This table displays the top underperforming students.\n"
            "If the student ID you typed in does not show on the top underperforming students you can still view thier charts.\n"
            "The Individual Student Chart and Class Comparison Chart will update based on the Student ID you provide."
        )

        tk.Label(
            input_frame,
            text=explanation,
            font=("Arial", 10),
            justify="left",
            fg="gray20"
        ).grid(row=0, column=0, columnspan=2, padx=10, pady=(5, 10), sticky="w")

        # Student ID input
        tk.Label(input_frame, text="Student ID (1–3 digits):", font=("Arial", 12, "bold")).grid(
            row=1, column=0, padx=10, pady=5, sticky="e"
        )
        self.student_entry = tk.Entry(input_frame, font=("Arial", 12), width=10)
        self.student_entry.grid(row=1, column=1, padx=10, pady=5, sticky="w")

        # Action frame
        action_frame = tk.LabelFrame(top_frame, text="Main Actions", font=("Arial", 11, "bold"))
        action_frame.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=10)

        tk.Button(
            action_frame,
            text="Identify Underperforming Students",
            font=("Arial", 12, "bold"),
            command=self.identify_underperformers,
            width=30,
        ).pack(pady=5, padx=10)

        tk.Button(
            action_frame,
            text="Exit Program",
            font=("Arial", 12, "bold"),
            command=self.confirm_exit,
            width=18,
        ).pack(pady=5, padx=10)

        # Main content area
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Table of underperformers
        left_frame = tk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        columns = ("Student_ID", "Formative_Avg", "Summative", "Diff", "Lowest_Formative")
        self.tree = ttk.Treeview(left_frame, columns=columns, show="headings", height=15)

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=140)

        scrollbar = ttk.Scrollbar(left_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Summary box
        right_frame = tk.Frame(main_frame)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0))

        tk.Label(right_frame, text="Summary & Interpretation:", font=("Arial", 12, "bold")).pack(
            anchor="w"
        )

        self.summary_box = ScrolledText(right_frame, height=20, wrap=tk.WORD, font=("Arial", 11))
        self.summary_box.pack(fill=tk.BOTH, expand=True)
        self.summary_box.config(state="disabled")

        # Visualisation buttons
        vis_frame = tk.Frame(self.root)
        vis_frame.pack(pady=10)

        tk.Button(
            vis_frame,
            text="Individual Student Chart",
            font=("Arial", 12),
            command=self.show_individual_chart,
            width=22,
        ).pack(side=tk.LEFT, padx=10)

        tk.Button(
            vis_frame,
            text="Class Comparison Chart",
            font=("Arial", 12),
            command=self.show_class_comparison_chart,
            width=22,
        ).pack(side=tk.LEFT, padx=10)

    # ========================================================
    # CORE CALLBACKS
    # ========================================================

    def identify_underperformers(self):
        try:
            self.all_results_df = self.analyser.load_all_results()
        except Exception as e:
            messagebox.showerror("Database Error", str(e))
            return

        self.under_df = self.analyser.compute_underperformers(self.all_results_df)

        for row in self.tree.get_children():
            self.tree.delete(row)

        self.summary_box.config(state="normal")
        self.summary_box.delete("1.0", tk.END)

        if self.under_df.empty:
            self.summary_box.insert(tk.END, "No underperforming students found.\n")
            self.summary_box.config(state="disabled")
            return

        for _, row in self.under_df.iterrows():
            sid = row["Student_ID"]
            form_avg = row["Formative_Avg"]
            summ = row[self.analyser.summative_test]
            diff = row["Diff_Sum_minus_Form"]
            lowest_name = row["Lowest_Formative_Name"]
            lowest_score = row["Lowest_Formative_Score"]

            self.tree.insert(
                "",
                tk.END,
                values=(
                    sid,
                    f"{form_avg:.2f}",
                    f"{summ:.2f}",
                    f"{diff:.2f}",
                    f"{lowest_name} ({lowest_score:.2f}%)",
                ),
            )

            self.summary_box.insert(
                tk.END,
                f"Student {sid}:\n"
                f"  • Avg formative: {form_avg:.2f}%\n"
                f"  • Summative: {summ:.2f}%\n"
                f"  • Drop: {diff:.2f}%\n"
                f"  • Lowest formative: {lowest_name} ({lowest_score:.2f}%)\n\n",
            )

        self.summary_box.config(state="disabled")

    # ========================================================
    # VISUALISATION CALLBACKS
    # ========================================================

    def _get_student_id(self):
        sid = self.student_entry.get().strip()

        if sid:
            if not sid.isdigit() or len(sid) > 3:
                messagebox.showerror("Invalid Student ID", "Student ID must be 1 to 3 digits.")
                return None
            return sid

        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No Student Selected", "Please enter or select a Student ID.")
            return None

        values = self.tree.item(selected[0], "values")
        return str(values[0]) if values else None

    def show_individual_chart(self):
        if self.all_results_df is None:
            messagebox.showwarning("No Data", "Please identify underperforming students first.")
            return

        sid = self._get_student_id()
        if sid is None:
            return

        row = self.all_results_df[self.all_results_df["Student_ID"].astype(str) == sid]
        if row.empty:
            messagebox.showerror("Error", f"No data found for Student {sid}.")
            return

        row = row.iloc[0]
        fig = self.analyser.plot_individual(row)

        window = tk.Toplevel(self.root)
        window.title(f"Individual Chart – Student {sid}")
        window.geometry("900x600")

        canvas = FigureCanvasTkAgg(fig, master=window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def show_class_comparison_chart(self):
        if self.under_df is None or self.under_df.empty:
            messagebox.showwarning("No Data", "Please identify underperforming students first.")
            return

        fig, ax = self.analyser.plot_class_comparison(self.under_df)

        student_ids = self.under_df["Student_ID"].astype(str).tolist()

        def on_pick(event):
            index = event.ind[0]
            sid = student_ids[index]
            self.student_entry.delete(0, tk.END)
            self.student_entry.insert(0, sid)
            self.show_individual_chart()

        fig.canvas.mpl_connect("pick_event", on_pick)

        window = tk.Toplevel(self.root)
        window.title("Class Comparison Scatter Plot")
        window.geometry("1400x900")

        canvas = FigureCanvasTkAgg(fig, master=window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    # ========================================================
    # EXIT + MAIN LOOP
    # ========================================================

    def confirm_exit(self):
        if messagebox.askokcancel("Exit", "Quit the program?"):
            self.root.destroy()

    def run(self):
        self.root.mainloop()


# ============================================================
# MAIN PROGRAM
# ============================================================

if __name__ == "__main__" and not TEST_CODE:
    app = UnderperformingStudentsGUI()
    app.run()


# ============================================================
# TEST CODE
# ============================================================

if TEST_CODE:
    import unittest
    from unittest import mock
    import os

    # A non-interactive backend so matplotlib doesn't try to open windows
    plt.switch_backend("Agg")

    def build_test_database(db_path):
        """
        Creates a small SQLite database for testing underperformance logic.
        Includes realistic formative and summative grades.
        """
        if os.path.exists(db_path):
            os.remove(db_path)

        conn = sqlite3.connect(db_path)

        table_definitions = {
            "Formative_Mock_Test_Clean": [("101", 60), ("102", 70), ("103", 80)],
            "Formative_Test_1_Clean":    [("101", 62), ("102", 72), ("103", 82)],
            "Formative_Test_2_Clean":    [("101", 64), ("102", 74), ("103", 84)],
            "Formative_Test_3_Clean":    [("101", 66), ("102", 76), ("103", 86)],
            "Formative_Test_4_Clean":    [("101", 68), ("102", 78), ("103", 88)],
            "SumTest_Clean":             [("101", 50), ("102", 75), ("103", 95)],
        }

        for table_name, rows in table_definitions.items():
            df = pd.DataFrame(rows, columns=["Student_ID", "Grade"])
            df.to_sql(table_name, conn, index=False, if_exists="replace")

        conn.close()


    # ============================================================
    # ANALYSER TESTS
    # ============================================================

    class TestUnderperformanceAnalyser(unittest.TestCase):

        @classmethod
        def setUpClass(cls):
            cls.test_db_path = "Resultdatabase_under_test.db"
            build_test_database(cls.test_db_path)
            cls.analyser = UnderperformanceAnalyser(db_path=cls.test_db_path)

        @classmethod
        def tearDownClass(cls):
            if os.path.exists(cls.test_db_path):
                os.remove(cls.test_db_path)

        def test_load_all_results_returns_dataframe(self):
            df = self.analyser.load_all_results()
            self.assertFalse(df.empty)
            self.assertIn("Mock Test", df.columns)
            self.assertIn("Summative Test", df.columns)
            self.assertEqual(len(df), 3)

        def test_compute_underperformers_identifies_correct_student(self):
            df = self.analyser.load_all_results()
            under_df = self.analyser.compute_underperformers(df)
            self.assertEqual(len(under_df), 1)
            self.assertEqual(str(under_df.iloc[0]["Student_ID"]), "101")

        def test_compute_underperformers_lowest_formative(self):
            df = self.analyser.load_all_results()
            under_df = self.analyser.compute_underperformers(df)
            row = under_df.iloc[0]
            self.assertIn("Lowest_Formative_Name", row)
            self.assertIn("Lowest_Formative_Score", row)

        def test_plot_individual_returns_figure(self):
            df = self.analyser.load_all_results()
            row = df[df["Student_ID"] == "101"].iloc[0]
            fig = self.analyser.plot_individual(row)
            self.assertEqual(fig.__class__.__name__, "Figure")

        def test_plot_class_comparison_returns_figure_and_axis(self):
            df = self.analyser.load_all_results()
            under_df = self.analyser.compute_underperformers(df)
            fig, ax = self.analyser.plot_class_comparison(under_df)
            self.assertEqual(fig.__class__.__name__, "Figure")
            self.assertIsNotNone(ax)


    # ============================================================
    # GUI TESTS
    # ============================================================

    class TestUnderperformingStudentsGUI(unittest.TestCase):

        @classmethod
        def setUpClass(cls):
            cls.test_db_path = "Resultdatabase_under_test.db"
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
            self.app = UnderperformingStudentsGUI(db_path=self.test_db_path)

            # Treeview selection returns a real student ID
            self.app.tree.selection = mock.Mock(return_value=["item1"])
            self.app.tree.item = mock.Mock(return_value={"values": ["101"]})

        def tearDown(self):
            self.tk_patcher.stop()

        def test_gui_initialises_with_analyser(self):
            self.assertIsInstance(self.app.analyser, UnderperformanceAnalyser)

        def test_identify_underperformers_populates_tree(self):
            with mock.patch.object(self.app.tree, "insert") as mock_insert:
                self.app.identify_underperformers()
                mock_insert.assert_called()

        def test_invalid_student_id_in_individual_chart(self):
            self.app.all_results_df = self.app.analyser.load_all_results()
            self.app.student_entry.get = mock.Mock(return_value="abc")

            with mock.patch.object(messagebox, "showerror") as mock_error:
                self.app.show_individual_chart()
                mock_error.assert_called_once()

        @mock.patch("underperformingStudent.FigureCanvasTkAgg")
        def test_show_individual_chart_calls_plot(self, mock_canvas):
            self.app.identify_underperformers()
            self.app.student_entry.get = mock.Mock(return_value="101")

            with mock.patch.object(self.app.analyser, "plot_individual",
                                   wraps=self.app.analyser.plot_individual) as mock_plot:
                self.app.show_individual_chart()
                mock_plot.assert_called_once()
                mock_canvas.assert_called_once()

        @mock.patch("underperformingStudent.FigureCanvasTkAgg")
        def test_show_class_comparison_chart_calls_plot(self, mock_canvas):
            self.app.identify_underperformers()

            with mock.patch.object(self.app.analyser, "plot_class_comparison",
                                   wraps=self.app.analyser.plot_class_comparison) as mock_plot:
                self.app.show_class_comparison_chart()
                mock_plot.assert_called_once()
                mock_canvas.assert_called_once()


    # ============================================================
    # RUN TESTS
    # ============================================================

    if __name__ == "__main__":
        unittest.main()
