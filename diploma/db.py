import sqlite3
import os


class Database:
    def __init__(self, db_file):
        self.db_file = db_file
        self.conn = sqlite3.connect(self.db_file, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                last_name TEXT,
                first_name TEXT,
                middle_name TEXT,
                roles TEXT,
                group_id INTEGER,
                department TEXT,
                start_date TEXT,
                end_date TEXT,
                FOREIGN KEY (group_id) REFERENCES groups(id)
            );
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS roles (
                id INTEGER PRIMARY KEY,
                name TEXT
            );
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS groups (
                id INTEGER PRIMARY KEY,
                name TEXT,
                schedule BLOB
            );
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS subjects (
                id INTEGER PRIMARY KEY,
                name TEXT,
                info TEXT,
                short_name TEXT
            );
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS taught_subjects (
                id INTEGER PRIMARY KEY,
                subject_id INTEGER,
                teacher_id INTEGER,
                group_id INTEGER,
                class_type TEXT,
                FOREIGN KEY (subject_id) REFERENCES subjects(id),
                FOREIGN KEY (teacher_id) REFERENCES users(id),
                FOREIGN KEY (group_id) REFERENCES groups(id)
            );
        """)

        self.conn.commit()

    def add_user(self, id, last_name, first_name, middle_name, roles, group_id, department, start_date, end_date):
        self.cursor.execute("""
            INSERT INTO users (id, last_name, first_name, middle_name, roles, group_id, department, start_date, end_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (id, last_name, first_name, middle_name, roles, group_id, department, start_date, end_date))
        self.conn.commit()

    def add_role(self, id, name):
        self.cursor.execute("""
            INSERT INTO roles (id, name) VALUES (?, ?)
        """, (id, name))
        self.conn.commit()

    def add_group(self, id, name, schedule):
        self.cursor.execute("""
            INSERT INTO groups (id, name, schedule) VALUES (?, ?, ?)
        """, (id, name, schedule))
        self.conn.commit()

    def add_group_with_schedule(self, id, name, schedule_path):
        with open(schedule_path, 'rb') as file:
            schedule = file.read()
        self.add_group(id, name, schedule)

    def add_subject(self, id, name, info=None, short_name=None):
        self.cursor.execute("""
            INSERT INTO subjects (id, name, info, short_name)
            VALUES (?, ?, ?, ?)
        """, (id, name, info, short_name))
        self.conn.commit()

    def add_taught_subject(self, id, subject_id, teacher_id, group_id, class_type):
        self.cursor.execute("""
            INSERT INTO taught_subjects (id, subject_id, teacher_id, group_id, class_type)
            VALUES (?, ?, ?, ?, ?)
        """, (id, subject_id, teacher_id, group_id, class_type))
        self.conn.commit()

    def view_users(self):
        self.cursor.execute("SELECT * FROM users")
        return self.cursor.fetchall()

    def view_roles(self):
        self.cursor.execute("SELECT * FROM roles")
        return self.cursor.fetchall()

    def view_groups(self):
        self.cursor.execute("SELECT * FROM groups")
        return self.cursor.fetchall()

    def view_subjects(self):
        self.cursor.execute("SELECT * FROM subjects")
        return self.cursor.fetchall()

    def view_taught_subjects(self):
        self.cursor.execute("SELECT * FROM taught_subjects")
        return self.cursor.fetchall()

    def delete_database(self):
        self.conn.close()
        if os.path.exists(self.db_file):
            os.remove(self.db_file)
            print(f"Database '{self.db_file}' has been deleted.")
        else:
            print(f"Database '{self.db_file}' does not exist.")

    def get_user_role(self, id):
        self.cursor.execute("SELECT roles FROM users WHERE id = ?", (id,))
        result = self.cursor.fetchone()
        if result:
            return result[0]
        return None

    def get_student_info(self, id):
        self.cursor.execute("""
            SELECT roles, groups.name, last_name, first_name, middle_name 
            FROM users 
            LEFT JOIN groups ON users.group_id = groups.id 
            WHERE users.id = ?
        """, (id,))
        result = self.cursor.fetchone()
        if result:
            return result
        return None, None, None, None, None

    def view_group_schedule(self, group_id):
        self.cursor.execute("SELECT schedule FROM groups WHERE id = ?", (group_id,))
        result = self.cursor.fetchone()
        if result:
            return result[0]
        return None

    def get_group_id_by_student_id(self, student_id):
        self.cursor.execute("SELECT group_id FROM users WHERE id = ?", (student_id,))
        result = self.cursor.fetchone()
        if result:
            return result[0]
        return None

    def get_students_by_group_id(self, group_id):
        self.cursor.execute("SELECT id FROM users WHERE group_id = ?", (group_id,))
        return self.cursor.fetchall()

    def get_group_id_by_name(self, group_name):
        self.cursor.execute("SELECT id FROM groups WHERE name = ?", (group_name,))
        result = self.cursor.fetchone()
        if result:
            return result[0]
        return None

    def get_student_info_by_id(self, student_id):
        self.cursor.execute("""
            SELECT last_name, first_name, middle_name, groups.name 
            FROM users 
            LEFT JOIN groups ON users.group_id = groups.id 
            WHERE users.id = ?
        """, (student_id,))
        result = self.cursor.fetchone()
        if result:
            return {
                "last_name": result[0],
                "first_name": result[1],
                "middle_name": result[2],
                "group_name": result[3]
            }
        return None

    def find_teachers_by_last_name(self, last_name):
        self.cursor.execute("""
            SELECT id, last_name, first_name, middle_name 
            FROM users 
            WHERE roles = 'teacher' AND last_name = ?
        """, (last_name,))
        return self.cursor.fetchall()

    def find_teachers_by_name(self, full_name):
        self.cursor.execute("""
            SELECT id, last_name, first_name, middle_name 
            FROM users 
            WHERE roles = 'teacher' AND last_name || ' ' || first_name || ' ' || middle_name = ?
        """, (full_name,))
        return self.cursor.fetchall()

    def find_students_by_last_name(self, last_name):
        self.cursor.execute("""
            SELECT id, last_name, first_name, middle_name 
            FROM users 
            WHERE roles = 'student' AND last_name = ?
        """, (last_name,))
        return self.cursor.fetchall()

    def find_students_by_name(self, full_name):
        self.cursor.execute("""
            SELECT id, last_name, first_name, middle_name 
            FROM users 
            WHERE roles = 'student' AND last_name || ' ' || first_name || ' ' || middle_name = ?
        """, (full_name,))
        return self.cursor.fetchall()

    def get_teacher_info(self, teacher_id):
        self.cursor.execute("SELECT last_name, first_name, middle_name FROM users WHERE id = ?", (teacher_id,))
        return self.cursor.fetchone()

    def get_teacher_info_all(self, teacher_id):
        self.cursor.execute("SELECT * FROM users WHERE id = ?", (teacher_id,))
        return self.cursor.fetchone()

    def get_teacher_info_by_id(self, teacher_id):
        self.cursor.execute("""
            SELECT last_name, first_name, middle_name
            FROM users  
            WHERE users.id = ?
        """, (teacher_id,))
        result = self.cursor.fetchone()
        if result:
            return {
                "last_name": result[0],
                "first_name": result[1],
                "middle_name": result[2]
            }
        return None

    def get_subject_info(self, subject_name):
        self.cursor.execute("""
            SELECT subjects.name, subjects.info, subjects.short_name, taught_subjects.class_type
            FROM subjects
            LEFT JOIN taught_subjects ON subjects.id = taught_subjects.subject_id
            WHERE subjects.name = ? OR subjects.short_name = ?
        """, (subject_name, subject_name))
        result = self.cursor.fetchone()
        if result:
            return {
                "name": result[0],
                "info": result[1],
                "short_name": result[2],
                "class_type": result[3]
            }
        return None

    def delete_user(self, user_id):
        self.cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        self.conn.commit()

    def delete_group(self, group_id):
        self.cursor.execute("DELETE FROM groups WHERE id = ?", (group_id,))
        self.cursor.execute("UPDATE users SET group_id = NULL WHERE group_id = ?", (group_id,))
        self.conn.commit()

    def alter_subjects_table(self):
        self.cursor.execute("""
            ALTER TABLE subjects ADD COLUMN info TEXT
        """)
        self.cursor.execute("""
            ALTER TABLE subjects ADD COLUMN short_name TEXT
        """)
        self.conn.commit()

    def execute_query(self, query, params):
        pass


db = Database("your_database.db")
# db.alter_subjects_table()
# sub = db.view_taught_subjects()
#
# for s in sub:
#     print(f"{s[0]}, {s[1]}, {s[2]}, {s[3]}, {s[4]}")
#
#
#
# db.add_subject(1, "Алгебра и Геометрия", "Преподаватель: Васильев Василий Васильевич. Время консультации: Среда(16:20)", "АиГ")
# db.add_taught_subject(1, 1, 6383988180, 60901, 'Лекция')

# db.delete_user(5937760889)
# db.delete_group(6001)

# groups = db.view_groups()
#
# for group in groups:
#     print(f"ID: {group[0]}, Name: {group[1]}")

# db.add_user(5937760889, "Иванов", "Иван", "Иванович", "student", 60501, "АиКС", "2021-09-01", "2025-06-30")
#db.add_role(2, "teacher")
# db.add_group_with_schedule(6001, "605-01", "s2.jpg")
# db.add_subject(1, "Математика")
# db.add_taught_subject(1, 1, 1, 1, "Лекция")
# with open("schedule.jpg", 'rb') as file:
#     schedule_image = file.read()
# db.add_group_with_schedule(60901, "609-01", schedule_image)

