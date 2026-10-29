import csv
import sqlite3
import random
from werkzeug.security import generate_password_hash


def import_from_csv(csv_filename):
    print(f"Đang đọc dữ liệu từ file {csv_filename}...")

    # Kết nối trực tiếp vào database hiện tại của web
    conn = sqlite3.connect('database.db')

    # Mật khẩu mặc định cho tất cả sinh viên nhập từ file là '11111'
    default_pass = generate_password_hash('11111')
    advisor_id = 'KCN101000'  # Gán cho thầy Hưng chủ nhiệm luôn
    subjects = ['INT1154', 'INT1339', 'INT1340', 'BAS1203']

    count = 0
    try:
        with open(csv_filename, mode='r', encoding='utf-8-sig') as file:
            reader = csv.DictReader(file)
            for row in reader:
                s_id = row['student_id'].strip()
                name = row['name'].strip()
                cls = row['class_name'].strip()
                email = f"{s_id.lower()}@stu.ptit.edu.vn"

                # Random điểm rèn luyện từ 40 đến 100 để test biểu đồ
                t_score = random.randint(40, 100)

                # 1. Bơm thông tin sinh viên vào Database
                conn.execute('''
                    INSERT OR IGNORE INTO students(
                        student_id, name, email, gender, CCCD, address, birth, religion, ethnic_group, 
                        major, faculty, cohort, academic_year, status, class, advisor_id, password, training_score
                    ) VALUES(
                        ?, ?, ?, 'Nam', '001206123456', 'Hà Nội', '01/01/2006', 'Không', 'Kinh', 
                        'CNTT', 'Công nghệ thông tin 1', 'Đại học chính quy', '2024-2029', 'Đang học', ?, ?, ?, ?
                    )
                ''', (s_id, name, email, cls, advisor_id, default_pass, t_score))

                # 2. Bơm ngẫu nhiên điểm 4 môn học để test tính năng Cảnh báo học vụ
                for sub in subjects:
                    att = random.choice([8.0, 9.0, 10.0])  # Chuyên cần
                    mid = round(random.uniform(4.0, 9.5), 1)  # Giữa kỳ
                    fin = round(random.uniform(3.0, 9.5), 1)  # Cuối kỳ (có điểm thấp để sinh ra Nợ môn)
                    conn.execute('''
                        INSERT OR IGNORE INTO grades (student_id, subject_id, attendance_score, midterm_score, final_score) 
                        VALUES (?, ?, ?, ?, ?)
                    ''', (s_id, sub, att, mid, fin))

                count += 1

        conn.commit()
        print(f"✅ Đã nạp thành công {count} sinh viên và tự động tạo bảng điểm ngẫu nhiên!")
    except Exception as e:
        print(f"❌ Có lỗi xảy ra: {e}")
    finally:
        conn.close()


if __name__ == '__main__':
    import_from_csv('danhsach.csv')