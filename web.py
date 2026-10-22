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
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            major TEXT NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'student'
        )
    ''')

    admin_pass = generate_password_hash('123456')
    student_pass = generate_password_hash('11111')

    conn.execute('''
        INSERT OR IGNORE INTO students(student_id, name, email, major, password, role) 
        VALUES('admin', 'Quản trị viên', 'admin@ptit.edu.vn', 'Quan tri vien', ?, 'admin')
    ''', (admin_pass,))

    conn.execute('''
        INSERT OR IGNORE INTO students(student_id, name, email, major, password, role) 
        VALUES('B24DCCN422', 'Nguyễn Trọng Nghĩa', 'nghiapro130206@gmail.com', 'CNTT', ?, 'student')
    ''', (student_pass,))

    conn.commit()
    conn.close()


# Đảm bảo database được khởi tạo khi app chạy
init_db()


def is_admin():
    return session.get('role') == 'admin'


@app.route('/')
def index():
    if 'student_id' not in session:
        return redirect(url_for('login'))

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

    return render_template('home.html', students=students, search_query=search_query,
                           page=page, total_pages=total_pages)


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

    student_id = request.form['student_id'].strip()
    name = request.form['name'].strip()
    email = request.form['email'].strip()
    major = request.form['major'].strip()
    default_pass = generate_password_hash('123456')

    if not student_id or not name or not email or not major:
        flash("Vui lòng điền đầy đủ thông tin!")
        return redirect(url_for('manage'))

    conn = get_db_connection()
    try:
        conn.execute(
            'INSERT INTO students (student_id, name, email, major, password) VALUES (?, ?, ?, ?, ?)',
            (student_id, name, email, major, default_pass)
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

    if len(new_pass) < 6:
        flash("Mật khẩu mới phải có ít nhất 6 ký tự!")
        return redirect(url_for('profile'))

    conn = get_db_connection()
    user = conn.execute('SELECT * FROM students WHERE student_id = ?', (session['student_id'],)).fetchone()

    # Chỉ sử dụng check_password_hash (bỏ so sánh chuỗi thuần)
    if user and check_password_hash(user['password'], old_pass):
        hashed_new_pass = generate_password_hash(new_pass)
        conn.execute('UPDATE students SET password = ? WHERE student_id = ?', (hashed_new_pass, session['student_id']))
        conn.commit()
        conn.close()
        flash("Đổi mật khẩu thành công!")
    else:
        conn.close()
        flash("Mật khẩu cũ không chính xác!")

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

        # Chỉ sử dụng check_password_hash
        if user and check_password_hash(user['password'], mk):
            session['student_id'] = user['student_id']
            session['name'] = user['name']
            session['role'] = user['role']
            session['major'] = user['major']
            session['email'] = user['email']

            if session['role'] == 'admin':
                return redirect(url_for('manage'))
            else:
                return redirect(url_for('profile'))
        else:
            flash("Sai tài khoản hoặc mật khẩu!")

    return render_template('login.html')


@app.route('/profile')
def profile():
    if 'student_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    user = conn.execute('SELECT * FROM students WHERE student_id = ?', (session['student_id'],)).fetchone()
    conn.close()

    # Cập nhật lại session name phòng trường hợp đã bị sửa
    if user:
        session['name'] = user['name']

    return render_template('profile.html', user=user)


@app.route('/manage',methods=['GET'])
def manage():
    return render_template('manage.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("Bạn đã đăng xuất khỏi hệ thống.")
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)