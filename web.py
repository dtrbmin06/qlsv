from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key='qlsv'


# Hàm kết nối CSDL SQLite
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row  # Truy xuất dữ liệu dưới dạng Dictionary
    return conn


# Khởi tạo bảng dữ liệu nếu chưa có
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

    conn.execute('''INSERT OR IGNORE INTO students(student_id,name,email,major,password,role) Values('admin','Quản trị viên', 'admin@ptit.edu.vn','Quan tri vien',123456,'admin')
    ''')
    conn.execute('''
    INSERT OR IGNORE INTO students(student_id,name,email,major,password,role) Values('B24DCCN422','Nguyễn Trọng Nghĩa','nghiapro130206@gmail.com','CNTT','nghiadai123','student')
    ''')

    conn.commit()
    conn.close()


# Trang chủ: Hiển thị danh sách & Tìm kiếm sinh viên
@app.route('/')
def index():
    search_query = request.args.get('search', '')
    conn = get_db_connection()
    if search_query:
        students = conn.execute(
            "SELECT * FROM students WHERE name LIKE ? OR student_id LIKE ?",
            (f'%{search_query}%', f'%{search_query}%')
        ).fetchall()
    else:
        students = conn.execute('SELECT * FROM students').fetchall()
    conn.close()
    return render_template('index.html', students=students, search_query=search_query)


# Chức năng Thêm sinh viên
@app.route('/add', methods=['POST'])
def add_student():
    student_id = request.form['student_id']
    name = request.form['name']
    email = request.form['email']
    major = request.form['major']

    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO students (student_id, name, email, major) VALUES (?, ?, ?, ?)',
                     (student_id, name, email, major))
        conn.commit()
    except sqlite3.IntegrityError:
        pass  # Xử lý nếu trùng Mã sinh viên
    finally:
        conn.close()
    return redirect(url_for('index'))


# Chức năng Sửa thông tin sinh viên
@app.route('/edit/<int:id>', methods=['POST'])
def edit_student(id):
    name = request.form['name']
    email = request.form['email']
    major = request.form['major']

    conn = get_db_connection()
    conn.execute('UPDATE students SET name = ?, email = ?, major = ? WHERE id = ?',
                 (name, email, major, id))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))


# Chức năng Xóa sinh viên
@app.route('/delete/<int:id>')
def delete_student(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM students WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))



@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=='POST':
        tai_khoan=request.form['username']
        mk=request.form['password']

        conn=get_db_connection()
        user=conn.execute('Select * from students where student_id = ? and password = ? ',(tai_khoan,mk)).fetchone()

        if user:
            session['student_id']=user['student_id']
            session['name']=user['name']
            session['role']=user['role']

            return redirect(url_for('index'))
        else:
            return "Sai tài khoản hoặc mật khẩu!"

    return render_template('login.html')


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
