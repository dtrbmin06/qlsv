import os
import math
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'qlsv_secret_key_2026_default')
STUDENTS_PER_PAGE = 5

# Cấu hình thư mục Upload Avatar
UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


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
            role text default 'student',

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
            avatar text,

            advisor_id text,
            FOREIGN KEY (advisor_id) REFERENCES advisors (advisor_id)
        )
    ''')

    # Tự động nâng cấp bảng nếu thiếu cột avatar
    try:
        conn.execute("ALTER TABLE students ADD COLUMN avatar text")
    except sqlite3.OperationalError:
        pass

    conn.execute('''
    CREATE TABLE IF NOT EXISTS subjects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject_id TEXT NOT NULL UNIQUE,
        subject_name TEXT NOT NULL,
        credits INTEGER NOT NULL 
    )
    ''')

    conn.execute('''
    CREATE TABLE IF NOT EXISTS grades(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT NOT NULL,
        subject_id TEXT NOT NULL,
        attendance_score FLOAT DEFAULT 0.0,
        midterm_score FLOAT DEFAULT 0.0,
        final_score FLOAT DEFAULT 0.0,
        FOREIGN KEY (student_id) REFERENCES students (student_id),
        FOREIGN KEY (subject_id) REFERENCES subjects (subject_id)
    )
    ''')

    conn.execute('''
    CREATE TABLE IF NOT EXISTS advisors(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        advisor_id TEXT NOT NULL UNIQUE,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        sdt TEXT NOT NULL
    )
    ''')

    conn.execute('''
        INSERT OR IGNORE INTO advisors (advisor_id, name, email, sdt) 
        VALUES ('KCN101000', 'Nguyễn Quang Hưng', 'hungnq1@ptit.edu.vn', '0949790117')
    ''')

    admin_pass = generate_password_hash('123456')
    student_pass = generate_password_hash('11111')

    conn.execute('''
        INSERT OR IGNORE INTO students(
            student_id, name, email, gender, CCCD, address, birth, religion, ethnic_group, 
            major, faculty, cohort, academic_year, status, class, password, role
        ) VALUES(
            'GV01', 'Phòng Giáo Vụ PTIT', 'giaovu@ptit.edu.vn', 'Nam', '000000000000', 
            'Hà Nội', '01/01/1985', 'Không', 'Kinh', 
            'Quản lý Đào tạo', 'Phòng Đào tạo', 'Cán bộ', '2026', 'Đang công tác', 'Giáo vụ', ?, 'admin'
        )
    ''', (admin_pass,))

    conn.execute('''
        INSERT OR IGNORE INTO students(
            student_id, name, email, gender, CCCD, address, birth, religion, ethnic_group, 
            major, faculty, cohort, academic_year, status, class, advisor_id, password, role
        ) VALUES(
            'B24DCCN422', 'Nguyễn Trọng Nghĩa', 'nghiapro130206@gmail.com', 'Nam', '001206123456', 
            'Hà Nội', '13/02/2006', 'Không', 'Kinh', 
            'CNTT', 'Công nghệ thông tin 1', 'Đại học chính quy', '2024-2029', 'Đang học', 'D24CQCN04-B', 'KCN101000', ?, 'student'
        )
    ''', (student_pass,))

    conn.executescript('''
        INSERT OR IGNORE INTO subjects (subject_id, subject_name, credits) VALUES ('INT1154', 'Cấu trúc dữ liệu và Giải thuật', 3);
        INSERT OR IGNORE INTO subjects (subject_id, subject_name, credits) VALUES ('INT1339', 'Lập trình hướng đối tượng', 3);
        INSERT OR IGNORE INTO subjects (subject_id, subject_name, credits) VALUES ('INT1340', 'Cơ sở dữ liệu', 3);
        INSERT OR IGNORE INTO subjects (subject_id, subject_name, credits) VALUES ('BAS1203', 'Giải tích 1', 3);
    ''')

    grade_count = conn.execute("SELECT COUNT(*) FROM grades").fetchone()[0]
    if grade_count == 0:
        conn.executescript('''
            INSERT INTO grades (student_id, subject_id, attendance_score, midterm_score, final_score) VALUES ('B24DCCN422', 'INT1154', 10.0, 8.5, 9.0);
            INSERT INTO grades (student_id, subject_id, attendance_score, midterm_score, final_score) VALUES ('B24DCCN422', 'INT1339', 9.0, 7.5, 8.0);
            INSERT INTO grades (student_id, subject_id, attendance_score, midterm_score, final_score) VALUES ('B24DCCN422', 'INT1340', 10.0, 9.0, 8.5);
            INSERT INTO grades (student_id, subject_id, attendance_score, midterm_score, final_score) VALUES ('B24DCCN422', 'BAS1203', 8.0, 6.5, 7.0);
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
    return render_template('home.html')


@app.route('/manage')
def manage():
    if 'student_id' not in session:
        return redirect(url_for('login'))

    if not is_admin():
        flash("Bạn không có quyền truy cập trang quản trị!")
        return redirect(url_for('profile'))

    search_query = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)
    offset = (page - 1) * STUDENTS_PER_PAGE

    conn = get_db_connection()
    if search_query:
        total_count = conn.execute(
            "SELECT COUNT(*) FROM students WHERE name LIKE ? OR student_id LIKE ?",
            (f'%{search_query}%', f'%{search_query}%')
        ).fetchone()[0]

        students = conn.execute(
            "SELECT * FROM students WHERE name LIKE ? OR student_id LIKE ? LIMIT ? OFFSET ?",
            (f'%{search_query}%', f'%{search_query}%', STUDENTS_PER_PAGE, offset)
        ).fetchall()
    else:
        total_count = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        students = conn.execute(
            "SELECT * FROM students LIMIT ? OFFSET ?", (STUDENTS_PER_PAGE, offset)
        ).fetchall()

    conn.close()
    total_pages = math.ceil(total_count / STUDENTS_PER_PAGE) if total_count > 0 else 1

    return render_template('manage.html', students=students, search_query=search_query,
                           page=page, total_pages=total_pages)


@app.route('/add', methods=['POST'])
def add_student():
    if not is_admin():
        flash("Bạn không có quyền thực hiện thao tác này!")
        return redirect(url_for('login'))

    student_id = request.form.get('student_id', '').strip()
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    major = request.form.get('major', '').strip()
    gender = request.form.get('gender', 'Nam').strip()
    cccd = request.form.get('cccd', '').strip()
    address = request.form.get('address', '').strip()
    birth = request.form.get('birth', '').strip()
    student_class = request.form.get('class', '').strip()

    if not all([student_id, name, email, major, cccd, address, birth, student_class]):
        flash("Vui lòng điền đầy đủ các thông tin bắt buộc!")
        return redirect(url_for('manage'))

    parts = name.split()
    if len(parts) > 1:
        mainname = parts[-1]
        initials = "".join([p[0] for p in parts[:-1]])
        gen_pass = f"{mainname}{initials}.{student_id}"
    else:
        gen_pass = f"{name}.{student_id}"

    hashed_pass = generate_password_hash(gen_pass)

    conn = get_db_connection()
    try:
        conn.execute('''
            INSERT INTO students (
                student_id, name, email, gender, CCCD, address, birth, 
                major, class, password, role
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'student')
        ''', (student_id, name, email, gender, cccd, address, birth, major, student_class, hashed_pass))

        subjects = conn.execute('SELECT subject_id FROM subjects').fetchall()
        for sub in subjects:
            conn.execute('''
                INSERT INTO grades (student_id, subject_id, attendance_score, midterm_score, final_score)
                VALUES (?, ?, 0.0, 0.0, 0.0)
            ''', (student_id, sub['subject_id']))

        conn.commit()
        flash(f"Thêm sinh viên thành công! Mật khẩu mặc định là: {gen_pass}")
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

    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    major = request.form.get('major', '').strip()
    gender = request.form.get('gender', 'Nam').strip()
    cccd = request.form.get('cccd', '').strip()
    address = request.form.get('address', '').strip()
    birth = request.form.get('birth', '').strip()
    student_class = request.form.get('class', '').strip()

    conn = get_db_connection()
    conn.execute('''
        UPDATE students 
        SET name = ?, email = ?, major = ?, gender = ?, CCCD = ?, address = ?, birth = ?, class = ? 
        WHERE id = ?
    ''', (name, email, major, gender, cccd, address, birth, student_class, id))
    conn.commit()

    user = conn.execute('SELECT * FROM students WHERE id = ?', (id,)).fetchone()
    if user and user['student_id'] == session.get('student_id'):
        session['name'] = user['name']
        session['email'] = user['email']
        session['major'] = user['major']

    conn.close()
    flash("Cập nhật thông tin sinh viên thành công!")
    return redirect(url_for('manage'))


@app.route('/delete/<int:id>', methods=['POST'])
def delete_student(id):
    if not is_admin():
        flash("Bạn không có quyền thực hiện thao tác này!")
        return redirect(url_for('login'))

    conn = get_db_connection()
    user = conn.execute('SELECT student_id FROM students WHERE id = ?', (id,)).fetchone()
    if user:
        conn.execute('DELETE FROM grades WHERE student_id = ?', (user['student_id'],))
        conn.execute('DELETE FROM students WHERE id = ?', (id,))
        conn.commit()
        flash("Xóa sinh viên thành công!")
    conn.close()
    return redirect(url_for('manage'))


@app.route('/grades/manage/<student_id>', methods=['GET', 'POST'])
def manage_student_grades(student_id):
    if not is_admin():
        flash("Bạn không có quyền nhập điểm!")
        return redirect(url_for('index'))

    conn = get_db_connection()
    student = conn.execute('SELECT * FROM students WHERE student_id = ?', (student_id,)).fetchone()

    if not student:
        flash("Không tìm thấy sinh viên!")
        conn.close()
        return redirect(url_for('manage'))

    if request.method == 'POST':
        subjects = conn.execute('SELECT subject_id FROM subjects').fetchall()
        for sub in subjects:
            sid = sub['subject_id']
            att = float(request.form.get(f'att_{sid}', 0.0))
            mid = float(request.form.get(f'mid_{sid}', 0.0))
            fin = float(request.form.get(f'fin_{sid}', 0.0))

            existing = conn.execute(
                'SELECT id FROM grades WHERE student_id = ? AND subject_id = ?',
                (student_id, sid)
            ).fetchone()

            if existing:
                conn.execute('''
                    UPDATE grades 
                    SET attendance_score = ?, midterm_score = ?, final_score = ?
                    WHERE student_id = ? AND subject_id = ?
                ''', (att, mid, fin, student_id, sid))
            else:
                conn.execute('''
                    INSERT INTO grades (student_id, subject_id, attendance_score, midterm_score, final_score)
                    VALUES (?, ?, ?, ?, ?)
                ''', (student_id, sid, att, mid, fin))

        conn.commit()
        flash(f"Cập nhật bảng điểm thành công cho sinh viên: {student['name']}")

    grades = conn.execute('''
        SELECT s.subject_id, s.subject_name, s.credits, 
               g.attendance_score, g.midterm_score, g.final_score
        FROM subjects s
        LEFT JOIN grades g ON s.subject_id = g.subject_id AND g.student_id = ?
    ''', (student_id,)).fetchall()

    conn.close()
    return render_template('manage_grades.html', student=student, grades=grades)


# --- NÚT 1: TÍNH NĂNG ĐỔI MẬT KHẨU ---
@app.route('/change-password', methods=['POST'])
def change_password():
    if 'student_id' not in session:
        return redirect(url_for('login'))

    old_pass = request.form.get('old_password')
    new_pass = request.form.get('new_password')
    confirm_pass = request.form.get('confirm_password')

    if new_pass != confirm_pass:
        flash("Mật khẩu xác nhận không trùng khớp!")
        return redirect(url_for('profile'))

    if len(new_pass) < 6:
        flash("Mật khẩu mới phải có ít nhất 6 ký tự!")
        return redirect(url_for('profile'))

    conn = get_db_connection()
    user = conn.execute('SELECT * FROM students WHERE student_id = ?', (session['student_id'],)).fetchone()

    if user and check_password_hash(user['password'], old_pass):
        hashed_new_pass = generate_password_hash(new_pass)
        conn.execute('UPDATE students SET password = ? WHERE student_id = ?', (hashed_new_pass, session['student_id']))
        conn.commit()
        conn.close()
        flash("Đổi mật khẩu thành công!")
    else:
        conn.close()
        flash("Mật khẩu hiện tại không chính xác!")

    return redirect(url_for('profile'))


# --- NÚT 2: TÍNH NĂNG ĐỔI ẢNH ĐẠI DIỆN ---
@app.route('/upload-avatar', methods=['POST'])
def upload_avatar():
    if 'student_id' not in session:
        return redirect(url_for('login'))

    if 'avatar' not in request.files:
        flash('Không tìm thấy file ảnh!')
        return redirect(url_for('profile'))

    file = request.files['avatar']
    if file.filename == '':
        flash('Vui lòng chọn một file ảnh!')
        return redirect(url_for('profile'))

    if file and allowed_file(file.filename):
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = secure_filename(f"avatar_{session['student_id']}.{ext}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        avatar_url = f"/static/uploads/{filename}"

        conn = get_db_connection()
        conn.execute('UPDATE students SET avatar = ? WHERE student_id = ?', (avatar_url, session['student_id']))
        conn.commit()
        conn.close()

        flash("Cập nhật ảnh đại diện thành công!")
    else:
        flash("Định dạng ảnh không hợp lệ! (Chỉ chấp nhận png, jpg, jpeg, gif)")

    return redirect(url_for('profile'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'student_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        tai_khoan = request.form['username'].strip()
        mk = request.form['password']

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM students WHERE student_id = ?', (tai_khoan,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password'], mk):
            session['student_id'] = user['student_id']
            session['name'] = user['name']
            session['role'] = user['role']
            session['major'] = user['major']
            session['email'] = user['email']

            if session['role'] == 'admin':
                return redirect(url_for('manage'))
            else:
                return redirect(url_for('index'))
        else:
            flash("Sai tài khoản hoặc mật khẩu!")

    return render_template('login.html')


@app.route('/profile')
def profile():
    if 'student_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    user = conn.execute('SELECT * FROM students WHERE student_id = ?', (session['student_id'],)).fetchone()

    grades = conn.execute('''
        SELECT s.subject_id, s.subject_name, s.credits, g.attendance_score, g.midterm_score, g.final_score
        FROM subjects s
        JOIN grades g ON g.subject_id = s.subject_id
        WHERE g.student_id = ?
    ''', (session['student_id'],)).fetchall()

    chart_labels = []
    chart_data = []
    formatted_grades = []

    total_credits = 0
    total_score = 0

    for g in grades:
        att = g['attendance_score'] if g['attendance_score'] is not None else 0.0
        mid = g['midterm_score'] if g['midterm_score'] is not None else 0.0
        fin = g['final_score'] if g['final_score'] is not None else 0.0

        sum_score = round(att * 0.1 + mid * 0.2 + fin * 0.7, 1)

        chart_labels.append(g['subject_id'])
        chart_data.append(sum_score)

        formatted_grades.append({
            'subject_id': g['subject_id'],
            'subject_name': g['subject_name'],
            'credits': g['credits'],
            'attendance_score': att,
            'midterm_score': mid,
            'final_score': fin,
            'total_score': sum_score
        })

        total_credits += g['credits']
        total_score += (sum_score * g['credits'])

    gpa = round(total_score / total_credits, 2) if total_credits > 0 else 0.0

    advisor = None
    if user and user['advisor_id']:
        advisor = conn.execute('SELECT * FROM advisors WHERE advisor_id = ?', (user['advisor_id'],)).fetchone()

    conn.close()

    return render_template('profile.html', user=user, grades=formatted_grades, advisor=advisor,
                           chart_data=chart_data, chart_labels=chart_labels, gpa=gpa, total_credits=total_credits)


@app.route('/logout')
def logout():
    session.clear()
    flash("Bạn đã đăng xuất khỏi hệ thống.")
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)