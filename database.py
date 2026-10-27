import mysql.connector
from mysql.connector import Error

class Database:
    def __init__(self):
        # Thông số cấu hình CSDL MySQL
        self.host = "localhost"
        self.user = "root"          # Thay bằng username MySQL của bạn (mặc định là root)
        self.password = "060706"    # Thay bằng mật khẩu MySQL của bạn
        self.database = "QL_TuThien"# Tên CSDL MySQL bạn đã tạo
        self.conn = None

    def connect(self):
        """Mở kết nối tới MySQL"""
        try:
            self.conn = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                charset='utf8mb4'
            )
            if self.conn.is_connected():
                return True
        except Error as e:
            print(f"Lỗi kết nối MySQL: {e}")
            return False

    def disconnect(self):
        """Đóng kết nối MySQL"""
        if self.conn and self.conn.is_connected():
            self.conn.close()

    def fetch_all(self, query, params=None):
        """Hàm dùng chung để SELECT nhiều dòng dữ liệu"""
        if not self.connect():
            return []
        try:
            cursor = self.conn.cursor(dictionary=True) # Trả về dạng Dictionary cho dễ gọi tên cột
            cursor.execute(query, params or ())
            result = cursor.fetchall()
            cursor.close()
            return result
        except Error as e:
            print(f"Lỗi truy vấn SQL (fetch_all): {e}")
            return []
        finally:
            if cursor:
                cursor.close()

    def fetch_one(self, query, params=None):
        """Hàm dùng chung để SELECT 1 dòng dữ liệu (ví dụ lấy mã MAX để sinh mã tự động)"""
        if not self.connect():
            return None
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, params or ())
            result = cursor.fetchone()
            cursor.close()
            return result
        except Error as e:
            print(f"Lỗi truy vấn SQL (fetch_one): {e}")
            return None
        finally:
            if cursor:
                cursor.close()

    def execute_query(self, query, params=None):
        """Hàm dùng chung để thực hiện INSERT, UPDATE, DELETE (có Commit)"""
        if not self.connect():
            return False
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, params or ())
            self.conn.commit()
            cursor.close()
            return True
        except Error as e:
            print(f"Lỗi thực thi SQL (execute_query): {e}")
            self.conn.rollback() # Hoàn tác nếu xảy ra lỗi
            return False
        finally:
            if cursor:
                cursor.close()