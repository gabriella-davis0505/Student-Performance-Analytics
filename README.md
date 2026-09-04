# Student Performance Analytics

MSc Data Science programming project developing an **end-to-end student assessment analytics application** using Python, Pandas, SQLite, Matplotlib and Tkinter.

The application processes raw assessment CSV files, standardises scores, creates a SQLite database and provides interactive tools for analysing student performance at both individual and class level.

---

## Project Overview

The aim of this project was to develop a reusable system for processing and analysing student assessment data.

The workflow covers:

**Raw CSV assessment data → Data preprocessing → SQLite database → Student performance analysis → Visualisation**

The application consists of a central dashboard and several analytical tools that allow users to:

- preprocess raw assessment data;
- examine a student's performance across multiple assessments;
- analyse question-level strengths and weaknesses;
- compare individual performance with class averages; and
- identify students whose summative performance has fallen below their formative performance.

---

## Application Components

### Data Preprocessing

`CWPreprocessing.py` provides the data-processing pipeline.

The preprocessing stage:

- reads assessment CSV files from the `TestResult` folder;
- identifies question-level score columns;
- handles different scoring formats;
- converts question scores to percentages;
- recalculates overall grades;
- standardises column names;
- removes duplicate student attempts while retaining the highest grade;
- creates cleaned datasets; and
- stores the results in a generated SQLite database.

The application supports question scores represented as:

- percentages;
- proportions;
- scaled proportions; and
- raw points.

This enables assessment files with different scoring structures to be processed consistently.

---

## Student Results Viewer

`testResults.py` analyses a student's performance across the available assessments.

The tool retrieves results from the SQLite database and provides:

- student scores across multiple tests;
- overall student mean;
- overall class mean;
- class mean for each assessment;
- median;
- mode;
- standard deviation;
- score range; and
- comparison of the student's result with the class average.

A bar chart is also generated to visualise the student's performance across assessments.

---

## Question-Level Performance Analysis

`studentPerformance.py` provides more detailed analysis of an individual assessment.

For a selected student and test, the application calculates:

### Absolute Performance

The student's percentage score for each question.

### Relative Performance

The difference between the student's score and the class mean for each question.

This makes it possible to identify individual areas of strength and weakness rather than relying only on the overall assessment grade.

The results are displayed using interactive tables, descriptive statistics and Matplotlib visualisations.

---

## Underperforming Students Analysis

`underperformingStudent.py` identifies students whose performance in the summative assessment is lower than their average performance across the formative assessments.

For each student, the tool calculates:

- average formative performance;
- summative performance;
- difference between summative and formative performance; and
- the student's weakest formative assessment.

Interactive visualisations allow individual students and the wider group of underperforming students to be explored.

---

## Assessment Analysis Dashboard

`menu.ipynb` provides a central interface for accessing the different components of the project.

The dashboard includes options for:

- Data Preprocessing
- Test Results Viewer
- Question-Level Student Performance
- Underperforming Students
- Help / Instructions
- Database Reset
- System Log
- Dark Mode

The dashboard launches the individual Python applications while keeping the project's functionality accessible from one interface.

---

## Assessment Data

The `TestResult` directory contains the assessment CSV files used by the application:

```text
TestResult/
├── Formative_Mock_Test.csv
├── Formative_Test_1.csv
├── Formative_Test_2.csv
├── Formative_Test_3.csv
├── Formative_Test_4.csv
├── SumTest.csv
└── StudentRate.csv
```

The datasets used in this project are fictional assessment datasets created for the coursework and do not contain real student information.

The preprocessing pipeline converts the assessment data into a SQLite database for subsequent analysis.

---

## Repository Structure

```text
student-performance-analytics/
│
├── README.md
├── .gitignore
├── requirements.txt
│
├── menu.ipynb
├── CWPreprocessing.py
├── testResults.py
├── studentPerformance.py
├── underperformingStudent.py
│
└── TestResult/
    ├── Formative_Mock_Test.csv
    ├── Formative_Test_1.csv
    ├── Formative_Test_2.csv
    ├── Formative_Test_3.csv
    ├── Formative_Test_4.csv
    ├── SumTest.csv
    └── StudentRate.csv
```

`Resultdatabase.db` is generated when the preprocessing pipeline is run and is therefore not stored in the repository.

---

## Technologies

### Programming

- Python
- Jupyter Notebook

### Data Processing

- Pandas
- NumPy

### Database

- SQLite
- Python `sqlite3`

### Visualisation

- Matplotlib

### User Interface

- Tkinter
- ipywidgets

### Software Development

- Object-oriented programming
- Data validation
- Reusable classes and functions
- Exception handling
- Automated testing
- Database integration
- GUI development

---

## How to Run the Project

### 1. Clone the Repository

Clone or download the repository and open a terminal in the project directory.

### 2. Install Python Dependencies

Install the required Python packages using:

```bash
pip install -r requirements.txt
```

The `requirements.txt` file contains:

```text
pandas
numpy
matplotlib
ipywidgets
```

Tkinter and SQLite are included with many standard Python installations, although Tkinter may need to be installed separately depending on the operating system.

### 3. Preprocess the Assessment Data

Run:

```bash
python CWPreprocessing.py
```

This reads the CSV files contained in `TestResult/` and generates:

```text
Resultdatabase.db
```

### 4. Run an Analysis Tool

The individual applications can then be launched using:

```bash
python testResults.py
```

```bash
python studentPerformance.py
```

or:

```bash
python underperformingStudent.py
```

Alternatively, open:

```text
menu.ipynb
```

in Jupyter Notebook and run the dashboard to access the tools from a central interface.

---

## Key Features

- End-to-end CSV-to-database processing pipeline
- Automatic score standardisation
- SQLite database creation
- Individual student performance analysis
- Class-level descriptive statistics
- Question-level performance analysis
- Student-versus-class comparisons
- Automated identification of underperforming students
- Interactive Tkinter interfaces
- Matplotlib visualisations
- Jupyter-based central dashboard
- Built-in testing within the Python modules

---

## Skills Demonstrated

This project demonstrates experience in:

- Python programming;
- object-oriented programming;
- Pandas data manipulation;
- data cleaning and preprocessing;
- SQLite database integration;
- data validation;
- descriptive statistics;
- analytical problem solving;
- data visualisation;
- GUI development;
- modular software design;
- automated testing; and
- developing an end-to-end data application.

---

## Academic Context

This repository contains work completed as part of an **MSc Data Science Programming Fundamentals module**.

The repository has been included in my data science portfolio to demonstrate programming, data-processing, database and analytical application development skills.

---

## Author

**Gabriella Davis**

MSc Data Science

GitHub: `gabriella-davis0505`
