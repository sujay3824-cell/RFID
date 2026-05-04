import os
from flask import Flask, render_template, request, redirect, jsonify, session
import psycopg2
import psycopg2.extras
from datetime import datetime
 
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'hospital_secret_key')
 
latest_data = {}
 
DATABASE_URL = os.environ.get('DATABASE_URL')
 
def get_db():
    conn = psycopg2.connect(
        host="aws-1-ap-southeast-2.pooler.supabase.com",
        port=6543,
        database="postgres",
        user="postgres.bunmjlewgbizarjcjhvv",
        password=os.environ.get('DB_PASSWORD')
    )
    return conn
def format_name(username):
    return username.replace('.', ' ').title()
# ── LOGIN ─────────────────────────────────────────────────────
@app.route('/')
def home():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    if username == 'kiosk' and password == 'hospital2025':
        session['kiosk'] = True
        return redirect('/mode')
    return render_template('login.html', error="Invalid credentials. Please try again.")

# ── MODE ──────────────────────────────────────────────────────
@app.route('/mode')
def mode():
    if not session.get('kiosk'):
        return redirect('/')
    return render_template('mode_select.html')

# ── AUTO SCAN ─────────────────────────────────────────────────
@app.route('/auto')
def auto():
    if not session.get('kiosk'):
        return redirect('/')
    return render_template('auto_scan.html')

@app.route('/rfid_auto', methods=['POST'])
def rfid_auto():
    rfid = request.json.get('rfid')
    conn = get_db()
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM users WHERE rfid=%s", (rfid,))
    user = cur.fetchone()
    conn.close()
    if user:
        session['user_id']        = user['id']
        session['username']       = user['username']
        session['display_name']   = format_name(user['username'])
        session['role']           = user['role']
        session['staff_type']     = user['staff_type']
        session['specialization'] = user['specialization']
        return jsonify({
            "status":       "ok",
            "display_name": format_name(user['username']),
            "role":         user['role'],
            "staff_type":   user['staff_type'],
            "redirect":     get_redirect(user['role'], user['staff_type'])
        })
    return jsonify({"status": "not found"})

# ── MANUAL ────────────────────────────────────────────────────
@app.route('/manual')
def manual():
    if not session.get('kiosk'):
        return redirect('/')
    return render_template('manual_select.html')

@app.route('/manual_login', methods=['POST'])
def manual_login():
    data          = request.json
    user_input    = data.get('id', '').strip()
    selected_role = data.get('role', '')
    conn = get_db()
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        user_id_int = int(user_input)
        cur.execute("SELECT * FROM users WHERE username=%s OR id=%s", (user_input, user_id_int))
    except ValueError:
        cur.execute("SELECT * FROM users WHERE username=%s", (user_input,))
    user = cur.fetchone()
    conn.close()
    if not user:
        return jsonify({"status": "not found"})
    role_match = False
    if selected_role == 'admin'        and user['role'] == 'admin':   role_match = True
    if selected_role == 'patient'      and user['role'] == 'patient': role_match = True
    if selected_role == 'doctor'       and user['role'] == 'doctor':  role_match = True
    if selected_role in ['nurse','pharmacist','receptionist'] and user['role'] == 'staff':
        if user['staff_type'].lower() == selected_role: role_match = True
    if not role_match:
        return jsonify({"status": "role mismatch"})
    session['user_id']        = user['id']
    session['username']       = user['username']
    session['display_name']   = format_name(user['username'])
    session['role']           = user['role']
    session['staff_type']     = user['staff_type']
    session['specialization'] = user['specialization']
    return jsonify({"status": "ok", "redirect": get_redirect(user['role'], user['staff_type'])})

def get_redirect(role, staff_type):
    if role == 'admin':   return '/dashboard/admin'
    if role == 'doctor':  return '/dashboard/doctor'
    if role == 'patient': return '/dashboard/patient'
    if role == 'staff':
        if staff_type == 'Pharmacist':   return '/dashboard/pharmacist'
        if staff_type == 'Receptionist': return '/dashboard/receptionist'
        if staff_type == 'Nurse':        return '/dashboard/staff'
    return '/mode'

def check_session():
    return 'user_id' in session



# ── DOCTOR DASHBOARD ──────────────────────────────────────────
@app.route('/dashboard/doctor')
def dash_doctor():
    if not check_session() or session.get('role') != 'doctor':
        return redirect('/mode')
    conn    = get_db()
    cur     = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    user_id = session['user_id']
    data    = {}
    cur.execute("SELECT * FROM appointments WHERE doctor_id=%s ORDER BY date", (user_id,))
    data['appointments'] = cur.fetchall()
    name_part = session['username'].replace('dr.','').replace('dr ','').replace('.','').strip().title()
    cur.execute("SELECT * FROM patients WHERE doctor ILIKE %s", ('%' + name_part + '%',))
    data['patients'] = cur.fetchall()
    conn.close()
    return render_template('dashboard_doctor.html',
        display_name=session.get('display_name'),
        specialization=session.get('specialization'), data=data)

# ── STAFF / NURSE DASHBOARD ───────────────────────────────────
@app.route('/dashboard/staff')
def dash_staff():
    if not check_session() or session.get('role') != 'staff':
        return redirect('/mode')
    conn = get_db()
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    data = {}
    cur.execute("SELECT * FROM patients ORDER BY admitted_date DESC")
    data['patients'] = cur.fetchall()
    conn.close()
    return render_template('dashboard_staff.html',
        display_name=session.get('display_name'),
        staff_type=session.get('staff_type'),
        specialization=session.get('specialization'), data=data)

# ── PHARMACIST DASHBOARD ──────────────────────────────────────
@app.route('/dashboard/pharmacist')
def dash_pharmacist():
    if not check_session() or session.get('staff_type') != 'Pharmacist':
        return redirect('/mode')
    conn = get_db()
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    data = {}
    cur.execute("SELECT * FROM patients ORDER BY name")
    data['patients'] = cur.fetchall()
    conn.close()
    return render_template('dashboard_pharmacist.html',
        display_name=session.get('display_name'),
        specialization=session.get('specialization'), data=data)

# ── RECEPTIONIST DASHBOARD ────────────────────────────────────
@app.route('/dashboard/receptionist')
def dash_receptionist():
    if not check_session() or session.get('staff_type') != 'Receptionist':
        return redirect('/mode')
    conn = get_db()
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    data = {}
    cur.execute("SELECT * FROM users ORDER BY role")
    data['users'] = cur.fetchall()
    cur.execute("SELECT * FROM patients ORDER BY admitted_date DESC")
    data['patients'] = cur.fetchall()
    cur.execute("SELECT * FROM billing ORDER BY date DESC")
    data['billing'] = cur.fetchall()
    conn.close()
    return render_template('dashboard_receptionist.html',
        display_name=session.get('display_name'),
        specialization=session.get('specialization'), data=data)

# ── PATIENT DASHBOARD ─────────────────────────────────────────
@app.route('/dashboard/patient')
def dash_patient():
    if not check_session() or session.get('role') != 'patient':
        return redirect('/mode')
    conn    = get_db()
    cur     = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    user_id = session['user_id']
    data    = {}
    cur.execute("SELECT * FROM patients WHERE id=%s",              (user_id,)); data['patient']       = cur.fetchone()
    cur.execute("SELECT * FROM scans WHERE patient_id=%s",         (user_id,)); data['scans']         = cur.fetchall()
    cur.execute("SELECT * FROM prescriptions WHERE patient_id=%s", (user_id,)); data['prescriptions'] = cur.fetchall()
    cur.execute("SELECT * FROM vitals WHERE patient_id=%s ORDER BY id DESC", (user_id,)); data['vitals'] = cur.fetchall()
    cur.execute("SELECT * FROM billing WHERE patient_id=%s",       (user_id,)); data['billing']       = cur.fetchall()
    conn.close()
    return render_template('dashboard_patient.html',
        display_name=session.get('display_name'), data=data)

# ── LOGOUT ────────────────────────────────────────────────────
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# ── ESP32 RFID ────────────────────────────────────────────────
@app.route('/scan', methods=['POST'])
def scan():

    global latest_data

    rfid = request.json['rfid']

    # CLEAR DASHBOARD
    if rfid == "CLEAR":
        latest_data = {}
        return jsonify({"status": "cleared"})

    conn = get_db()

    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cur.execute("SELECT * FROM patients WHERE rfid=%s", (rfid,))
    patient = cur.fetchone()

    cur.execute("SELECT * FROM users WHERE rfid=%s", (rfid,))
    user = cur.fetchone()

    conn.close()

    latest_data = {}

    if patient:

        latest_data = {
            "name": patient['name'],
            "disease": patient['disease'],
            "history": patient['history'],
            "medication": patient['medication']
        }

    if user:
        latest_data['rfid'] = rfid

    return jsonify({"status": "ok"})

# ── MANUAL SEARCH ─────────────────────────────────────────────
@app.route('/manual_search', methods=['POST'])
def manual_search():
    value = request.json['id']
    conn  = get_db()
    cur   = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        value_int = int(value)
        cur.execute("SELECT * FROM patients WHERE rfid=%s OR id=%s", (value, value_int))
    except ValueError:
        cur.execute("SELECT * FROM patients WHERE rfid=%s", (value,))
    patient = cur.fetchone()
    if patient:
        cur.execute("SELECT * FROM vitals WHERE patient_id=%s ORDER BY id DESC LIMIT 1", (patient['id'],))
        vitals = cur.fetchone()
        cur.execute("SELECT * FROM scans WHERE patient_id=%s ORDER BY id DESC", (patient['id'],))
        scans = cur.fetchall()
        cur.execute("SELECT * FROM prescriptions WHERE patient_id=%s ORDER BY id DESC", (patient['id'],))
        prescriptions = cur.fetchall()
        conn.close()
        return jsonify({
            "id": patient['id'], "name": patient['name'],
            "disease": patient['disease'], "history": patient['history'],
            "ward": patient['ward'], "doctor": patient['doctor'],
            "medication": patient['medication'], "admitted_date": patient['admitted_date'],
            "status": patient['status'],
            "vitals":        dict(vitals) if vitals else None,
            "scans":         [dict(s) for s in scans],
            "prescriptions": [dict(p) for p in prescriptions]
        })
    conn.close()
    return jsonify({"error": "not found"})

# ── ADD STAFF ─────────────────────────────────────────────────
@app.route('/add_staff', methods=['POST'])
def add_staff():
    d = request.json
    conn = get_db(); cur = conn.cursor()
    cur.execute("INSERT INTO users (username,password,role,staff_type,specialization,rfid) VALUES (%s,%s,%s,%s,%s,%s)",
        (d['username'], d['password'], d['role'], d['staff_type'], d['specialization'], d['rfid']))
    conn.commit(); conn.close()
    return jsonify({"status": "Staff added"})

# ── REMOVE STAFF ──────────────────────────────────────────────
@app.route('/remove_staff', methods=['POST'])
def remove_staff():
    d = request.json
    conn = get_db(); cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE id=%s AND role != 'admin'", (d['user_id'],))
    conn.commit(); conn.close()
    return jsonify({"status": "Removed"})

# ── ADD PATIENT (Receptionist) ────────────────────────────────
@app.route('/add_patient', methods=['POST'])
def add_patient():
    d = request.json
    conn = get_db(); cur = conn.cursor()
    cur.execute("INSERT INTO users (username,password,role,staff_type,specialization,rfid) VALUES (%s,%s,%s,%s,%s,%s) RETURNING id",
        (d['username'], d['password'], 'patient', 'Patient', 'N/A', d['rfid']))
    user_id = cur.fetchone()[0]
    cur.execute("INSERT INTO patients VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
        (user_id, d['name'], d['rfid'], d['disease'], '', d['ward'],
         d['medication'], d['doctor'], d['admitted_date'], '', '', 'admitted'))
    conn.commit(); conn.close()
    return jsonify({"status": "Patient added"})

# ── DISCHARGE PATIENT (Receptionist) ─────────────────────────
@app.route('/discharge_patient', methods=['POST'])
def discharge_patient():
    d = request.json
    conn = get_db(); cur = conn.cursor()
    cur.execute("UPDATE patients SET discharge_date=%s, status='discharged' WHERE id=%s",
        (d['date'], d['patient_id']))
    conn.commit(); conn.close()
    return jsonify({"status": "Discharged"})

# ── ADD VITALS (Nurse) ────────────────────────────────────────
@app.route('/add_vitals', methods=['POST'])
def add_vitals():
    d = request.json
    conn = get_db(); cur = conn.cursor()
    cur.execute("INSERT INTO vitals (patient_id,bp,pulse,temperature,oxygen,recorded_by,recorded_at) VALUES (%s,%s,%s,%s,%s,%s,%s)",
        (d['patient_id'], d['bp'], d['pulse'], d['temperature'], d['oxygen'],
         session.get('display_name'), datetime.now().strftime('%Y-%m-%d %H:%M')))
    conn.commit(); conn.close()
    return jsonify({"status": "Vitals saved"})

# ── ADD SCAN ──────────────────────────────────────────────────
@app.route('/add_scan', methods=['POST'])
def add_scan():
    d = request.json
    conn = get_db(); cur = conn.cursor()
    cur.execute("INSERT INTO scans (patient_id,scan_type,scan_result,uploaded_by,uploaded_at) VALUES (%s,%s,%s,%s,%s)",
        (d['patient_id'], d['scan_type'], d['scan_result'],
         session.get('display_name'), datetime.now().strftime('%Y-%m-%d')))
    conn.commit(); conn.close()
    return jsonify({"status": "Scan saved"})

# ── ADD PRESCRIPTION (Doctor) ─────────────────────────────────
@app.route('/add_prescription', methods=['POST'])
def add_prescription():
    d = request.json
    conn = get_db(); cur = conn.cursor()
    cur.execute("INSERT INTO prescriptions (patient_id,medicine,dosage,duration,notes,prescribed_by,prescribed_at) VALUES (%s,%s,%s,%s,%s,%s,%s)",
        (d['patient_id'], d['medicine'], d['dosage'], d['duration'], d['notes'],
         session.get('display_name'), datetime.now().strftime('%Y-%m-%d')))
    cur.execute("UPDATE patients SET medication=%s WHERE id=%s",
        (d['medicine'] + ' ' + d['dosage'], d['patient_id']))
    conn.commit(); conn.close()
    return jsonify({"status": "Prescription saved"})

# ── UPDATE MEDICATION (Doctor / Nurse) ───────────────────────
@app.route('/update_medication', methods=['POST'])
def update_medication():
    d = request.json
    conn = get_db(); cur = conn.cursor()
    cur.execute("UPDATE patients SET medication=%s WHERE id=%s", (d['medication'], d['patient_id']))
    conn.commit(); conn.close()
    return jsonify({"status": "Medication updated"})

# ── ADD BILLING (Receptionist) ────────────────────────────────
@app.route('/add_billing', methods=['POST'])
def add_billing():
    d = request.json
    conn = get_db(); cur = conn.cursor()
    cur.execute("INSERT INTO billing (patient_id,description,amount,date,added_by) VALUES (%s,%s,%s,%s,%s)",
        (d['patient_id'], d['description'], d['amount'],
         datetime.now().strftime('%Y-%m-%d'), session.get('display_name', 'Receptionist')))
    conn.commit(); conn.close()
    return jsonify({"status": "Bill added"})
# ── ADD APPOINTMENT (Receptionist / Nurse) ────────────────────
@app.route('/add_appointment', methods=['POST'])
def add_appointment():
    d = request.json
    conn = get_db(); cur = conn.cursor()
    cur.execute(
        "INSERT INTO appointments (doctor_id, patient_name, date, type) VALUES (%s,%s,%s,%s)",
        (d['doctor_id'], d['patient_name'], d['date'], d['type'])
    )
    conn.commit(); conn.close()
    return jsonify({"status": "Appointment added"})

# ── GET ALL DOCTORS (for appointment form dropdown) ───────────
@app.route('/get_doctors')
def get_doctors():
    conn = get_db(); cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT id, username, specialization FROM users WHERE role='doctor' ORDER BY username")
    doctors = cur.fetchall()
    conn.close()
    return jsonify({"doctors": [dict(d) for d in doctors]})

# ── GET ALL PATIENTS (for appointment form dropdown) ──────────
@app.route('/get_patients')
def get_patients():
    conn = get_db(); cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT id, name FROM patients WHERE status='admitted' ORDER BY name")
    patients = cur.fetchall()
    conn.close()
    return jsonify({"patients": [dict(p) for p in patients]})
if __name__ == '__main__':
    app.run(debug=False)