import psycopg2

DB_CONFIG = {
    "host":     "localhost",
    "port":     5432,
    "database": "hospital_db",
    "user":     "postgres",
    "password": "post2026"   # ← Change this
}

conn   = psycopg2.connect(**DB_CONFIG)
cursor = conn.cursor()

# Drop all old tables
tables = ['billing','prescriptions','scans','vitals','appointments','patients','users']
for t in tables:
    cursor.execute(f"DROP TABLE IF EXISTS {t} CASCADE")

# Users table
cursor.execute('''
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username TEXT,
    password TEXT,
    role TEXT,
    staff_type TEXT,
    specialization TEXT,
    rfid TEXT
)''')

# Patients table
cursor.execute('''
CREATE TABLE patients (
    id INTEGER PRIMARY KEY,
    name TEXT,
    rfid TEXT,
    disease TEXT,
    history TEXT,
    ward TEXT,
    medication TEXT,
    doctor TEXT,
    admitted_date TEXT,
    discharge_date TEXT,
    next_appointment TEXT,
    status TEXT DEFAULT 'admitted'
)''')

# Appointments
cursor.execute('''
CREATE TABLE appointments (
    id SERIAL PRIMARY KEY,
    doctor_id INTEGER,
    patient_name TEXT,
    date TEXT,
    type TEXT
)''')

# Vitals
cursor.execute('''
CREATE TABLE vitals (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER,
    bp TEXT,
    pulse TEXT,
    temperature TEXT,
    oxygen TEXT,
    recorded_by TEXT,
    recorded_at TEXT
)''')

# Scans
cursor.execute('''
CREATE TABLE scans (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER,
    scan_type TEXT,
    scan_result TEXT,
    uploaded_by TEXT,
    uploaded_at TEXT
)''')

# Prescriptions
cursor.execute('''
CREATE TABLE prescriptions (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER,
    medicine TEXT,
    dosage TEXT,
    duration TEXT,
    notes TEXT,
    prescribed_by TEXT,
    prescribed_at TEXT
)''')

# Billing
cursor.execute('''
CREATE TABLE billing (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER,
    description TEXT,
    amount REAL,
    date TEXT,
    added_by TEXT
)''')

# ── SAMPLE DATA ───────────────────────────────────────────────


# Doctors
cursor.execute("INSERT INTO users (username,password,role,staff_type,specialization,rfid) VALUES ('dr.kumar','doc123','doctor','Doctor','Physician','RFID002')")
cursor.execute("INSERT INTO users (username,password,role,staff_type,specialization,rfid) VALUES ('dr.priya','doc456','doctor','Doctor','Gynaecologist','RFID003')")

# Staff — 2 Nurses
cursor.execute("INSERT INTO users (username,password,role,staff_type,specialization,rfid) VALUES ('nurse.rani','staff123','staff','Nurse','General Nursing','RFID004')")
cursor.execute("INSERT INTO users (username,password,role,staff_type,specialization,rfid) VALUES ('nurse.meena','staff222','staff','Nurse','ICU Nursing','RFID008')")

# Pharmacist
cursor.execute("INSERT INTO users (username,password,role,staff_type,specialization,rfid) VALUES ('pharma.meena','staff789','staff','Pharmacist','Pharmacy','RFID006')")

# Receptionist
cursor.execute("INSERT INTO users (username,password,role,staff_type,specialization,rfid) VALUES ('receptionist.ravi','staff456','staff','Receptionist','Front Desk','RFID005')")

# Patients
cursor.execute("INSERT INTO users (username,password,role,staff_type,specialization,rfid) VALUES ('asha','pat123','patient','Patient','N/A','RFID007')")
cursor.execute("INSERT INTO users (username,password,role,staff_type,specialization,rfid) VALUES ('ramu','pat456','patient','Patient','N/A','RFID009')")
cursor.execute("INSERT INTO users (username,password,role,staff_type,specialization,rfid) VALUES ('sunita','pat789','patient','Patient','N/A','RFID010')")
cursor.execute("INSERT INTO users (username,password,role,staff_type,specialization,rfid) VALUES ('vijay','pat000','patient','Patient','N/A','RFID011')")
cursor.execute("INSERT INTO users (username,password,role,staff_type,specialization,rfid) VALUES ('lakshmi','pat111','patient','Patient','N/A','RFID012')")

# Get IDs
cursor.execute("SELECT id FROM users WHERE username='dr.kumar'");  did2  = cursor.fetchone()[0]
cursor.execute("SELECT id FROM users WHERE username='dr.priya'");  did3  = cursor.fetchone()[0]
cursor.execute("SELECT id FROM users WHERE username='asha'");      pid7  = cursor.fetchone()[0]
cursor.execute("SELECT id FROM users WHERE username='ramu'");      pid8  = cursor.fetchone()[0]
cursor.execute("SELECT id FROM users WHERE username='sunita'");    pid9  = cursor.fetchone()[0]
cursor.execute("SELECT id FROM users WHERE username='vijay'");     pid10 = cursor.fetchone()[0]
cursor.execute("SELECT id FROM users WHERE username='lakshmi'");   pid11 = cursor.fetchone()[0]

# Patient records
cursor.execute("INSERT INTO patients VALUES (%s,'Asha','RFID007','Fever','Visited 3 times','Ward A','Paracetamol 500mg','Dr. Kumar','2025-04-10','','2025-05-01','admitted')",(pid7,))
cursor.execute("INSERT INTO patients VALUES (%s,'Ramu','RFID009','Diabetes','Visited 5 times','Ward B','Insulin 10 units','Dr. Priya','2025-04-12','','2025-04-28','admitted')",(pid8,))
cursor.execute("INSERT INTO patients VALUES (%s,'Sunita','RFID010','Fracture','First visit','Ward C','Calcium + Rest','Dr. Kumar','2025-04-15','','2025-05-05','admitted')",(pid9,))
cursor.execute("INSERT INTO patients VALUES (%s,'Vijay','RFID011','BP High','Visited 2 times','Ward A','Amlodipine 5mg','Dr. Priya','2025-04-18','','2025-04-30','admitted')",(pid10,))
cursor.execute("INSERT INTO patients VALUES (%s,'Lakshmi','RFID012','Asthma','Visited 4 times','Ward B','Inhaler + Steroids','Dr. Kumar','2025-04-19','','2025-05-10','admitted')",(pid11,))

# Appointments
cursor.execute("INSERT INTO appointments (doctor_id,patient_name,date,type) VALUES (%s,'Asha','2025-04-22','OPD')",(did2,))
cursor.execute("INSERT INTO appointments (doctor_id,patient_name,date,type) VALUES (%s,'Sunita','2025-04-23','OT')",(did2,))
cursor.execute("INSERT INTO appointments (doctor_id,patient_name,date,type) VALUES (%s,'Lakshmi','2025-04-24','Round')",(did2,))
cursor.execute("INSERT INTO appointments (doctor_id,patient_name,date,type) VALUES (%s,'Ramu','2025-04-22','OPD')",(did3,))
cursor.execute("INSERT INTO appointments (doctor_id,patient_name,date,type) VALUES (%s,'Vijay','2025-04-23','OPD')",(did3,))

# Vitals
cursor.execute("INSERT INTO vitals (patient_id,bp,pulse,temperature,oxygen,recorded_by,recorded_at) VALUES (%s,'120/80','72','98.6','99','Nurse Rani','2025-04-20 09:00')",(pid7,))
cursor.execute("INSERT INTO vitals (patient_id,bp,pulse,temperature,oxygen,recorded_by,recorded_at) VALUES (%s,'140/90','80','99.1','97','Nurse Rani','2025-04-20 10:00')",(pid8,))

# Scans
cursor.execute("INSERT INTO scans (patient_id,scan_type,scan_result,uploaded_by,uploaded_at) VALUES (%s,'X-Ray','No abnormalities found','Dr. Kumar','2025-04-15')",(pid7,))
cursor.execute("INSERT INTO scans (patient_id,scan_type,scan_result,uploaded_by,uploaded_at) VALUES (%s,'Blood Test','HbA1c: 8.2 Elevated','Dr. Priya','2025-04-16')",(pid8,))

# Prescriptions
cursor.execute("INSERT INTO prescriptions (patient_id,medicine,dosage,duration,notes,prescribed_by,prescribed_at) VALUES (%s,'Paracetamol','500mg','5 days','Take after food','Dr. Kumar','2025-04-15')",(pid7,))
cursor.execute("INSERT INTO prescriptions (patient_id,medicine,dosage,duration,notes,prescribed_by,prescribed_at) VALUES (%s,'Insulin','10 units','Ongoing','Before breakfast','Dr. Priya','2025-04-16')",(pid8,))

# Billing
cursor.execute("INSERT INTO billing (patient_id,description,amount,date,added_by) VALUES (%s,'Consultation Fee',500,'2025-04-10','Receptionist Ravi')",(pid7,))
cursor.execute("INSERT INTO billing (patient_id,description,amount,date,added_by) VALUES (%s,'Lab Tests',1200,'2025-04-11','Receptionist Ravi')",(pid7,))
cursor.execute("INSERT INTO billing (patient_id,description,amount,date,added_by) VALUES (%s,'Consultation Fee',500,'2025-04-12','Receptionist Ravi')",(pid8,))
cursor.execute("INSERT INTO billing (patient_id,description,amount,date,added_by) VALUES (%s,'Insulin Supply',800,'2025-04-13','Receptionist Ravi')",(pid8,))
cursor.execute("INSERT INTO billing (patient_id,description,amount,date,added_by) VALUES (%s,'X-Ray',900,'2025-04-15','Receptionist Ravi')",(pid9,))

conn.commit()
conn.close()
print("✅ Database created successfully!")