import sqlite3
import random
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

ho_list = ['Nguyễn', 'Trần', 'Lê', 'Phạm', 'Hoàng', 'Huỳnh', 'Phan', 'Vũ', 'Võ', 'Đặng', 'Bùi', 'Đỗ', 'Hồ', 'Ngô',
           'Dương']
dem_nam = ['Văn', 'Đình', 'Minh', 'Đức', 'Quang', 'Hữu', 'Công', 'Tiến', 'Thành', 'Trọng']
ten_nam = ['Hùng', 'Nghĩa', 'Long', 'Tùng', 'Sơn', 'Nam', 'Cường', 'Dũng', 'Tuấn', 'Đạt', 'Bình', 'Hải', 'Phong',
           'Khánh']
dem_nu = ['Thị', 'Thu', 'Phương', 'Ngọc', 'Thanh', 'Mai', 'Bích', 'Quỳnh', 'Thúy', 'Diệu']
ten_nu = ['Hà', 'Lan', 'Hương', 'Trang', 'Linh', 'Thảo', 'Yến', 'Anh', 'Phương', 'Hoa', 'Nguyệt', 'Nhung', 'Vy', 'My']

tinh_thanh = ['Hà Nội', 'Hải Phòng', 'Quảng Ninh', 'Nam Định', 'Thái Bình', 'Ninh Bình', 'Bắc Ninh', 'Vĩnh Phúc',
              'Hải Dương', 'Hưng Yên', 'Thanh Hóa', 'Nghệ An', 'Hà Tĩnh', 'Phú Thọ', 'Thái Nguyên']
ton_giao = ['Không'] * 90 + ['Phật giáo'] * 7 + ['Công giáo'] * 3
dan_toc = ['Kinh'] * 95 + ['Tày', 'Mường', 'Thái', 'Nùng', 'H\'Mông']

classes = ['D24CQCN04-B', 'D24CQCN05-B']
subjects = ['INT1154', 'INT1339', 'INT1340', 'BAS1203']


def random_birth():
    start_date = datetime(2006, 1, 1)
    end_date = datetime(2006, 12, 31)
    random_days = random.randint(0, (end_date - start_date).days)
    return (start_date + timedelta(days=random_days)).strftime("%d/%m/%Y")


def random_cccd():
    ma_tinh = f"{random.randint(1, 38):02d}"
    duoi = f"{random.randint(1, 999999):06d}"
    return f"0{ma_tinh}206{duoi}"


def generate_and_import():
    conn = sqlite3.connect('database.db')
    default_pass = generate_password_hash('11111')
    advisor_id = 'KCN101000'
    count = 0

    try:
        for i in range(1, 121):
            ma_sv = f"B24DCCN{i:03d}"

            if random.choice([True, False]):
                gender = 'Nam'
                ho_ten = f"{random.choice(ho_list)} {random.choice(dem_nam)} {random.choice(ten_nam)}"
            else:
                gender = 'Nữ'
                ho_ten = f"{random.choice(ho_list)} {random.choice(dem_nu)} {random.choice(ten_nu)}"

            email = f"{ma_sv.lower()}@stu.ptit.edu.vn"
            cccd = random_cccd()
            address = random.choice(tinh_thanh)
            birth = random_birth()
            religion = random.choice(ton_giao)
            ethnic_group = random.choice(dan_toc)
            status = random.choices(['Đang học', 'Bảo lưu'], weights=[98, 2])[0]
            lop = classes[0] if i <= 60 else classes[1]
            t_score = random.randint(40, 100)

            conn.execute('''
                INSERT OR IGNORE INTO students(
                    student_id, name, email, gender, CCCD, address, birth, religion, ethnic_group, 
                    major, faculty, cohort, academic_year, status, class, advisor_id, password, training_score
                ) VALUES(
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, 
                    ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
            ''', (
                ma_sv, ho_ten, email, gender, cccd, address,
                birth, religion, ethnic_group, 'CNTT', 'Công nghệ thông tin 1',
                'Đại học chính quy', '2024-2029', status, lop,
                advisor_id, default_pass, t_score
            ))

            for sub in subjects:
                att = random.choice([8.0, 9.0, 10.0])
                mid = round(random.uniform(4.0, 9.5), 1)
                fin = round(random.uniform(3.0, 9.5), 1)
                conn.execute('''
                    INSERT OR IGNORE INTO grades (student_id, subject_id, attendance_score, midterm_score, final_score) 
                    VALUES (?, ?, ?, ?, ?)
                ''', (ma_sv, sub, att, mid, fin))

            count += 1

        conn.commit()
        print(f"Da nap thanh cong {count} ho so sinh vien va bang diem vao database!")
    except Exception as e:
        print(f"Loi xay ra: {e}")
    finally:
        conn.close()


if __name__ == '__main__':
    generate_and_import()