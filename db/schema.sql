-- Matches the ERD in PRD Section 6 / thesis Chapter 3, Figure 3.4
CREATE TABLE IF NOT EXISTS patient (
    patient_id TEXT PRIMARY KEY,
    age INTEGER NOT NULL,
    sex TEXT NOT NULL,
    location TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS visit (
    visit_id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id TEXT NOT NULL,
    visit_date TEXT NOT NULL,
    facility TEXT,
    FOREIGN KEY (patient_id) REFERENCES patient(patient_id)
);

CREATE TABLE IF NOT EXISTS diagnosis (
    diagnosis_id INTEGER PRIMARY KEY AUTOINCREMENT,
    visit_id INTEGER NOT NULL,
    disease_code TEXT NOT NULL,
    disease_name TEXT NOT NULL,
    glucose REAL,
    bmi REAL,
    hba1c REAL,
    fever_days REAL,
    parasite_density REAL,
    FOREIGN KEY (visit_id) REFERENCES visit(visit_id)
);

CREATE TABLE IF NOT EXISTS trend_report (
    report_id INTEGER PRIMARY KEY AUTOINCREMENT,
    disease_code TEXT NOT NULL,
    period TEXT NOT NULL,      -- 'YYYY-MM'
    location TEXT NOT NULL,
    trend_value REAL NOT NULL, -- case count for that disease/period/location
    generated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_visit_patient ON visit(patient_id);
CREATE INDEX IF NOT EXISTS idx_diagnosis_visit ON diagnosis(visit_id);
CREATE INDEX IF NOT EXISTS idx_trend_disease_period ON trend_report(disease_code, period);
