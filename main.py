import sys
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QMessageBox
from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox, QTableWidgetItem, QHeaderView
from PyQt6.QtCore import QDate
from PyQt6 import uic
from database import Database

class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        # Load file UI từ Qt Designer
        uic.loadUi("giaodien.ui", self)
        
        # Khởi tạo đối tượng Database
        self.db = Database()

        # Kiểm tra kết nối CSDL ngay khi khởi động
        self.check_database_connection()
        self.btnThemNHTQuick.clicked.connect(self.mo_popup_them_nha_hao_tam)
        self.btnThemNTHQuick.clicked.connect(self.mo_popup_them_nguoi_thu_huong)
        #========================================================================
        # BAT SU KIEN TAB1
        #========================================================================
        # 1. Cấu hình tự động dãn cột cho 2 bảng ở Tab 1
        self.tblChienDich.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tblPhanCong.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # 2. Gán sự kiện cho các nút bấm & click bảng ở Tab 1
        self.btnThemCD.clicked.connect(self.them_chien_dich)
        self.btnCapNhat.clicked.connect(self.cap_nhat_chien_dich)
        self.btnLamMoi.clicked.connect(self.reset_form_tab1)
        self.tblChienDich.itemClicked.connect(self.hien_thi_chi_tiet_chien_dich)

        # 3. Nạp danh sách BĐH vào ComboBox và tải danh sách chiến dịch
        self.load_cbo_bdh()
        self.reset_form_tab1()
        self.load_data_tbl_chien_dich()
        self.setup_tab_1_phan_cong_events()
        #========================================================================
        # BAT SU KIEN TAB2
        #========================================================================
        self.setup_tab_2_events()


    # =========================================================================
    # CÁC HÀM XỬ LÝ DỮ LIỆU VÀ SỰ KIỆN CHO TAB 1
    # ========================================================================= 

    def load_cbo_bdh(self):
        """Nạp danh sách Ban Điều Hành từ CSDL vào ComboBox cboBDHQuanLy"""
        query = """
            SELECT bdh.MaBDH, n.HoTen 
            FROM BAN_DIEU_HANH bdh
            JOIN NGUOI n ON bdh.CCCD = n.CCCD
        """
        ds_bdh = self.db.fetch_all(query)
        
        # Gọi trực tiếp cboBDHQuanLy
        if hasattr(self, 'cboBDHQuanLy'):
            self.cboBDHQuanLy.clear()
            for bdh in ds_bdh:
                display_text = f"{bdh['MaBDH']} - {bdh['HoTen']}"
                # Lưu Mã BDH vào UserRole để phục vụ việc lưu/sửa sau này
                self.cboBDHQuanLy.addItem(display_text, bdh['MaBDH'])

    def generate_ma_cd(self):
        """Tự động sinh Mã Chiến Dịch tiếp theo (CD001, CD002...)"""
        row = self.db.fetch_one("SELECT MaCD FROM CHIEN_DICH ORDER BY MaCD DESC LIMIT 1")
        if row and row[0]:
            last_id = str(row[0])
            try:
                num = int(last_id.replace("CD", "")) + 1
                return f"CD{num:03d}"
            except ValueError:
                return "CD001"
        return "CD001"

    def load_data_tbl_chien_dich(self):
        """Tải danh sách chiến dịch từ MySQL lên Bảng bên trái (tblChienDich)"""
        query = "SELECT MaCD, TenChienDich, LoaiChienDich, MucTieuTien, TrangThai FROM CHIEN_DICH ORDER BY MaCD DESC"
        data = self.db.fetch_all(query)
        
        self.tblChienDich.setRowCount(0)
        for row_idx, row_data in enumerate(data):
            self.tblChienDich.insertRow(row_idx)
            self.tblChienDich.setItem(row_idx, 0, QTableWidgetItem(str(row_data['MaCD'])))
            self.tblChienDich.setItem(row_idx, 1, QTableWidgetItem(str(row_data['TenChienDich'])))
            self.tblChienDich.setItem(row_idx, 2, QTableWidgetItem(str(row_data['LoaiChienDich'])))
            
            muc_tieu = f"{row_data['MucTieuTien']:,.0f}" if row_data['MucTieuTien'] else "0"
            self.tblChienDich.setItem(row_idx, 3, QTableWidgetItem(muc_tieu))
            self.tblChienDich.setItem(row_idx, 4, QTableWidgetItem(str(row_data['TrangThai'])))


    def them_chien_dich(self):
        """Xử lý sự kiện nút [Thêm CD]"""
        ma_cd = self.txtMaCD.text().strip()
        ten_cd = self.txtTenCD.text().strip()
        loai_cd = self.cboLoaiCD.currentText()
        muc_tieu = self.spnMucTieu.value()
        ngay_bd = self.dtNgayBD.date().toString("yyyy-MM-dd")
        ngay_kt = self.dtNgayKT.date().toString("yyyy-MM-dd")
        trang_thai = self.cboTrangThai.currentText()

        # Lấy MaBDH từ ô ComboBox vừa thêm
        cbo_target = getattr(self, 'cboBDHQuanLy', getattr(self, 'cboBDH', None))
        ma_bdh = cbo_target.currentData() if cbo_target else None

        if not ma_bdh:
            # Nếu chưa có bản ghi BĐH nào trong CSDL, lấy mặc định BDH001
            row_bdh = self.db.fetch_one("SELECT MaBDH FROM BAN_DIEU_HANH LIMIT 1")
            ma_bdh = row_bdh[0] if row_bdh else "BDH001"

        if not ten_cd:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng nhập Tên Chiến Dịch!")
            return

        query = """
            INSERT INTO CHIEN_DICH (MaCD, MaBDH, TenChienDich, LoaiChienDich, MucTieuTien, NgayBatDau, NgayKetThuc, TrangThai)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (ma_cd, ma_bdh, ten_cd, loai_cd, muc_tieu, ngay_bd, ngay_kt, trang_thai)

        if self.db.execute_query(query, params):
            QMessageBox.information(self, "Thành công", f"Đã thêm chiến dịch: {ten_cd}")
            self.load_data_tbl_chien_dich()
            self.reset_form_tab1()
        else:
            QMessageBox.critical(self, "Lỗi", "Không thể thêm chiến dịch! Kiểm tra kết nối CSDL hoặc kiểm tra khóa ngoại BAN_DIEU_HANH.")

    def cap_nhat_chien_dich(self):
        """Xử lý sự kiện nút [Cập nhật]"""
        ma_cd = self.txtMaCD.text().strip()
        ten_cd = self.txtTenCD.text().strip()
        loai_cd = self.cboLoaiCD.currentText()
        muc_tieu = self.spnMucTieu.value()
        ngay_bd = self.dtNgayBD.date().toString("yyyy-MM-dd")
        ngay_kt = self.dtNgayKT.date().toString("yyyy-MM-dd")
        trang_thai = self.cboTrangThai.currentText()

        cbo_target = getattr(self, 'cboBDHQuanLy', getattr(self, 'cboBDH', None))
        ma_bdh = cbo_target.currentData() if cbo_target else None

        query = """
            UPDATE CHIEN_DICH 
            SET TenChienDich = %s, LoaiChienDich = %s, MucTieuTien = %s, NgayBatDau = %s, NgayKetThuc = %s, TrangThai = %s, MaBDH = COALESCE(%s, MaBDH)
            WHERE MaCD = %s
        """
        params = (ten_cd, loai_cd, muc_tieu, ngay_bd, ngay_kt, trang_thai, ma_bdh, ma_cd)

        if self.db.execute_query(query, params):
            QMessageBox.information(self, "Thành công", f"Đã cập nhật chiến dịch {ma_cd}")
            self.load_data_tbl_chien_dich()
        else:
            QMessageBox.critical(self, "Lỗi", "Cập nhật thất bại!")

    def reset_form_tab1(self):
        """Xử lý sự kiện nút [Làm mới]"""
        self.txtMaCD.setText(self.generate_ma_cd())
        self.txtTenCD.clear()
        self.spnMucTieu.setValue(0)
        self.dtNgayBD.setDate(QDate.currentDate())
        self.dtNgayKT.setDate(QDate.currentDate().addMonths(1))
        self.tblPhanCong.setRowCount(0)

    def setup_tab_1_phan_cong_events(self):
        """Đăng ký tất cả sự kiện bắt thao tác người dùng cho Tab 1"""
        
        # 1. Bắt sự kiện chọn dòng trên bảng Chiến dịch (Bảng bên trái)
        if hasattr(self, 'tblChienDich'):
            self.tblChienDich.itemClicked.connect(self.hien_thi_chi_tiet_chien_dich)

        # 2. Bắt sự kiện đổi Vai trò trên ComboBox -> Tự lọc lại danh sách Nhân sự bên dưới
        if hasattr(self, 'cboVaiTroPhanCong'):
            self.cboVaiTroPhanCong.clear()
            self.cboVaiTroPhanCong.addItems(["Tình nguyện viên", "Kế toán", "Ban điều hành"])
            self.cboVaiTroPhanCong.currentIndexChanged.connect(self.load_cbo_nhan_su_phan_cong)

        # 3. Bắt sự kiện click 2 nút bấm Phân công và Hủy PC
        if hasattr(self, 'btnPhanCong'):
            self.btnPhanCong.clicked.connect(self.thuc_hien_phan_cong)

        if hasattr(self, 'btnHuyPhanCong'):
            self.btnHuyPhanCong.clicked.connect(self.huy_phan_cong)

        # Nạp dữ liệu mặc định ban đầu
        self.load_cbo_nhan_su_phan_cong()

    def load_cbo_nhan_su_phan_cong(self):
        """Nạp danh sách Nhân sự CHƯA ĐƯỢC PHÂN CÔNG vào chiến dịch đang chọn"""
        if not hasattr(self, 'cboVaiTroPhanCong') or not hasattr(self, 'cboNhanSuRanh'):
            return

        # Lấy Mã chiến dịch đang chọn từ bảng tblChienDich
        current_row_cd = self.tblChienDich.currentRow() if hasattr(self, 'tblChienDich') else -1
        ma_cd = self.tblChienDich.item(current_row_cd, 0).text().strip() if current_row_cd >= 0 else None

        vaitro = self.cboVaiTroPhanCong.currentText()
        query = ""
        
        # Nếu đã chọn 1 Chiến dịch, lọc bớt những nhân sự ĐÃ CÓ trong bảng PHAN_CONG_NVIEN của chiến dịch đó
        if vaitro == "Tình nguyện viên":
            query = """
                SELECT tnv.MaTNV AS MaNS, n.HoTen 
                FROM TINH_NGUYEN_VIEN tnv 
                JOIN NGUOI n ON tnv.CCCD = n.CCCD
                WHERE (%s IS NULL OR tnv.MaTNV NOT IN (
                    SELECT MaTNV FROM PHAN_CONG_NVIEN WHERE MaCD = %s AND MaTNV IS NOT NULL
                ))
            """
        elif vaitro == "Kế toán":
            query = """
                SELECT kt.MaKT AS MaNS, n.HoTen 
                FROM KE_TOAN kt 
                JOIN NGUOI n ON kt.CCCD = n.CCCD
                WHERE (%s IS NULL OR kt.MaKT NOT IN (
                    SELECT MaKT FROM PHAN_CONG_NVIEN WHERE MaCD = %s AND MaKT IS NOT NULL
                ))
            """
        elif vaitro == "Ban điều hành":
            query = """
                SELECT bdh.MaBDH AS MaNS, n.HoTen 
                FROM BAN_DIEU_HANH bdh 
                JOIN NGUOI n ON bdh.CCCD = n.CCCD
                WHERE (%s IS NULL OR bdh.MaBDH NOT IN (
                    SELECT MaBDH FROM PHAN_CONG_NVIEN WHERE MaCD = %s AND MaBDH IS NOT NULL
                ))
            """

        self.cboNhanSuRanh.clear()
        if query:
            ds_ns = self.db.fetch_all(query, (ma_cd, ma_cd))
            for ns in ds_ns:
                mans = ns['MaNS'] if isinstance(ns, dict) else ns[0]
                hoten = ns['HoTen'] if isinstance(ns, dict) else ns[1]
                self.cboNhanSuRanh.addItem(f"{mans} - {hoten}", mans)

    def hien_thi_chi_tiet_chien_dich(self, item):
        """Khi click chọn 1 dòng chiến dịch: Hiển thị thông tin + Nạp danh sách Phân công + Cập nhật ComboBox Nhân sự rảnh"""
        row_idx = item.row()
        ma_cd = self.tblChienDich.item(row_idx, 0).text().strip()

        # 1. Hiển thị thông tin Form
        query_cd = "SELECT * FROM CHIEN_DICH WHERE MaCD = %s"
        cd = self.db.fetch_all(query_cd, (ma_cd,))
        if cd:
            data = cd[0]
            self.txtMaCD.setText(str(data['MaCD']))
            self.txtTenCD.setText(str(data['TenChienDich']))
            self.cboLoaiCD.setCurrentText(str(data['LoaiChienDich']))
            
            if hasattr(self, 'spnMucTieu'):
                self.spnMucTieu.setValue(float(data['MucTieuTien']))
            elif hasattr(self, 'txtMucTieu'):
                self.txtMucTieu.setText(f"{data['MucTieuTien']:,.0f}")

            self.cboTrangThai.setCurrentText(str(data['TrangThai']))
            
            cbo_target = getattr(self, 'cboBDHQuanLy', getattr(self, 'cboBDH', None))
            if cbo_target and data.get('MaBDH'):
                idx = cbo_target.findData(data['MaBDH'])
                if idx >= 0:
                    cbo_target.setCurrentIndex(idx)

            if data.get('NgayBatDau'):
                self.dtNgayBD.setDate(QDate.fromString(str(data['NgayBatDau']), "yyyy-MM-dd"))
            if data.get('NgayKetThuc'):
                self.dtNgayKT.setDate(QDate.fromString(str(data['NgayKetThuc']), "yyyy-MM-dd"))

        # 2. Đổ danh sách Nhân sự đã phân công vào bảng bên phải
        query_pc = """
            SELECT 
                CASE 
                    WHEN pc.MaTNV IS NOT NULL THEN 'Tình nguyện viên'
                    WHEN pc.MaKT IS NOT NULL THEN 'Kế toán'
                    WHEN pc.MaBDH IS NOT NULL THEN 'Ban điều hành'
                    ELSE 'Khác'
                END AS VaiTro,
                COALESCE(pc.MaTNV, pc.MaKT, pc.MaBDH, 'N/A') AS MaNS,
                COALESCE(n_tnv.HoTen, n_kt.HoTen, n_bdh.HoTen, 'Chưa cập nhật') AS HoTen
            FROM PHAN_CONG_NVIEN pc
            LEFT JOIN TINH_NGUYEN_VIEN tnv ON pc.MaTNV = tnv.MaTNV
            LEFT JOIN NGUOI n_tnv ON tnv.CCCD = n_tnv.CCCD
            LEFT JOIN KE_TOAN kt ON pc.MaKT = kt.MaKT
            LEFT JOIN NGUOI n_kt ON kt.CCCD = n_kt.CCCD
            LEFT JOIN BAN_DIEU_HANH bdh ON pc.MaBDH = bdh.MaBDH
            LEFT JOIN NGUOI n_bdh ON bdh.CCCD = n_bdh.CCCD
            WHERE pc.MaCD = %s
        """
        ds_phan_cong = self.db.fetch_all(query_pc, (ma_cd,))
        self.tblPhanCong.setRowCount(0)
        for r_idx, r_data in enumerate(ds_phan_cong):
            self.tblPhanCong.insertRow(r_idx)
            vaitro = r_data['VaiTro'] if isinstance(r_data, dict) else r_data[0]
            mans = r_data['MaNS'] if isinstance(r_data, dict) else r_data[1]
            hoten = r_data['HoTen'] if isinstance(r_data, dict) else r_data[2]

            self.tblPhanCong.setItem(r_idx, 0, QTableWidgetItem(str(vaitro)))
            self.tblPhanCong.setItem(r_idx, 1, QTableWidgetItem(str(mans)))
            self.tblPhanCong.setItem(r_idx, 2, QTableWidgetItem(str(hoten)))

        # 3. Nạp lại ComboBox Nhân sự rảnh (chỉ lấy người CHƯA có trong danh sách phân công trên)
        self.load_cbo_nhan_su_phan_cong()

    def thuc_hien_phan_cong(self):
        """Thêm 1 bản ghi phân công nhân sự vào chiến dịch"""
        current_row_cd = self.tblChienDich.currentRow()
        if current_row_cd < 0:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng click chọn 1 chiến dịch ở bảng bên trái trước!")
            return

        ma_cd = self.tblChienDich.item(current_row_cd, 0).text().strip()
        vaitro = self.cboVaiTroPhanCong.currentText()
        ma_ns = self.cboNhanSuRanh.currentData()

        if not ma_ns:
            QMessageBox.warning(self, "Cảnh báo", "Không có nhân sự khả dụng hoặc chưa chọn nhân sự!")
            return

        cbo_bdh = getattr(self, 'cboBDHQuanLy', getattr(self, 'cboBDH', None))
        ma_bdh_quan_ly = cbo_bdh.currentData() if (cbo_bdh and cbo_bdh.currentData()) else 'BDH001'

        res = self.db.fetch_all("SELECT MaPC FROM PHAN_CONG_NVIEN ORDER BY MaPC DESC LIMIT 1")
        if res:
            last_code = res[0]['MaPC'] if isinstance(res[0], dict) else res[0][0]
            try:
                num = int(last_code.replace('PC', '')) + 1
            except ValueError:
                num = 1
        else:
            num = 1
        ma_pc = f"PC{num:03d}"

        ma_tnv = ma_ns if vaitro == "Tình nguyện viên" else None
        ma_kt = ma_ns if vaitro == "Kế toán" else None
        ma_bdh_assigned = ma_ns if vaitro == "Ban điều hành" else ma_bdh_quan_ly

        query = """
            INSERT INTO PHAN_CONG_NVIEN (MaPC, MaBDH, MaCD, MaTNV, MaKT)
            VALUES (%s, %s, %s, %s, %s)
        """
        try:
            self.db.execute_query(query, (ma_pc, ma_bdh_assigned, ma_cd, ma_tnv, ma_kt))
            QMessageBox.information(self, "Thành công", f"Đã phân công {ma_ns} vào chiến dịch {ma_cd}!")
            
            # Cập nhật lại ngay bảng phân công + lọc lại ComboBox
            self.hien_thi_chi_tiet_chien_dich(self.tblChienDich.currentItem())
        except Exception as e:
            QMessageBox.critical(self, "Lỗi CSDL", f"Không thể phân công: {e}")

    def huy_phan_cong(self):
        """Rút nhân sự được chọn khỏi chiến dịch"""
        current_row_pc = self.tblPhanCong.currentRow()
        if current_row_pc < 0:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn 1 dòng nhân sự trên bảng Phân công cần hủy!")
            return

        current_row_cd = self.tblChienDich.currentRow()
        ma_cd = self.tblChienDich.item(current_row_cd, 0).text().strip()
        ma_ns = self.tblPhanCong.item(current_row_pc, 1).text().strip()
        hoten = self.tblPhanCong.item(current_row_pc, 2).text().strip()

        reply = QMessageBox.question(
            self, "Xác nhận hủy phân công", 
            f"Bạn có chắc chắn muốn gỡ nhân sự {hoten} ({ma_ns}) khỏi chiến dịch {ma_cd}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            query = """
                DELETE FROM PHAN_CONG_NVIEN 
                WHERE MaCD = %s AND (MaTNV = %s OR MaKT = %s OR MaBDH = %s)
            """
            try:
                self.db.execute_query(query, (ma_cd, ma_ns, ma_ns, ma_ns))
                QMessageBox.information(self, "Thành công", "Đã hủy phân công nhân sự thành công!")
                
                # Refresh lại bảng phân công + trả nhân sự về ComboBox rảnh
                self.hien_thi_chi_tiet_chien_dich(self.tblChienDich.currentItem())
            except Exception as e:
                QMessageBox.critical(self, "Lỗi CSDL", f"Không thể hủy phân công: {e}")
    # =========================================================================
    # END XỬ LÝ TAB 1
    # ========================================================================= 

    # =========================================================================
    # CÁC HÀM XỬ LÝ DỮ LIỆU VÀ SỰ KIỆN CHO TAB 2
    # =========================================================================
    def setup_tab_2_events(self):
        """Kết nối sự kiện cho các control thuộc Tab 2"""
        # Nạp dữ liệu vào ComboBox Vai Trò nếu chưa có
        if hasattr(self, 'cboLoaiNhanSu'):
            self.cboLoaiNhanSu.clear()
            self.cboLoaiNhanSu.addItems(["Ban điều hành", "Kế toán", "Tình nguyện viên"])

        # Gán sự kiện cho các nút bấm
        if hasattr(self, 'btnThemNhanSu'):
            self.btnThemNhanSu.clicked.connect(self.them_nhan_su)
        if hasattr(self, 'btnSuaNhanSu'):
            self.btnSuaNhanSu.clicked.connect(self.sua_nhan_su)
        if hasattr(self, 'btnXoaNhanSu'):
            self.btnXoaNhanSu.clicked.connect(self.xoa_nhan_su)
            
        # Sự kiện click chọn dòng trên bảng tblNhanSu
        if hasattr(self, 'tblNhanSu'):
            self.tblNhanSu.itemClicked.connect(self.hien_thi_chi_tiet_nhan_su)

        # Nạp dữ liệu bảng ngay khi khởi chạy
        self.load_data_tbl_nhan_su()

    def load_data_tbl_nhan_su(self):
        """Đổ dữ liệu tổng hợp từ CSDL vào bảng tblNhanSu (7 cột)"""
        if not hasattr(self, 'tblNhanSu'):
            return

        query = """
            SELECT 
                n.CCCD,
                CASE 
                    WHEN n.LoaiNguoi = 'BanDieuHanh' THEN 'Ban điều hành'
                    WHEN n.LoaiNguoi = 'KeToan' THEN 'Kế toán'
                    WHEN n.LoaiNguoi = 'TinhNguyenVien' THEN 'Tình nguyện viên'
                    ELSE n.LoaiNguoi
                END AS VaiTro,
                COALESCE(bdh.MaBDH, kt.MaKT, tnv.MaTNV, 'N/A') AS MaDinhDanh,
                n.HoTen,
                COALESCE(n.SDT, '') AS SDT,
                COALESCE(n.Email, '') AS Email,
                COALESCE(n.DiaChi, '') AS DiaChi
            FROM NGUOI n
            LEFT JOIN BAN_DIEU_HANH bdh ON n.CCCD = bdh.CCCD
            LEFT JOIN KE_TOAN kt ON n.CCCD = kt.CCCD
            LEFT JOIN TINH_NGUYEN_VIEN tnv ON n.CCCD = tnv.CCCD
            WHERE n.LoaiNguoi IN ('BanDieuHanh', 'KeToan', 'TinhNguyenVien')
            ORDER BY n.CCCD DESC
        """
        ds_nhan_su = self.db.fetch_all(query)
        
        self.tblNhanSu.setRowCount(0)
        for r_idx, r_data in enumerate(ds_nhan_su):
            self.tblNhanSu.insertRow(r_idx)
            
            cccd = r_data['CCCD'] if isinstance(r_data, dict) else r_data[0]
            vaitro = r_data['VaiTro'] if isinstance(r_data, dict) else r_data[1]
            madanhdanh = r_data['MaDinhDanh'] if isinstance(r_data, dict) else r_data[2]
            hoten = r_data['HoTen'] if isinstance(r_data, dict) else r_data[3]
            sdt = r_data['SDT'] if isinstance(r_data, dict) else r_data[4]
            email = r_data['Email'] if isinstance(r_data, dict) else r_data[5]
            diachi = r_data['DiaChi'] if isinstance(r_data, dict) else r_data[6]

            # Đổ dữ liệu khớp thứ tự 7 cột: CCCD | Vai trò | Mã định danh | Họ tên | SDT | Email | Địa chỉ
            self.tblNhanSu.setItem(r_idx, 0, QTableWidgetItem(str(cccd)))
            self.tblNhanSu.setItem(r_idx, 1, QTableWidgetItem(str(vaitro)))
            self.tblNhanSu.setItem(r_idx, 2, QTableWidgetItem(str(madanhdanh)))
            self.tblNhanSu.setItem(r_idx, 3, QTableWidgetItem(str(hoten)))
            self.tblNhanSu.setItem(r_idx, 4, QTableWidgetItem(str(sdt)))
            self.tblNhanSu.setItem(r_idx, 5, QTableWidgetItem(str(email)))
            self.tblNhanSu.setItem(r_idx, 6, QTableWidgetItem(str(diachi)))

    def hien_thi_chi_tiet_nhan_su(self, item):
        """Hiển thị thông tin dòng được chọn lên các Input Controls"""
        row_idx = item.row()
        self.txtCCCD.setText(self.tblNhanSu.item(row_idx, 0).text())
        self.cboLoaiNhanSu.setCurrentText(self.tblNhanSu.item(row_idx, 1).text())
        self.txtHoTen.setText(self.tblNhanSu.item(row_idx, 3).text())
        self.txtSDT.setText(self.tblNhanSu.item(row_idx, 4).text())
        self.txtEmail.setText(self.tblNhanSu.item(row_idx, 5).text())
        self.txtDiaChi.setText(self.tblNhanSu.item(row_idx, 6).text())

    def tao_ma_dinh_danh_moi(self, loai_nguoi):
        """Hàm sinh Mã định danh tự động (BDHxxx, KTxxx, TNVxxx)"""
        prefix_map = {
            'BanDieuHanh': ('BDH', 'BAN_DIEU_HANH', 'MaBDH'),
            'KeToan': ('KT', 'KE_TOAN', 'MaKT'),
            'TinhNguyenVien': ('TNV', 'TINH_NGUYEN_VIEN', 'MaTNV')
        }
        prefix, table, col = prefix_map[loai_nguoi]
        query = f"SELECT {col} FROM {table} ORDER BY {col} DESC LIMIT 1"
        res = self.db.fetch_all(query)
        if res:
            last_code = res[0][col] if isinstance(res[0], dict) else res[0][0]
            try:
                num = int(last_code.replace(prefix, '')) + 1
            except ValueError:
                num = 1
        else:
            num = 1
        return f"{prefix}{num:03d}"

    def them_nhan_su(self):
        """Thêm Nhân sự mới vào bảng NGUOI và bảng Subtype tương ứng"""
        cccd = self.txtCCCD.text().strip()
        hoten = self.txtHoTen.text().strip()
        sdt = self.txtSDT.text().strip()
        email = self.txtEmail.text().strip()
        diachi = self.txtDiaChi.text().strip()
        vaitro_text = self.cboLoaiNhanSu.currentText()

        if not cccd or not hoten:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng nhập đầy đủ Số CCCD và Họ tên!")
            return

        map_loai = {
            "Ban điều hành": "BanDieuHanh",
            "Kế toán": "KeToan",
            "Tình nguyện viên": "TinhNguyenVien"
        }
        loai_nguoi = map_loai.get(vaitro_text, "TinhNguyenVien")

        # 1. Thêm vào bảng NGUOI
        query_nguoi = """
            INSERT INTO NGUOI (CCCD, HoTen, SDT, Email, DiaChi, LoaiNguoi)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        # 2. Sinh mã và thêm vào bảng Subtype
        ma_dd = self.tao_ma_dinh_danh_moi(loai_nguoi)
        
        try:
            self.db.execute_query(query_nguoi, (cccd, hoten, sdt, email, diachi, loai_nguoi))

            if loai_nguoi == 'BanDieuHanh':
                query_sub = "INSERT INTO BAN_DIEU_HANH (MaBDH, CCCD, ChucVu) VALUES (%s, %s, %s)"
                self.db.execute_query(query_sub, (ma_dd, cccd, 'Thành viên'))
            elif loai_nguoi == 'KeToan':
                query_sub = "INSERT INTO KE_TOAN (MaKT, CCCD, ViTriChuyenTrach) VALUES (%s, %s, %s)"
                self.db.execute_query(query_sub, (ma_dd, cccd, 'Kế toán viên'))
            elif loai_nguoi == 'TinhNguyenVien':
                query_sub = "INSERT INTO TINH_NGUYEN_VIEN (MaTNV, CCCD, KhuVucHoatDongChinh) VALUES (%s, %s, %s)"
                self.db.execute_query(query_sub, (ma_dd, cccd, 'Hà Nội'))

            QMessageBox.information(self, "Thành công", f"Thêm nhân sự mới thành công! Mã định danh: {ma_dd}")
            self.load_data_tbl_nhan_su()
            # Nạp lại ComboBox BĐH ở Tab 1 phòng trường hợp vừa thêm 1 BĐH mới
            if hasattr(self, 'load_cbo_bdh'):
                self.load_cbo_bdh()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi CSDL", f"Không thể thêm nhân sự: {e}")

    def sua_nhan_su(self):
        """Cập nhật thông tin Nhân sự theo CCCD"""
        cccd = self.txtCCCD.text().strip()
        hoten = self.txtHoTen.text().strip()
        sdt = self.txtSDT.text().strip()
        email = self.txtEmail.text().strip()
        diachi = self.txtDiaChi.text().strip()

        if not cccd:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn hoặc nhập Số CCCD cần sửa!")
            return

        query = """
            UPDATE NGUOI 
            SET HoTen = %s, SDT = %s, Email = %s, DiaChi = %s
            WHERE CCCD = %s
        """
        try:
            self.db.execute_query(query, (hoten, sdt, email, diachi, cccd))
            QMessageBox.information(self, "Thành công", "Cập nhật thông tin nhân sự thành công!")
            self.load_data_tbl_nhan_su()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi CSDL", f"Không thể cập nhật: {e}")

    def xoa_nhan_su(self):
        """Xóa nhân sự theo CCCD"""
        cccd = self.txtCCCD.text().strip()
        if not cccd:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn nhân sự cần xóa!")
            return

        reply = QMessageBox.question(
            self, "Xác nhận xóa", 
            f"Bạn có chắc chắn muốn xóa nhân sự có CCCD: {cccd}?\nDữ liệu liên quan ở các bảng Subtype sẽ bị xóa tự động.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            query = "DELETE FROM NGUOI WHERE CCCD = %s"
            try:
                self.db.execute_query(query, (cccd,))
                QMessageBox.information(self, "Thành công", "Đã xóa nhân sự khỏi hệ thống!")
                self.load_data_tbl_nhan_su()
                # Clear form
                self.txtCCCD.clear()
                self.txtHoTen.clear()
                self.txtSDT.clear()
                self.txtEmail.clear()
                self.txtDiaChi.clear()
            except Exception as e:
                QMessageBox.critical(self, "Lỗi CSDL", f"Không thể xóa nhân sự: {e}")

    # =========================================================================
    # END XỬ LÝ TAB 2
    # =========================================================================
    

    def check_database_connection(self):
        if self.db.connect():
            print(">>> Kết nối CSDL MySQL thành công!")
            self.db.disconnect()
        else:
            QMessageBox.critical(
                self, 
                "Lỗi CSDL", 
                "Không thể kết nối đến CSDL MySQL! Vui lòng kiểm tra lại thông số kết nối."
            )
    def mo_popup_them_nha_hao_tam(self):
        """Bật Pop-up thêm Nhà hảo tâm mới và lưu vào MySQL"""
        dialog = FormThemNhanhDialog(title="Thêm Nhà Hảo Tâm Mới", parent=self)
        
        # Nếu người dùng bấm nút "Lưu thông tin"
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            if not data["cccd"] or not data["ho_ten"]:
                QMessageBox.warning(self, "Cảnh báo", "Vui lòng nhập đầy đủ CCCD và Họ tên!")
                return

            # 1. Thêm vào bảng NGUOI
            query_nguoi = "INSERT INTO NGUOI (CCCD, HoTen, SDT, DiaChi) VALUES (%s, %s, %s, %s)"
            if self.db.execute_query(query_nguoi, (data["cccd"], data["ho_ten"], data["sdt"], data["dia_chi"])):
                
                # 2. Sinh mã NHT tự động và Thêm vào bảng NHA_HAO_TAM
                # (Ví dụ: Lấy mã NHT lớn nhất rồi +1 thành NHT005...)
                query_nht = "INSERT INTO NHA_HAO_TAM (MaNHT, CCCD) VALUES (%s, %s)"
                ma_nht_moi = "NHT_MOI" # Xử lý sinh mã ngầm
                self.db.execute_query(query_nht, (ma_nht_moi, data["cccd"]))

                QMessageBox.information(self, "Thành công", f"Đã thêm Nhà hảo tâm: {data['ho_ten']}")
                
                # 3. Nạp lại ComboBox Tab 3 và tự động chọn luôn người vừa thêm
                self.load_cbo_nha_hao_tam()
                self.cboNhaHaoTam.setCurrentText(f"{ma_nht_moi} - {data['ho_ten']}")

    def mo_popup_them_nguoi_thu_huong(self):
        """Bật Pop-up thêm Người thụ hưởng mới (Tab 4)"""
        dialog = FormThemNhanhDialog(title="Thêm Người Thụ Hưởng Mới", parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()

class FormThemNhanhDialog(QDialog):
    def __init__(self, title="Thêm đối tượng mới", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(350, 220)

        # Tạo Layout chính
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # Tạo các ô nhập liệu
        self.txtCCCD = QLineEdit()
        self.txtCCCD.setPlaceholderText("Nhập số CCCD/Mã định danh...")
        
        self.txtHoTen = QLineEdit()
        self.txtHoTen.setPlaceholderText("Nhập họ và tên...")
        
        self.txtSDT = QLineEdit()
        self.txtSDT.setPlaceholderText("Nhập số điện thoại...")

        self.txtDiaChi = QLineEdit()
        self.txtDiaChi.setPlaceholderText("Nhập địa chỉ...")

        # Đưa vào Form
        form_layout.addRow("Số CCCD:", self.txtCCCD)
        form_layout.addRow("Họ và Tên:", self.txtHoTen)
        form_layout.addRow("Số ĐT:", self.txtSDT)
        form_layout.addRow("Địa chỉ:", self.txtDiaChi)
        layout.addLayout(form_layout)

        # Nút bấm Lưu
        self.btnLuu = QPushButton("Lưu thông tin")
        self.btnLuu.clicked.connect(self.accept) # Đóng Dialog và trả về kết quả Thành công
        layout.addWidget(self.btnLuu)

    def get_data(self):
        """Hàm trả về dữ liệu người dùng đã nhập"""
        return {
            "cccd": self.txtCCCD.text().strip(),
            "ho_ten": self.txtHoTen.text().strip(),
            "sdt": self.txtSDT.text().strip(),
            "dia_chi": self.txtDiaChi.text().strip()
        }

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec())