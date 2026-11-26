"""BIT3360 Database Security prototype: SQL injection vs parameterised query.
Install the connector first:  pip install mysql-connector-python
Run the SQL setup script before this one.
"""
import getpass
import mysql.connector

password = getpass.getpass("Password for registrar_user: ")
conn = mysql.connector.connect(
    host="localhost", user="registrar_user",
    password=password, database="zuct_records",
)
cur = conn.cursor()


def unsafe_search(programme):
    # VULNERABLE: user input is pasted into the SQL text
    sql = "SELECT student_id, full_name FROM students WHERE programme = '" + programme + "'"
    print("\nSQL sent:", sql)
    cur.execute(sql)
    return cur.fetchall()


def safe_search(programme):
    # SAFE: input is sent separately as a parameter, so it is never run as SQL
    sql = "SELECT student_id, full_name FROM students WHERE programme = %s"
    print("\nSQL sent:", sql, "| parameter:", programme)
    cur.execute(sql, (programme,))
    return cur.fetchall()


normal_input = "BIT"
attack_input = "' OR '1'='1"

print("=== Normal input ===")
print("Unsafe:", unsafe_search(normal_input))
print("Safe:  ", safe_search(normal_input))

print("\n=== Injection attempt: ' OR '1'='1 ===")
print("Unsafe (returns ALL students):", unsafe_search(attack_input))
print("Safe   (returns nothing):     ", safe_search(attack_input))

cur.close()
conn.close()
