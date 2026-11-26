"""BIT3360 Database Security prototype: permission matrix + audit log demo.

Logs in as each user in turn, tries operations, and prints ALLOWED / DENIED
next to what we EXPECT. Run AFTER 01_security_setup.sql.

    pip install mysql-connector-python
    python 03_permission_and_audit_demo.py

Sample data only. Test changes are rolled back, except the one deliberate
grade change used for the audit-log demonstration (restored at the end).
"""
import mysql.connector
from mysql.connector import Error

DB = "zuct_records"
PASSWORDS = {
    "admin_user": "Admin#2026",
    "registrar_user": "Registrar#2026",
    "lecturer_user": "Lecturer#2026",
    "auditor_user": "Auditor#2026",
}

# (user, description, SQL, should_be_allowed)
TESTS = [
    ("admin_user", "SELECT students", "SELECT * FROM students", True),
    ("admin_user", "SELECT audit_log", "SELECT * FROM audit_log", True),
    ("admin_user", "DELETE grades", "DELETE FROM grades WHERE grade_id = 5", True),

    ("registrar_user", "SELECT students", "SELECT * FROM students", True),
    ("registrar_user", "INSERT students",
     "INSERT INTO students (full_name,email,phone,programme) VALUES ('Test','t@example.com','0970000000','BIT')", True),
    ("registrar_user", "UPDATE students", "UPDATE students SET programme='BIT' WHERE student_id = 1", True),
    ("registrar_user", "SELECT grades", "SELECT * FROM grades", True),
    ("registrar_user", "UPDATE grades", "UPDATE grades SET mark = 99 WHERE grade_id = 1", False),
    ("registrar_user", "DELETE students", "DELETE FROM students WHERE student_id = 1", False),
    ("registrar_user", "SELECT audit_log", "SELECT * FROM audit_log", False),

    ("lecturer_user", "SELECT student_public (view)", "SELECT * FROM student_public", True),
    ("lecturer_user", "SELECT students (phone)", "SELECT phone FROM students", False),
    ("lecturer_user", "UPDATE grades", "UPDATE grades SET mark = 70 WHERE grade_id = 2", True),
    ("lecturer_user", "INSERT grades", "INSERT INTO grades (student_id,course_code,mark) VALUES (1,'BIT3361',60)", True),
    ("lecturer_user", "DELETE grades", "DELETE FROM grades WHERE grade_id = 2", False),
    ("lecturer_user", "SELECT audit_log", "SELECT * FROM audit_log", False),

    ("auditor_user", "SELECT grades", "SELECT * FROM grades", True),
    ("auditor_user", "SELECT audit_log", "SELECT * FROM audit_log", True),
    ("auditor_user", "SELECT students", "SELECT * FROM students", False),
    ("auditor_user", "UPDATE grades", "UPDATE grades SET mark = 100", False),
    ("auditor_user", "DELETE grades", "DELETE FROM grades", False),
]


def connect(user):
    return mysql.connector.connect(host="localhost", user=user,
                                   password=PASSWORDS[user], database=DB)


def attempt(conn, sql):
    """Return (allowed, detail). Rolls back so test data is unchanged."""
    cur = conn.cursor()
    try:
        cur.execute(sql)
        if cur.with_rows:
            detail = f"{len(cur.fetchall())} row(s) returned"
        else:
            detail = f"{cur.rowcount} row(s) affected"
        return True, detail
    except Error as e:
        return False, f"error {e.errno}: {e.msg}"
    finally:
        conn.rollback()
        cur.close()


print("=" * 100)
print("PART 1: WHAT CAN EACH USER DO?")
print("=" * 100)
passed = 0
current = None
conn = None
for user, desc, sql, expected in TESTS:
    if user != current:
        if conn:
            conn.close()
        conn = connect(user)
        current = user
        print(f"\n--- Logged in as {user} ---")
    allowed, detail = attempt(conn, sql)
    result = "ALLOWED" if allowed else "DENIED "
    ok = "PASS" if allowed == expected else "FAIL (unexpected)"
    passed += allowed == expected
    print(f"  {result} | {desc:<28} | {ok:<5} | {detail[:60]}")
conn.close()
print(f"\n{passed}/{len(TESTS)} results matched the expected permissions.")

print("\n" + "=" * 100)
print("PART 2: AUDIT LOG DEMONSTRATION")
print("=" * 100)

lec = connect("lecturer_user")
cur = lec.cursor()
print("\n1) lecturer_user changes grade 1 from 72 to 75 (and commits)")
cur.execute("UPDATE grades SET mark = 75 WHERE grade_id = 1")
lec.commit()
cur.close()
lec.close()

aud = connect("auditor_user")
cur = aud.cursor()
print("\n2) auditor_user reads the audit log:")
cur.execute("SELECT log_id, table_name, action, record_id, old_value, new_value, db_user, changed_at "
            "FROM audit_log ORDER BY log_id")
print("   log_id | table  | action | record | old | new | user                | time")
for row in cur.fetchall():
    print("   " + " | ".join(str(c) for c in row))
cur.close()
aud.close()

adm = connect("admin_user")
cur = adm.cursor()
print("\n3) admin_user restores the mark to 72 (this is also logged)")
cur.execute("UPDATE grades SET mark = 72 WHERE grade_id = 1")
adm.commit()
cur.close()
adm.close()
print("\nDone. Take a screenshot of this output for your presentation.")
