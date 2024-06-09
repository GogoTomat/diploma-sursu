import sqlite3
import os
import datetime


class Database:
    def __init__(self, db_file):
        self.db_file = db_file
        self.conn = sqlite3.connect(self.db_file, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()
        # self.add_news_table()
        # self.add_is_active_column()


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
            SELECT id, last_name, first_name, middle_name, group_id 
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

    def add_is_active_column(self):
        self.cursor.execute("ALTER TABLE users ADD COLUMN isActive BOOL DEFAULT 1")
        self.conn.commit()

    def find_students_by_name_and_group(self, full_name, group_name):
        self.cursor.execute("""
            SELECT users.id, last_name, first_name, middle_name 
            FROM users 
            JOIN groups ON users.group_id = groups.id 
            WHERE users.roles = 'student' AND groups.name = ? AND last_name || ' ' || first_name || ' ' || middle_name = ?
        """, (group_name, full_name))
        return self.cursor.fetchone()

    def find_teachers_by_name_and_department(self, full_name, department):
        self.cursor.execute("""
            SELECT id, last_name, first_name, middle_name 
            FROM users 
            WHERE roles = 'teacher' AND department = ? AND last_name || ' ' || first_name || ' ' || middle_name = ?
        """, (department, full_name))
        return self.cursor.fetchone()

    def update_user_activity_status(self):
        today = datetime.date.today()
        self.cursor.execute("""
            UPDATE users 
            SET isActive = CASE 
                WHEN start_date <= ? AND end_date >= ? THEN 1
                ELSE 0
            END
        """, (today, today))
        self.conn.commit()

    def view_is_active(self, user_id):
        self.cursor.execute("SELECT isActive FROM users WHERE id = ?", (user_id,))
        result = self.cursor.fetchone()
        if result:
            return result[0]
        return None

    def get_user_by_id(self, user_id):
        self.cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        result = self.cursor.fetchone()
        if result:
            user_data = {
                "id": result[0],
                "last_name": result[1],
                "first_name": result[2],
                "middle_name": result[3],
                "roles": result[4],
                "group_id": result[5],
                "department": result[6],
                "start_date": result[7],
                "end_date": result[8],
                "isActive": result[9] if len(result) > 9 else None
            }
            return user_data
        return None

    def get_subjects_taught_by_teacher(self, teacher_id):
        self.cursor.execute("""
            SELECT  subjects.name, subjects.short_name
            FROM taught_subjects
            JOIN subjects ON taught_subjects.subject_id = subjects.id
            WHERE taught_subjects.teacher_id = ?
        """, (teacher_id,))
        return self.cursor.fetchall()

    def get_group_id_by_subject_name(self, subject_name):
        self.cursor.execute("""
            SELECT id 
            FROM subjects
            WHERE name = ? OR short_name = ?
        """, (subject_name, subject_name))
        subject = self.cursor.fetchone()
        if subject:
            subject_id = subject[0]
            self.cursor.execute("""
                SELECT group_id 
                FROM taught_subjects
                WHERE subject_id = ?
            """, (subject_id,))
            result = self.cursor.fetchone()
            if result:
                return result[0]
        return None

    def add_news_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS news (
                id INTEGER PRIMARY KEY,
                new TEXT,
                themes TEXT
            );
        """)
        self.conn.commit()

    def view_recent_news(self, num):
        self.cursor.execute("""
            SELECT * FROM news ORDER BY id DESC LIMIT ?
        """, (num,))
        rows = self.cursor.fetchall()
        news_list = []
        for row in rows:
            news_dict = {
                'id': row[0],
                'topic': row[1],
                'text': row[2],
            }
            news_list.append(news_dict)
        return news_list

    def view_recent_news_by_theme(self, num, theme):
        self.cursor.execute("""
            SELECT * FROM news WHERE themes LIKE ? ORDER BY id DESC LIMIT ?
        """, ('%' + theme + '%', num))
        rows = self.cursor.fetchall()
        return rows

    def add_news_entry(self, news_content, themes):
        self.cursor.execute("""
            INSERT INTO news (new, themes) VALUES (?, ?)
        """, (news_content, themes))
        self.conn.commit()

    def execute_query(self, query, params):
        pass


db = Database("your_database.db")
# users = db.get_subjects_taught_by_teacher(6383988180)
# print(users)
# subject_names = 'АиГ'
taught = db.get_subjects_taught_by_teacher(6383988180)
print(taught)
# for full, short in taught:
#     if short == subject_names or short == subject_names:
#         print(1)
#         break
#     else:
#         print(2)
#         break