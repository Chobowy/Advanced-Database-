-- BIT3360 Database Security prototype (MySQL)
-- Run as root/admin in DBeaver. Sample data only.

DROP DATABASE IF EXISTS zuct_records;
CREATE DATABASE zuct_records;
USE zuct_records;

-- ---------- Tables ----------
CREATE TABLE students (
  student_id INT PRIMARY KEY AUTO_INCREMENT,
  full_name  VARCHAR(80) NOT NULL,
  email      VARCHAR(80) NOT NULL,
  phone      VARCHAR(20),
  programme  VARCHAR(60) NOT NULL
);

CREATE TABLE grades (
  grade_id    INT PRIMARY KEY AUTO_INCREMENT,
  student_id  INT NOT NULL,
  course_code VARCHAR(10) NOT NULL,
  mark        INT NOT NULL CHECK (mark BETWEEN 0 AND 100),
  FOREIGN KEY (student_id) REFERENCES students(student_id)
);

CREATE TABLE audit_log (
  log_id     INT PRIMARY KEY AUTO_INCREMENT,
  table_name VARCHAR(30),
  action     VARCHAR(10),
  record_id  INT,
  old_value  VARCHAR(100),
  new_value  VARCHAR(100),
  db_user    VARCHAR(80),
  changed_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ---------- Sample data ----------
INSERT INTO students (full_name, email, phone, programme) VALUES
 ('Mary Banda',    'mary.banda@example.com',    '0971000001', 'BIT'),
 ('John Phiri',    'john.phiri@example.com',    '0971000002', 'BIT'),
 ('Grace Mwansa',  'grace.mwansa@example.com',  '0971000003', 'BSc Computer Science'),
 ('Peter Zulu',    'peter.zulu@example.com',    '0971000004', 'BIT'),
 ('Ruth Tembo',    'ruth.tembo@example.com',    '0971000005', 'BSc Computer Science');

INSERT INTO grades (student_id, course_code, mark) VALUES
 (1,'BIT3360',72),(2,'BIT3360',65),(3,'BIT3360',80),(4,'BIT3360',58),(5,'BIT3360',77);

-- View that hides contact details (used by lecturers)
CREATE VIEW student_public AS
  SELECT student_id, full_name, programme FROM students;

-- ---------- Audit triggers (run with the definer's rights) ----------
DELIMITER //
CREATE TRIGGER trg_grades_update AFTER UPDATE ON grades
FOR EACH ROW
BEGIN
  INSERT INTO audit_log (table_name, action, record_id, old_value, new_value, db_user)
  VALUES ('grades', 'UPDATE', OLD.grade_id, OLD.mark, NEW.mark, USER());
END//

CREATE TRIGGER trg_grades_insert AFTER INSERT ON grades
FOR EACH ROW
BEGIN
  INSERT INTO audit_log (table_name, action, record_id, old_value, new_value, db_user)
  VALUES ('grades', 'INSERT', NEW.grade_id, NULL, NEW.mark, USER());
END//
DELIMITER ;

-- ---------- Users and least-privilege permissions ----------
DROP USER IF EXISTS 'admin_user'@'localhost';
DROP USER IF EXISTS 'registrar_user'@'localhost';
DROP USER IF EXISTS 'lecturer_user'@'localhost';
DROP USER IF EXISTS 'auditor_user'@'localhost';

CREATE USER 'admin_user'@'localhost'     IDENTIFIED BY 'Admin#2026';
CREATE USER 'registrar_user'@'localhost' IDENTIFIED BY 'Registrar#2026';
CREATE USER 'lecturer_user'@'localhost'  IDENTIFIED BY 'Lecturer#2026';
CREATE USER 'auditor_user'@'localhost'   IDENTIFIED BY 'Auditor#2026';

-- Administrator: full control of this database
GRANT ALL PRIVILEGES ON zuct_records.* TO 'admin_user'@'localhost';

-- Registrar: manages student details, can only read grades
GRANT SELECT, INSERT, UPDATE ON zuct_records.students TO 'registrar_user'@'localhost';
GRANT SELECT ON zuct_records.grades TO 'registrar_user'@'localhost';

-- Lecturer: sees names/programmes only (via view), manages grades
GRANT SELECT ON zuct_records.student_public TO 'lecturer_user'@'localhost';
GRANT SELECT, INSERT, UPDATE ON zuct_records.grades TO 'lecturer_user'@'localhost';

-- Auditor: read-only on grades and the audit log
GRANT SELECT ON zuct_records.grades TO 'auditor_user'@'localhost';
GRANT SELECT ON zuct_records.audit_log TO 'auditor_user'@'localhost';

FLUSH PRIVILEGES;

-- ---------- Demonstration queries (run each as the user named) ----------
-- registrar_user: SELECT * FROM students;                      -> allowed
-- registrar_user: DELETE FROM students WHERE student_id = 1;   -> DENIED
-- lecturer_user : SELECT * FROM student_public;                -> allowed
-- lecturer_user : SELECT phone FROM students;                  -> DENIED
-- lecturer_user : UPDATE grades SET mark = 75 WHERE grade_id=1;-> allowed (logged)
-- auditor_user  : SELECT * FROM audit_log;                     -> allowed, shows the change
-- auditor_user  : UPDATE grades SET mark = 100;                -> DENIED
