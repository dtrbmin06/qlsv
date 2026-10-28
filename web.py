import os
import math
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
# Đọc secret key từ biến môi trường, có fallback để dev
app.secret_key = os.getenv('SECRET_KEY', 'qlsv_secret_key_2026_default')
STUDENTS_PER_PAGE = 5


def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()


    conn.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL UNIQUE,
            password text,

            name TEXT NOT NULL,
            email TEXT NOT NULL,
            gender TEXT NOT NULL,
            CCCD text not null,
            address text not null,
            birth text not null,
            religion text,
            ethnic_group text,

            major TEXT NOT NULL,
            faculty text,
            cohort text,
            academic_year text,
            status text DEFAULT 'Đang học',
            class text not null,

            advisor_id text,
            Foreign key (advisor_id) references advisors (advisor_id)
        )
    ''')


    conn.execute('''
    CREATE TABLE if not exists subjects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject_id TEXT NOT NULL UNIQUE,
        subject_name TEXT NOT NULL,
        credits INTEGER NOT NULL 
        )
    ''')

    conn.execute('''
        CREATE TABLE if not exists grades(
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              student_id TEXT NOT NULL,
              subject_id TEXT NOT NULL,
              attendance_score  FLOAT,
              midterm_score FLOAT,
              final_score float,
              FOREIGN KEY (student_id) REFERENCES students (student_id),
              FOREIGN KEY (subject_id) REFERENCES subjects (subject_id),
              UNIQUE(student_id, subject_id)
              )
        ''')


    conn.execute('''
    CREATE Table if not exists advisors(
          id Integer primary key autoincrement,
          advisor_id text not null unique,
          password text,
          name text not null,
          email text not null,
          sdt text not null
          )
    ''')


    advisor_pass = generate_password_hash('123456')
    student_pass = generate_password_hash('11111')

    conn.execute('''
            INSERT OR IGNORE INTO advisors (advisor_id, password, name, email, sdt) 
            VALUES ('KCN101000', ?, 'Nguyễn Quang Hưng', 'hungnq1@ptit.edu.vn', '0949790117')
        ''', (advisor_pass,))

    conn.execute('''
            INSERT OR IGNORE INTO students(
                student_id, name, email, gender, CCCD, address, birth, religion, ethnic_group, 
                major, faculty, cohort, academic_year, status, class, advisor_id, password
            ) VALUES(
                'B24DCCN422', 'Nguyễn Trọng Nghĩa', 'nghiapro130206@gmail.com', 'Nam', '001206123456', 
                'Hà Nội', '13/02/2006', 'Không', 'Kinh', 
                'CNTT', 'Công nghệ thông tin 1', 'Đại học chính quy', '2024-2029', 'Đang học', 'D24CQCN04-B', 'KCN101000', ?
            )
        ''', (student_pass,))


    conn.executescript('''
            INSERT OR IGNORE INTO subjects (subject_id, subject_name, credits) VALUES ('INT1154', 'Cấu trúc dữ liệu và Giải thuật', 3);
            INSERT OR IGNORE INTO subjects (subject_id, subject_name, credits) VALUES ('INT1339', 'Lập trình hướng đối tượng', 3);
            INSERT OR IGNORE INTO subjects (subject_id, subject_name, credits) VALUES ('INT1340', 'Cơ sở dữ liệu', 3);
            INSERT OR IGNORE INTO subjects (subject_id, subject_name, credits) VALUES ('BAS1203', 'Giải tích 1', 3);
        ''')

    conn.executescript('''
                INSERT OR IGNORE INTO grades (student_id, subject_id, attendance_score, midterm_score, final_score) VALUES ('B24DCCN422', 'INT1154', 10.0, 8.5, 9.0);
                INSERT OR IGNORE INTO grades (student_id, subject_id, attendance_score, midterm_score, final_score) VALUES ('B24DCCN422', 'INT1339', 9.0, 7.5, 8.0);
                INSERT OR IGNORE INTO grades (student_id, subject_id, attendance_score, midterm_score, final_score) VALUES ('B24DCCN422', 'INT1340', 10.0, 9.0, 8.5);
                INSERT OR IGNORE INTO grades (student_id, subject_id, attendance_score, midterm_score, final_score) VALUES ('B24DCCN422', 'BAS1203', 8.0, 6.5, 7.0);
            ''')

    conn.commit()
    conn.close()



init_db()


def is_admin():
    return session.get('role') == 'admin'


@app.route('/')
def index():
    if 'student_id' not in session:
        return redirect(url_for('login'))

    if session.get('role') == 'advisor':
        return redirect(url_for('manage'))

    return render_template('home.html')



@app.route('/add', methods=['POST'])
def add_student():
    if not is_admin():
        flash("Bạn không có quyền thực hiện thao tác này!")
        return redirect(url_for('login'))

    student_id = request.form['student_id'].strip()
    name = request.form['name'].strip()
    email = request.form['email'].strip()
    major = request.form['major'].strip()


    if not student_id or not name or not email or not major:
        flash("Vui lòng điền đầy đủ thông tin!")
        return redirect(url_for('manage'))

    s = name.split()
    mainname = s[-1]

    c = ''
    for i in range(len(s) - 1):
        c += s[i][0]
    password = f"{mainname}{c}.{student_id}"

    conn = get_db_connection()
    try:
        mk_ma_hoa=generate_password_hash(password)
        conn.execute(
            'INSERT INTO students (student_id, name, email, major, password) VALUES (?, ?, ?, ?, ?)',
            (student_id, name, email, major, mk_ma_hoa)
        )
        conn.commit()
        flash("Thêm sinh viên mới thành công!")
    except sqlite3.IntegrityError:
        flash("Lỗi: Mã sinh viên đã tồn tại trong hệ thống!")
    finally:
        conn.close()
    return redirect(url_for('manage'))


@app.route('/edit/<int:id>', methods=['POST'])
def edit_student(id):
    if not is_admin():
        flash("Bạn không có quyền thực hiện thao tác này!")
        return redirect(url_for('login'))

    name = request.form['name'].strip()
    email = request.form['email'].strip()
    major = request.form['major'].strip()

    conn = get_db_connection()
    conn.execute('UPDATE students SET name = ?, email = ?, major = ? WHERE id = ?',
                 (name, email, major, id))
    conn.commit()

    # Cập nhật lại session nếu admin tự sửa thông tin chính mình
    user = conn.execute('SELECT * FROM students WHERE id = ?', (id,)).fetchone()
    if user and user['student_id'] == session.get('student_id'):
        session['name'] = user['name']
        session['email'] = user['email']
        session['major'] = user['major']

    conn.close()
    flash("Cập nhật thông tin thành công!")
    return redirect(url_for('manage'))


# Chuyển route xóa sang phương thức POST để bảo mật
@app.route('/delete/<int:id>', methods=['POST'])
def delete_student(id):
    if not is_admin():
        flash("Bạn không có quyền thực hiện thao tác này!")
        return redirect(url_for('login'))

    conn = get_db_connection()
    conn.execute('DELETE FROM students WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash("Xóa sinh viên thành công!")
    return redirect(url_for('manage'))


@app.route('/change-password', methods=['POST'])
def change_password():
    if 'student_id' not in session:
        return redirect(url_for('login'))

    old_pass = request.form['old_password']
    new_pass = request.form['new_password']
    role = session.get('role')

    if len(new_pass) < 6:
        flash("Mật khẩu mới phải có ít nhất 6 ký tự!")
        return redirect(url_for('advisor_home') if role == 'advisor' else url_for('profile'))

    conn = get_db_connection()
    account_id = session['student_id']

    if role == 'student':
        user = conn.execute('SELECT * FROM students WHERE student_id = ?', (account_id,)).fetchone()
        table_name = 'students'
        id_column = 'student_id'
    else:
        user = conn.execute('SELECT * FROM advisors WHERE advisor_id = ?', (account_id,)).fetchone()
        table_name = 'advisors'
        id_column = 'advisor_id'

    if user and check_password_hash(user['password'], old_pass):
        hashed_new_pass = generate_password_hash(new_pass)
        conn.execute(f'UPDATE {table_name} SET password = ? WHERE {id_column} = ?', (hashed_new_pass, account_id))
        conn.commit()
        conn.close()
        flash("Đổi mật khẩu thành công!")
    else:
        conn.close()
        flash("Mật khẩu cũ không chính xác!")

    return redirect(url_for('advisor_home') if role == 'advisor' else url_for('profile'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'student_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        tai_khoan = request.form['username'].strip()
        mk = request.form['password']

        conn = get_db_connection()

        user = conn.execute('SELECT * FROM students WHERE student_id = ?', (tai_khoan,)).fetchone()

        if user and check_password_hash(user['password'], mk):
            session['student_id'] = user['student_id']
            session['name'] = user['name']
            session['role'] = 'student'
            conn.close()
            return redirect(url_for('index'))

        advisor = conn.execute('SELECT * FROM advisors WHERE advisor_id = ?', (tai_khoan,)).fetchone()

        if advisor and check_password_hash(advisor['password'], mk):
            session['student_id'] = advisor['advisor_id']
            session['name'] = advisor['name']
            session['role'] = 'advisor'
            conn.close()
            return redirect(url_for('advisor_home'))

        conn.close()
        flash("Sai tài khoản hoặc mật khẩu!")

    return render_template('login.html')


@app.route('/advisor')
def advisor_home():
    if session.get('role') != 'advisor':
        return redirect(url_for('login'))

    advisor_id = session['student_id']
    conn = get_db_connection()

    total_students = conn.execute("SELECT COUNT(*) FROM students WHERE advisor_id = ?", (advisor_id,)).fetchone()[0]
    students = conn.execute("SELECT student_id, name FROM students WHERE advisor_id = ?", (advisor_id,)).fetchall()

    warning_students = []
    stats = {'gioi': 0, 'kha': 0, 'tb': 0, 'yeu': 0}

    for s in students:
        grades = conn.execute('''
            SELECT attendance_score, midterm_score, final_score, credits 
            FROM grades 
            JOIN subjects ON grades.subject_id = subjects.subject_id 
            WHERE student_id = ?
        ''', (s['student_id'],)).fetchall()

        if grades:
            failed_subjects = 0
            total_score = 0
            total_credits = 0

            for g in grades:
                tong_ket = round(g['attendance_score'] * 0.1 + g['midterm_score'] * 0.2 + g['final_score'] * 0.7, 1)
                if tong_ket < 4.0:
                    failed_subjects += 1
                total_score += (tong_ket * g['credits'])
                total_credits += g['credits']

            if failed_subjects > 0:
                warning_students.append({
                    'id': s['student_id'],
                    'name': s['name'],
                    'failed_count': failed_subjects
                })

            gpa = round(total_score / total_credits, 2) if total_credits > 0 else 0
            if gpa >= 8.0:
                stats['gioi'] += 1
            elif gpa >= 6.5:
                stats['kha'] += 1
            elif gpa >= 5.0:
                stats['tb'] += 1
            else:
                stats['yeu'] += 1

    conn.close()
    chart_data = [stats['gioi'], stats['kha'], stats['tb'], stats['yeu']]

    return render_template('advisor_home.html', total_students=total_students, warning_students=warning_students,
                           chart_data=chart_data)


@app.route('/manage')
def manage():
    if 'student_id' not in session:
        return redirect(url_for('login'))

    if session.get('role') != 'advisor':
        flash("Bạn không có quyền truy cập trang quản trị!")
        return redirect(url_for('profile'))

    advisor_id = session['student_id']
    search_query = request.args.get('search', '').strip()
    class_filter = request.args.get('class_filter', '').strip()
    page = request.args.get('page', 1, type=int)
    offset = (page - 1) * STUDENTS_PER_PAGE

    conn = get_db_connection()

    classes = conn.execute("SELECT DISTINCT class FROM students WHERE advisor_id = ?", (advisor_id,)).fetchall()
    class_list = [c['class'] for c in classes]

    query = "SELECT * FROM students WHERE advisor_id = ?"
    params = [advisor_id]

    if search_query:
        query += " AND (name LIKE ? OR student_id LIKE ?)"
        params.extend([f'%{search_query}%', f'%{search_query}%'])

    if class_filter:
        query += " AND class = ?"
        params.append(class_filter)

    count_query = query.replace("SELECT *", "SELECT COUNT(*)")
    query_count = conn.execute(count_query, params).fetchone()[0]

    query += " LIMIT ? OFFSET ?"
    params.extend([STUDENTS_PER_PAGE, offset])
    students = conn.execute(query, params).fetchall()

    conn.close()
    total_pages = math.ceil(query_count / STUDENTS_PER_PAGE) if query_count > 0 else 1

    return render_template('manage.html', students=students, search_query=search_query,
                           page=page, total_pages=total_pages, class_list=class_list, class_filter=class_filter)


@app.route('/upload-avatar', methods=['POST'])
def upload_avatar():
    if 'student_id' not in session:
        return redirect(url_for('login'))

    file = request.files.get('avatar')
    if file and file.filename != '':
        os.makedirs(os.path.join('static', 'avatars'), exist_ok=True)
        filepath = os.path.join('static', 'avatars', f"{session['student_id']}.jpg")
        file.save(filepath)
        flash("Cập nhật ảnh đại diện thành công!")

    return redirect(url_for('profile'))


@app.route('/profile')
def profile():
    if 'student_id' not in session:
        return redirect(url_for('login'))

    target_id = request.args.get('id')

    if session.get('role') == 'advisor':
        if not target_id:
            return redirect(url_for('manage'))
    else:
        target_id = session['student_id']

    conn = get_db_connection()
    user = conn.execute('SELECT * FROM students WHERE student_id = ?', (target_id,)).fetchone()

    if not user:
        conn.close()
        return redirect(url_for('index'))

    grades = conn.execute('''
    select s.subject_id,s.subject_name,s.credits,g.id,g.attendance_score,g.midterm_score,g.final_score
    from subjects s
    join grades g on g.subject_id=s.subject_id
    where g.student_id=?
    ''', (target_id,)).fetchall()

    chart_labels = []
    chart_data = []
    total_credits = 0
    total_score = 0

    for g in grades:
        chart_labels.append(g['subject_id'])
        tong_ket = round(g['attendance_score'] * 0.1 + g['midterm_score'] * 0.2 + g['final_score'] * 0.7, 1)
        chart_data.append(tong_ket)
        total_credits += g['credits']
        total_score += (tong_ket * g['credits'])

    gpa = round(total_score / total_credits, 2) if total_credits > 0 else 0.0

    advisor = None
    if user['advisor_id']:
        advisor = conn.execute('Select * from advisors where advisor_id=?', (user['advisor_id'],)).fetchone()

    conn.close()

    if session.get('role') != 'advisor' and user['student_id'] == session.get('student_id'):
        session['name'] = user['name']

    avatar_filename = f"avatars/{target_id}.jpg"
    if os.path.exists(os.path.join('static', avatar_filename)):
        avatar_path = url_for('static', filename=avatar_filename)
    else:
        avatar_path = f"https://ui-avatars.com/api/?name={user['name']}&background=d1ece5&color=0f766e&size=150"

    return render_template('profile.html', user=user, grades=grades, advisor=advisor, chart_data=chart_data,
                           chart_labels=chart_labels, gpa=gpa, total_credits=total_credits, avatar_path=avatar_path)




@app.route('/edit_grades/<student_id>', methods=['GET', 'POST'])
def edit_grades(student_id):
    if session.get('role') != 'advisor':
        return redirect(url_for('login'))

    conn = get_db_connection()

    if request.method == 'POST':
        for key in request.form:
            if key.startswith('attendance_'):
                subj_id = key.split('_')[1]
                att = request.form.get(f'attendance_{subj_id}')
                mid = request.form.get(f'midterm_{subj_id}')
                fin = request.form.get(f'final_{subj_id}')

                conn.execute('''
                    UPDATE grades 
                    SET attendance_score = ?, midterm_score = ?, final_score = ? 
                    WHERE student_id = ? AND subject_id = ?
                ''', (att, mid, fin, student_id, subj_id))
        conn.commit()
        conn.close()
        flash("Cập nhật điểm thành công!")
        return redirect(url_for('manage'))

    student = conn.execute('SELECT * FROM students WHERE student_id = ? AND advisor_id = ?',
                           (student_id, session['student_id'])).fetchone()

    if not student:
        conn.close()
        return redirect(url_for('manage'))

    grades = conn.execute('''
        SELECT s.subject_id, s.subject_name, g.attendance_score, g.midterm_score, g.final_score
        FROM subjects s
        JOIN grades g ON g.subject_id = s.subject_id
        WHERE g.student_id = ?
    ''', (student_id,)).fetchall()

    conn.close()
    return render_template('edit_grades.html', student=student, grades=grades)



@app.route('/logout')
def logout():
    session.clear()
    flash("Bạn đã đăng xuất khỏi hệ thống.")
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)