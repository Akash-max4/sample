from flask import Flask, request, jsonify
import pyodbc
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app)

# ---------------- DB CONNECTION FUNCTION ----------------
# Instead of one global connection, create fresh connection per route
def get_conn():
    return pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};'
        'SERVER=localhost;'
        'DATABASE=student_database;'
        'Trusted_Connection=yes;'
    )

# ---------------- COMMON FUNCTION ----------------
def format_dob(dob):
    try:
        if isinstance(dob, str):
            dob = datetime.strptime(dob, "%Y-%m-%d")
        return dob.strftime("%d-%m-%Y")
    except:
        return str(dob)


# ---------------- INSERT ----------------
@app.route('/insert', methods=['POST'])
def insert_student():
    try:
        data = request.json
        course_id  = data['course_id']
        college_id = data['college_id']
        conn = get_conn()
        cur  = conn.cursor()
        cur.execute("SELECT 1 FROM course WHERE course_id = ?", (course_id,))
        if not cur.fetchone():
            return jsonify({"error": "Invalid Course ID"})
        cur.execute("SELECT 1 FROM college WHERE college_id = ?", (college_id,))
        if not cur.fetchone():
            return jsonify({"error": "Invalid College ID"})
        cur.execute("""
            INSERT INTO student (Name, phone_no, Email_id, password, DOB, Address, Father_name, Mother_name, course_id, college_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (data['Name'], data['phone_no'], data['Email_id'], data['password'],
              data['DOB'], data['Address'], data['Father_name'], data['Mother_name'], course_id, college_id))
        conn.commit()
        cur.execute("SELECT @@IDENTITY")
        new_id = cur.fetchone()[0]
        cur.execute("""
            SELECT Student_id, Name, phone_no, Email_id, DOB, Address, Father_name, Mother_name, course_id, college_id
            FROM student WHERE Student_id = ?
        """, (new_id,))
        result = cur.fetchone()
        conn.close()
        return jsonify({"message": f"Student ID {new_id} inserted successfully", "data": {
            "ID": result[0], "Name": result[1], "Phone": result[2], "Email": result[3],
            "DOB": format_dob(result[4]), "Address": result[5], "Father Name": result[6],
            "Mother Name": result[7], "Course ID": result[8], "College ID": result[9]
        }})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------- SEARCH ----------------
@app.route('/search/<int:student_id>', methods=['GET'])
def search_student(student_id):
    try:
        conn = get_conn()
        cur  = conn.cursor()
        cur.execute("""
            SELECT Student_id, Name, phone_no, Email_id, DOB, Address, Father_name, Mother_name, course_id, college_id
            FROM student WHERE Student_id = ?
        """, (student_id,))
        result = cur.fetchone()
        conn.close()
        if result:
            return jsonify({"ID": result[0], "Name": result[1], "Phone": result[2], "Email": result[3],
                "DOB": format_dob(result[4]), "Address": result[5], "Father Name": result[6],
                "Mother Name": result[7], "Course ID": result[8], "College ID": result[9]})
        return jsonify({"error": "No record found"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------- UPDATE ----------------
@app.route('/update/<int:student_id>', methods=['PUT'])
def update_student(student_id):
    try:
        data = request.json
        allowed_columns = ["Name", "phone_no", "Email_id", "Address", "Father_name", "Mother_name", "course_id", "college_id"]
        column = data['column']
        value  = data['value']
        if column not in allowed_columns:
            return jsonify({"error": "Invalid column name"})
        conn = get_conn()
        cur  = conn.cursor()
        cur.execute(f"UPDATE student SET {column} = ? WHERE Student_id = ?", (value, student_id))
        conn.commit()
        conn.close()
        return jsonify({"message": f"Student ID {student_id} updated successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------- DELETE ----------------
@app.route('/delete/<int:student_id>', methods=['DELETE'])
def delete_student(student_id):
    try:
        conn = get_conn()
        cur  = conn.cursor()
        cur.execute("DELETE FROM student WHERE Student_id = ?", (student_id,))
        conn.commit()
        conn.close()
        return jsonify({"message": f"Student ID {student_id} deleted successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------- REGISTRATION ----------------
@app.route('/register', methods=['PUT'])
def register():
    try:
        data     = request.json
        email    = data['email']
        password = data['password']
        conn = get_conn()
        cur  = conn.cursor()
        cur.execute("SELECT * FROM student WHERE Email_id = ?", email)
        if not cur.fetchone():
            conn.close()
            return jsonify({"message": "Email not found"}), 404
        cur.execute("UPDATE student SET password=? WHERE Email_id=?", password, email)
        conn.commit()
        conn.close()
        return jsonify({"message": "Registered successfully"})
    except Exception as e:
        return jsonify({"message": str(e)}), 500


# ---------------- STUDENT LOGIN ----------------
@app.route('/login', methods=['POST'])
def login():
    try:
        data     = request.json
        email    = data['email']
        password = data['password']
        conn = get_conn()
        cur  = conn.cursor()
        cur.execute("SELECT * FROM student WHERE Email_id=? AND password=?", email, password)
        user = cur.fetchone()
        conn.close()
        if user:
            return jsonify({"message": "Login success"})
        return jsonify({"message": "Invalid credentials"}), 401
    except Exception as e:
        return jsonify({"message": str(e)}), 500


# ================================================================
#                  TEACHER ROUTES
# ================================================================

# ---------------- TEACHER LOGIN ----------------
@app.route('/teacher/login', methods=['POST'])
def teacher_login():
    try:
        data     = request.json
        email    = data['email']
        password = data['password']
        conn = get_conn()
        cur  = conn.cursor()
        cur.execute("""
            SELECT teacher_id, name, email, college_id, subject_id
            FROM teacher WHERE email = ? AND password = ?
        """, (email, password))
        teacher = cur.fetchone()
        conn.close()
        if teacher:
            return jsonify({
                "message":    "Login success",
                "teacher_id": teacher[0],
                "name":       teacher[1],
                "email":      teacher[2],
                "college_id": teacher[3],
                "subject_id": teacher[4]
            })
        return jsonify({"message": "Invalid credentials"}), 401
    except Exception as e:
        return jsonify({"message": str(e)}), 500


# ---------------- TEACHER OVERVIEW ----------------
@app.route('/teacher/overview/<int:teacher_id>', methods=['GET'])
def teacher_overview(teacher_id):
    try:
        conn = get_conn()
        cur  = conn.cursor()

        cur.execute("SELECT subject_id FROM teacher WHERE teacher_id = ?", (teacher_id,))
        teacher = cur.fetchone()
        if not teacher:
            conn.close()
            return jsonify({"error": "Teacher not found"}), 404
        subject_id = teacher[0]

        cur.execute("SELECT course_id FROM subject WHERE subject_id = ?", (subject_id,))
        course_id = cur.fetchone()[0]

        cur.execute("""
            SELECT COUNT(DISTINCT m.student_id) FROM marks m
            JOIN student s ON m.student_id = s.Student_id
            WHERE m.subject_id = ? AND s.course_id = ?
        """, (subject_id, course_id))
        total_students = cur.fetchone()[0] or 0

        cur.execute("""
            SELECT AVG(CAST(m.marks_obtained AS FLOAT)) FROM marks m
            JOIN student s ON m.student_id = s.Student_id
            WHERE m.subject_id = ? AND s.course_id = ?
        """, (subject_id, course_id))
        avg_marks = round(cur.fetchone()[0] or 0, 2)

        cur.execute("""
            SELECT AVG(CAST(a.Attendance AS FLOAT)) * 100 FROM attendance a
            JOIN student s ON a.student_id = s.Student_id
            WHERE a.subject_id = ? AND s.course_id = ?
        """, (subject_id, course_id))
        avg_attendance = round(cur.fetchone()[0] or 0, 2)

        cur.execute("""
            SELECT COUNT(*) FROM marks m
            JOIN subject sub ON m.subject_id = sub.subject_id
            JOIN student s ON m.student_id = s.Student_id
            WHERE m.subject_id = ? AND s.course_id = ?
            AND m.marks_obtained >= sub.max_marks * 0.4
        """, (subject_id, course_id))
        passed = cur.fetchone()[0] or 0

        cur.execute("""
            SELECT COUNT(*) FROM marks m
            JOIN subject sub ON m.subject_id = sub.subject_id
            JOIN student s ON m.student_id = s.Student_id
            WHERE m.subject_id = ? AND s.course_id = ?
            AND m.marks_obtained < sub.max_marks * 0.4
        """, (subject_id, course_id))
        failed = cur.fetchone()[0] or 0

        cur.execute("SELECT subject_name, max_marks FROM subject WHERE subject_id = ?", (subject_id,))
        sub = cur.fetchone()

        conn.close()
        return jsonify({
            "subject_name":   sub[0] if sub else "",
            "max_marks":      sub[1] if sub else 0,
            "total_students": total_students,
            "avg_marks":      avg_marks,
            "avg_attendance": avg_attendance,
            "passed":         passed,
            "failed":         failed
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------- TEACHER - GET STUDENTS ----------------
@app.route('/teacher/students/<int:teacher_id>', methods=['GET'])
def teacher_students(teacher_id):
    try:
        conn = get_conn()
        cur  = conn.cursor()

        cur.execute("SELECT subject_id FROM teacher WHERE teacher_id = ?", (teacher_id,))
        teacher = cur.fetchone()
        if not teacher:
            conn.close()
            return jsonify({"error": "Teacher not found"}), 404
        subject_id = teacher[0]

        cur.execute("SELECT course_id FROM subject WHERE subject_id = ?", (subject_id,))
        subject = cur.fetchone()
        if not subject:
            conn.close()
            return jsonify({"error": "Subject not found"}), 404
        course_id = subject[0]

        cur.execute("""
            SELECT s.Student_id, s.Name, c.course_name, s.phone_no, s.Email_id, col.college_name
            FROM student s
            JOIN course c ON s.course_id = c.course_id
            JOIN college col ON s.college_id = col.college_id
            WHERE s.course_id = ?
            ORDER BY s.Name
        """, (course_id,))
        rows = cur.fetchall()
        conn.close()
        return jsonify({"students": [
            {"student_id": r[0], "name": r[1], "course_name": r[2],
             "phone": r[3], "email": r[4], "college_name": r[5]}
            for r in rows
        ]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    #----------------add student---------
@app.route('/teacher/form-data', methods=['GET'])
def get_form_data():
    try:
        conn = get_conn()
        cur  = conn.cursor()

        cur.execute("SELECT course_id, course_name FROM course")
        courses = [{"course_id": r[0], "course_name": r[1]} for r in cur.fetchall()]

        cur.execute("SELECT college_id, college_name FROM college")
        colleges = [{"college_id": r[0], "college_name": r[1]} for r in cur.fetchall()]

        conn.close()
        return jsonify({"courses": courses, "colleges": colleges})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/teacher/add-student', methods=['POST'])
def teacher_add_student():
    try:
        data = request.json
        conn = get_conn()
        cur  = conn.cursor()

        # validate course and college
        cur.execute("SELECT 1 FROM course WHERE course_id = ?", (data['course_id'],))
        if not cur.fetchone():
            conn.close()
            return jsonify({"error": "Invalid Course ID"}), 400

        cur.execute("SELECT 1 FROM college WHERE college_id = ?", (data['college_id'],))
        if not cur.fetchone():
            conn.close()
            return jsonify({"error": "Invalid College ID"}), 400

        cur.execute("""
            INSERT INTO student
            (Name, phone_no, Email_id, password, DOB, Address, Father_name, Mother_name, course_id, college_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data['name'], data['phone'], data['email'], None,
            data['dob'], data['address'], data['father'], data['mother'],
            int(data['course_id']), int(data['college_id'])
        ))
        conn.commit()

        cur.execute("SELECT @@IDENTITY")
        new_id = cur.fetchone()[0]
        conn.close()

        return jsonify({"message": f"Student added successfully with ID {new_id}"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------- TEACHER - SAVE ATTENDANCE ----------------
@app.route('/teacher/attendance/save', methods=['POST'])
def save_attendance():
    try:
        data       = request.json
        subject_id = int(data['subject_id'])
        records    = data['records']
        conn = get_conn()
        cur  = conn.cursor()

        for rec in records:
            student_id = int(rec['student_id'])
            attendance = int(rec['attendance'])

            # get next attendance_id manually
            cur.execute("SELECT ISNULL(MAX(attendance_id), 0) + 1 FROM attendance")
            next_id = cur.fetchone()[0]

            cur.execute("""
                INSERT INTO attendance (attendance_id, student_id, subject_id, Attendance)
                VALUES (?, ?, ?, ?)
            """, (next_id, student_id, subject_id, attendance))

        conn.commit()
        conn.close()
        return jsonify({"message": f"Attendance saved for {len(records)} students"})

    except Exception as e:
        print("ERROR:", e)
        return jsonify({"error": str(e)}), 500


# ---------------- TEACHER - SAVE MARKS ----------------
@app.route('/teacher/marks/save', methods=['POST'])
def save_marks():
    try:
        data       = request.json
        subject_id = int(data['subject_id'])
        records    = data['records']
        conn = get_conn()
        cur  = conn.cursor()

        for rec in records:
            student_id = int(rec['student_id'])
            marks      = int(rec['marks'])

            cur.execute("""
                SELECT marks_id FROM marks
                WHERE student_id = ? AND subject_id = ?
            """, (student_id, subject_id))
            existing = cur.fetchone()

            if existing:
                cur.execute("""
                    UPDATE marks SET marks_obtained = ?
                    WHERE student_id = ? AND subject_id = ?
                """, (marks, student_id, subject_id))
            else:
                cur.execute("SELECT ISNULL(MAX(marks_id), 0) + 1 FROM marks")
                next_id = cur.fetchone()[0]
                cur.execute("""
                    INSERT INTO marks (marks_id, student_id, subject_id, marks_obtained)
                    VALUES (?, ?, ?, ?)
                """, (next_id, student_id, subject_id, marks))

        conn.commit()
        conn.close()
        return jsonify({"message": f"Marks saved for {len(records)} students"})
    except Exception as e:
        print("ERROR:", e)
        return jsonify({"error": str(e)}), 500


# ---------------- TEACHER - ATTENDANCE REPORT ----------------
@app.route('/teacher/attendance/report/<int:teacher_id>', methods=['GET'])
def teacher_attendance_report(teacher_id):
    try:
        conn = get_conn()
        cur  = conn.cursor()

        cur.execute("SELECT subject_id FROM teacher WHERE teacher_id = ?", (teacher_id,))
        teacher = cur.fetchone()
        if not teacher:
            conn.close()
            return jsonify({"error": "Teacher not found"}), 404
        subject_id = teacher[0]

        cur.execute("SELECT course_id FROM subject WHERE subject_id = ?", (subject_id,))
        course_id = cur.fetchone()[0]

        cur.execute("""
            SELECT s.Student_id, s.Name,
                   SUM(CASE WHEN a.Attendance = 1 THEN 1 ELSE 0 END) as present,
                   COUNT(*) as total
            FROM student s
            JOIN attendance a ON s.Student_id = a.student_id
            WHERE a.subject_id = ? AND s.course_id = ?
            GROUP BY s.Student_id, s.Name
            ORDER BY s.Name
        """, (subject_id, course_id))
        rows = cur.fetchall()
        conn.close()

        report = []
        for row in rows:
            pct = round((row[2] * 100.0 / row[3]), 2) if row[3] > 0 else 0
            report.append({
                "student_id": row[0], "name": row[1],
                "present": row[2], "total": row[3],
                "percentage": pct,
                "status": "Good" if pct >= 75 else "Low"
            })
        return jsonify({"report": report})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------- TEACHER - MARKS REPORT ----------------
@app.route('/teacher/marks/report/<int:teacher_id>', methods=['GET'])
def teacher_marks_report(teacher_id):
    try:
        conn = get_conn()
        cur  = conn.cursor()

        cur.execute("SELECT subject_id FROM teacher WHERE teacher_id = ?", (teacher_id,))
        teacher = cur.fetchone()
        if not teacher:
            conn.close()
            return jsonify({"error": "Teacher not found"}), 404
        subject_id = teacher[0]

        cur.execute("SELECT course_id FROM subject WHERE subject_id = ?", (subject_id,))
        course_id = cur.fetchone()[0]

        cur.execute("""
            SELECT s.Student_id, s.Name, m.marks_obtained, sub.max_marks
            FROM marks m
            JOIN student s ON m.student_id = s.Student_id
            JOIN subject sub ON m.subject_id = sub.subject_id
            WHERE m.subject_id = ? AND s.course_id = ?
            ORDER BY m.marks_obtained DESC
        """, (subject_id, course_id))
        rows = cur.fetchall()
        conn.close()

        def get_grade(pct):
            if pct >= 90: return "A+"
            if pct >= 80: return "A"
            if pct >= 70: return "B+"
            if pct >= 60: return "B"
            if pct >= 50: return "C"
            if pct >= 40: return "D"
            return "F"

        report = []
        for row in rows:
            pct = round((row[2] / row[3]) * 100, 2) if row[3] else 0
            report.append({
                "student_id": row[0], "name": row[1],
                "marks_obtained": row[2], "max_marks": row[3],
                "percentage": pct, "grade": get_grade(pct),
                "status": "Pass" if row[2] >= round(row[3] * 0.4) else "Fail"
            })

        avg     = round(sum(r["marks_obtained"] for r in report) / len(report), 2) if report else 0
        highest = max(report, key=lambda x: x["marks_obtained"]) if report else {}
        lowest  = min(report, key=lambda x: x["marks_obtained"]) if report else {}

        return jsonify({
            "report": report, "class_avg": avg,
            "highest_marks": highest.get("marks_obtained", 0),
            "highest_student": highest.get("name", ""),
            "lowest_marks": lowest.get("marks_obtained", 0),
            "lowest_student": lowest.get("name", "")
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------- TEACHER - RESULTS ----------------
@app.route('/teacher/results/<int:teacher_id>', methods=['GET'])
def teacher_results(teacher_id):
    try:
        conn = get_conn()
        cur  = conn.cursor()

        cur.execute("SELECT subject_id FROM teacher WHERE teacher_id = ?", (teacher_id,))
        teacher = cur.fetchone()
        if not teacher:
            conn.close()
            return jsonify({"error": "Teacher not found"}), 404
        subject_id = teacher[0]

        cur.execute("SELECT course_id FROM subject WHERE subject_id = ?", (subject_id,))
        course_id = cur.fetchone()[0]

        cur.execute("""
            SELECT s.Student_id, s.Name, m.marks_obtained, sub.max_marks, c.course_name
            FROM marks m
            JOIN student s ON m.student_id = s.Student_id
            JOIN subject sub ON m.subject_id = sub.subject_id
            JOIN course c ON s.course_id = c.course_id
            WHERE m.subject_id = ? AND s.course_id = ?
            ORDER BY s.Name
        """, (subject_id, course_id))
        rows = cur.fetchall()
        conn.close()

        results = []
        passed = 0
        failed = 0
        for row in rows:
            pass_mark = round(row[3] * 0.4)
            is_pass   = row[2] >= pass_mark
            if is_pass: passed += 1
            else:       failed += 1
            results.append({
                "student_id": row[0], "name": row[1],
                "marks_obtained": row[2], "max_marks": row[3],
                "course_name": row[4],
                "status": "Pass" if is_pass else "Fail"
            })
        return jsonify({"results": results, "passed": passed, "failed": failed, "total": len(results)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ================================================================
#              EXISTING STUDENT ROUTES
# ================================================================

@app.route('/overview/<email>', methods=['GET'])
def overview(email):
    try:
        conn = get_conn()
        cur  = conn.cursor()

        cur.execute("SELECT student_id, course_id FROM student WHERE Email_id = ?", (email,))
        student = cur.fetchone()
        if not student:
            conn.close()
            return jsonify({"error": "Student not found"}), 404
        student_id = student[0]
        course_id  = student[1]

        cur.execute("""
            SELECT CASE WHEN COUNT(*) = 0 THEN 0
            ELSE (SUM(CASE WHEN Attendance = 1 THEN 1 ELSE 0 END) * 100.0) / COUNT(*) END
            FROM attendance WHERE student_id = ?
        """, (student_id,))
        attendance = cur.fetchone()[0] or 0

        cur.execute("SELECT AVG(marks_obtained) FROM marks WHERE student_id = ?", (student_id,))
        avg_marks = cur.fetchone()[0] or 0

        cur.execute("""
            SELECT m.student_id, RANK() OVER (ORDER BY AVG(m.marks_obtained) DESC) AS rank
            FROM marks m JOIN student s ON m.student_id = s.student_id
            WHERE s.course_id = ? GROUP BY m.student_id
        """, (course_id,))
        rank = 0
        for r in cur.fetchall():
            if r[0] == student_id:
                rank = r[1]
                break

        cur.execute("""
            SELECT COUNT(*) FROM marks m JOIN subject sub ON m.subject_id = sub.subject_id
            WHERE m.student_id = ? AND m.marks_obtained >= sub.max_marks * 0.4
        """, (student_id,))
        subjects_passed = cur.fetchone()[0] or 0

        conn.close()
        return jsonify({
            "attendance": round(attendance, 2), "avg_marks": round(avg_marks, 2),
            "rank": rank, "subjects_passed": subjects_passed
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/marks-chart/<email>', methods=['GET'])
def marks_chart(email):
    try:
        conn = get_conn()
        cur  = conn.cursor()
        cur.execute("SELECT student_id FROM student WHERE Email_id = ?", (email,))
        student = cur.fetchone()
        if not student:
            conn.close()
            return jsonify({"error": "Student not found"}), 404
        student_id = student[0]
        cur.execute("""
            SELECT sub.subject_name, m.marks_obtained, AVG(m2.marks_obtained) as class_avg
            FROM marks m JOIN subject sub ON m.subject_id = sub.subject_id
            JOIN marks m2 ON m.subject_id = m2.subject_id
            WHERE m.student_id = ? GROUP BY sub.subject_name, m.marks_obtained
        """, (student_id,))
        data = cur.fetchall()
        conn.close()
        subjects = []; student_marks = []; class_avg = []
        for row in data:
            subjects.append(row[0]); student_marks.append(float(row[1])); class_avg.append(float(row[2]))
        return jsonify({"subjects": subjects, "student_marks": student_marks, "class_avg": class_avg})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/achievements/<email>', methods=['GET'])
def achievements(email):
    try:
        conn = get_conn()
        cur  = conn.cursor()

        cur.execute("SELECT student_id, course_id FROM student WHERE Email_id = ?", (email,))
        student = cur.fetchone()
        if not student:
            conn.close()
            return jsonify({"error": "Student not found"}), 404
        student_id = student[0]
        course_id  = student[1]
        ach = []

        cur.execute("SELECT AVG(marks_obtained) FROM marks WHERE student_id = ?", (student_id,))
        my_avg = cur.fetchone()[0] or 0

        cur.execute("SELECT AVG(m.marks_obtained) FROM marks m JOIN student s ON m.student_id = s.student_id WHERE s.course_id = ?", (course_id,))
        class_avg = cur.fetchone()[0] or 0
        if my_avg > class_avg: ach.append("📈 Above Average")

        cur.execute("SELECT CASE WHEN COUNT(*) = 0 THEN 0 ELSE (SUM(CASE WHEN Attendance = 1 THEN 1 ELSE 0 END) * 100.0) / COUNT(*) END FROM attendance WHERE student_id = ?", (student_id,))
        attendance = cur.fetchone()[0] or 0
        if attendance > 75: ach.append("📅 Good Attendance")

        cur.execute("SELECT m.student_id, RANK() OVER (ORDER BY AVG(m.marks_obtained) DESC) AS rank FROM marks m JOIN student s ON m.student_id = s.student_id WHERE s.course_id = ? GROUP BY m.student_id", (course_id,))
        my_rank = 0
        for r in cur.fetchall():
            if r[0] == student_id: my_rank = r[1]; break
        if my_rank <= 5: ach.append("🎯 Top 5 Rank")

        cur.execute("SELECT COUNT(*) FROM marks m WHERE m.student_id = ? AND m.marks_obtained = (SELECT MAX(m2.marks_obtained) FROM marks m2 WHERE m2.subject_id = m.subject_id)", (student_id,))
        if cur.fetchone()[0] > 0: ach.append("🏆 Top Scorer")

        conn.close()
        if not ach: ach.append("No achievements yet 😅")
        return jsonify({"achievements": ach})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/update_profile', methods=['PUT'])
def update_profile():
    try:
        data = request.json
        conn = get_conn()
        cur  = conn.cursor()
        cur.execute("UPDATE student SET Name=?, phone_no=?, Address=?, Father_name=?, Mother_name=? WHERE Email_id=?",
                    (data.get("name"), data.get("phone"), data.get("address"),
                     data.get("father"), data.get("mother"), data.get("email")))
        conn.commit()
        conn.close()
        return jsonify({"message": "Profile updated successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/profile/<email>', methods=['GET'])
def get_profile(email):
    try:
        conn = get_conn()
        cur  = conn.cursor()
        cur.execute("""
            SELECT s.Student_id, s.Name, s.phone_no, s.Email_id, s.Address,
                   s.Father_name, s.Mother_name, c.course_name, col.college_name
            FROM student s JOIN course c ON s.course_id = c.course_id
            JOIN college col ON s.college_id = col.college_id WHERE s.Email_id = ?
        """, (email,))
        data = cur.fetchone()
        conn.close()
        if not data:
            return jsonify({"error": "Student not found"}), 404
        return jsonify({"ID": data[0], "Name": data[1], "Phone": data[2], "Email": data[3],
                        "Address": data[4], "Father Name": data[5], "Mother Name": data[6],
                        "Course": data[7], "College": data[8]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/attendance/<email>', methods=['GET'])
def get_attendance(email):
    try:
        conn = get_conn()
        cur  = conn.cursor()
        cur.execute("SELECT Student_id FROM student WHERE Email_id=?", (email,))
        student = cur.fetchone()
        if not student:
            conn.close()
            return jsonify({"error": "Student not found"}), 404
        student_id = student[0]
        cur.execute("""
            SELECT sub.subject_name,
                   SUM(CASE WHEN a.Attendance = 1 THEN 1 ELSE 0 END) as present_count,
                   COUNT(*) as total_classes
            FROM attendance a JOIN subject sub ON a.subject_id = sub.subject_id
            WHERE a.student_id = ? GROUP BY sub.subject_name
        """, (student_id,))
        rows = cur.fetchall()
        conn.close()
        result = []
        for row in rows:
            percent = (row[1] * 100.0 / row[2]) if row[2] != 0 else 0
            result.append({"subject": row[0], "status": "Present" if percent >= 75 else "Absent", "percentage": round(percent, 2)})
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/marks/<email>', methods=['GET'])
def get_marks(email):
    try:
        conn = get_conn()
        cur  = conn.cursor()
        cur.execute("SELECT Student_id FROM student WHERE Email_id=?", (email,))
        student = cur.fetchone()
        if not student:
            conn.close()
            return jsonify({"error": "Student not found"}), 404
        student_id = student[0]
        cur.execute("SELECT sub.subject_name, m.marks_obtained FROM marks m JOIN subject sub ON m.subject_id = sub.subject_id WHERE m.student_id = ?", (student_id,))
        rows = cur.fetchall()
        conn.close()
        return jsonify([{"subject": row[0], "marks": row[1]} for row in rows])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/subjects/<email>', methods=['GET'])
def get_subjects(email):
    try:
        conn = get_conn()
        cur  = conn.cursor()
        cur.execute("SELECT Student_id FROM student WHERE Email_id=?", (email,))
        student = cur.fetchone()
        if not student:
            conn.close()
            return jsonify({"error": "Student not found"}), 404
        student_id = student[0]
        cur.execute("SELECT DISTINCT s.subject_name FROM subject s JOIN marks m ON s.subject_id = m.subject_id WHERE m.student_id = ?", (student_id,))
        rows = cur.fetchall()
        conn.close()
        return jsonify([row[0] for row in rows])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/results/<email>', methods=['GET'])
def get_results(email):
    try:
        conn = get_conn()
        cur  = conn.cursor()
        cur.execute("SELECT Student_id FROM student WHERE Email_id=?", (email,))
        student = cur.fetchone()
        if not student:
            conn.close()
            return jsonify({"error": "Student not found"}), 404
        student_id = student[0]
        cur.execute("""
            SELECT sub.subject_name,
                   CASE WHEN m.marks_obtained >= sub.max_marks * 0.4 THEN 'Pass' ELSE 'Fail' END
            FROM marks m JOIN subject sub ON m.subject_id = sub.subject_id WHERE m.student_id = ?
        """, (student_id,))
        rows = cur.fetchall()
        conn.close()
        return jsonify([{"subject": row[0], "result": row[1]} for row in rows])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --------------- RUN ----------------
if __name__ == '__main__':
    app.run(debug=True)