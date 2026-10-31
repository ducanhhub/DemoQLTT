import sys
import csv
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QMessageBox,
    QApplication, QMainWindow, QTableWidgetItem, QHeaderView, QHBoxLayout, QWidget, QSpinBox, 
    QComboBox, QLabel, QFrame, QDoubleSpinBox, QTextEdit, QProgressBar, QFileDialog
)
from PyQt6.QtCore import Qt, QDate
from PyQt6 import uic
from database import Database

# =========================================================================
# 1. DIALOG THÊM NHANH NHÀ HẢO TÂM
# =========================================================================
class DialogThemNHT(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Thêm Nhanh Nhà Hảo Tâm (NHA_HAO_TAM)")
        self.setFixedSize(420, 380)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.cboLoaiNHT = QComboBox()
        self.cboLoaiNHT.addItems(["Cá nhân", "Tổ chức / Doanh nghiệp", "Ẩn danh"])
        
        self.txtTenNHT = QLineEdit()
        self.txtTenNHT.setPlaceholderText("VD: Tập đoàn VNPT / Phạm Văn Hảo Tâm...")
        
        self.txtSDT = QLineEdit()
        self.txtSDT.setPlaceholderText("09..., 08... (Nhiều SĐT phân tách bằng dấu phẩy)")
        
        self.txtEmail = QLineEdit()
        self.txtEmail.setPlaceholderText("email@example.com")
        
        self.txtMST = QLineEdit()
        self.txtMST.setPlaceholderText("0101...")

        form.addRow("Loại Nhà Hảo Tâm:", self.cboLoaiNHT)
        form.addRow("Tên Nhà Hảo Tâm / Tổ Chức *:", self.txtTenNHT)
        
        self.lblSDT = QLabel("Số Điện Thoại:")
        form.addRow(self.lblSDT, self.txtSDT)
        
        self.lblEmail = QLabel("Email:")
        form.addRow(self.lblEmail, self.txtEmail)
        
        self.lblMST = QLabel("Mã Số Thuế (Nếu có):")
        form.addRow(self.lblMST, self.txtMST)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        self.btnHuy = QPushButton("Hủy")
        self.btnThem = QPushButton("+ Thêm mới")
        self.btnThem.setStyleSheet("background-color: #00bcd4; color: white; font-weight: bold;")
        
        btn_layout.addWidget(self.btnHuy)
        btn_layout.addWidget(self.btnThem)
        layout.addLayout(btn_layout)

        self.cboLoaiNHT.currentIndexChanged.connect(self.thay_doi_loai_nht)
        self.btnHuy.clicked.connect(self.reject)
        self.btnThem.clicked.connect(self.luu_nha_hao_tam)

        self.thay_doi_loai_nht()

    def thay_doi_loai_nht(self):
        idx = self.cboLoaiNHT.currentIndex()
        if idx == 0:
            self.txtTenNHT.show()
            self.txtSDT.show(); self.lblSDT.show()
            self.txtEmail.show(); self.lblEmail.show()
            self.txtMST.hide(); self.lblMST.hide()
        elif idx == 1:
            self.txtTenNHT.show()
            self.txtSDT.show(); self.lblSDT.show()
            self.txtEmail.show(); self.lblEmail.show()
            self.txtMST.show(); self.lblMST.show()
        elif idx == 2:
            self.txtTenNHT.hide()
            self.txtSDT.hide(); self.lblSDT.hide()
            self.txtEmail.hide(); self.lblEmail.hide()
            self.txtMST.hide(); self.lblMST.hide()

    def luu_nha_hao_tam(self):
        idx = self.cboLoaiNHT.currentIndex()
        loai_str = 'CaNhan' if idx == 0 else ('ToChuc' if idx == 1 else 'AnDanh')
        
        ten = self.txtTenNHT.text().strip() if loai_str != 'AnDanh' else "Nhà hảo tâm ẩn danh"
        if not ten and loai_str != 'AnDanh':
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng nhập Tên Nhà Hảo Tâm / Tổ chức!")
            return

        sdt_raw = self.txtSDT.text().strip() if (loai_str != 'AnDanh') else ""
        email = self.txtEmail.text().strip() if (loai_str != 'AnDanh') else None
        mst = self.txtMST.text().strip() if (loai_str == 'ToChuc') else None

        try:
            res = self.db.fetch_all("SELECT MaNHT FROM NHA_HAO_TAM ORDER BY MaNHT DESC LIMIT 1")
            num = int(res[0]['MaNHT'].replace("NHT", "")) + 1 if res else 1
            ma_nht = f"NHT{num:02d}"

            q_nht = "INSERT INTO NHA_HAO_TAM (MaNHT, TenNHT, LoaiNHT, MaSoThue, Email) VALUES (%s, %s, %s, %s, %s)"
            self.db.execute_query(q_nht, (ma_nht, ten, loai_str, mst, email))

            if sdt_raw:
                sdt_list = [s.strip() for s in sdt_raw.split(",") if s.strip()]
                for sdt in sdt_list:
                    self.db.execute_query("INSERT INTO NHA_HAO_TAM_SDT (MaNHT, SDT) VALUES (%s, %s)", (ma_nht, sdt))

            QMessageBox.information(self, "Thành công", f"Đã thêm Nhà Hảo Tâm: {ten} ({ma_nht})")
            self.ma_nht_vua_them = ma_nht
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể thêm nhà hảo tâm: {e}")


# =========================================================================
# 2. DIALOG THÊM NHANH NGƯỜI THỤ HƯỞNG
# =========================================================================
class DialogThemNTH(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Thêm Nhanh Đối Tượng Khó Khăn (NGUOI_THU_HUONG)")
        self.setFixedSize(450, 480)
        self.setStyleSheet("""
            QDialog { background-color: #0b1329; color: white; font-family: Arial, sans-serif; }
            QLabel { color: #cbd5e1; font-size: 13px; font-weight: bold; }
            QLineEdit, QTextEdit { background-color: #1e293b; color: white; border: 1px solid #334155; border-radius: 6px; padding: 6px; }
            QPushButton { border-radius: 6px; font-weight: bold; padding: 8px; }
        """)

        layout = QVBoxLayout(self)

        title = QLabel("Thêm Nhanh Đối Tượng Khó Khăn\n(NGUOI_THU_HUONG)")
        title.setStyleSheet("font-size: 16px; color: #38bdf8; font-weight: bold;")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)

        self.txtHoTen = QLineEdit()
        self.txtHoTen.setPlaceholderText("VD: Bà Trần Thị Mai, Cháu Lê...")
        self.txtCCCD = QLineEdit()
        self.txtCCCD.setPlaceholderText("12 số...")
        self.txtSDT = QLineEdit()
        self.txtSDT.setPlaceholderText("035...")
        self.txtDiaChi = QLineEdit()
        self.txtDiaChi.setPlaceholderText("Thôn, Xã, Huyện, Tỉnh...")
        self.txtHoanCanh = QTextEdit()
        self.txtHoanCanh.setPlaceholderText("Mô tả mức độ thiệt hại bão lũ, hoàn cảnh...")
        self.txtHoanCanh.setMaximumHeight(90)

        form.addRow("Họ và Tên Người Thụ Hưởng *:", self.txtHoTen)
        row_id_sdt = QHBoxLayout()
        row_id_sdt.addWidget(self.txtCCCD)
        row_id_sdt.addWidget(self.txtSDT)
        form.addRow(QLabel("Số CCCD / Số Điện Thoại:"), row_id_sdt)
        form.addRow("Địa Chỉ Thực Tế Cư Trú *:", self.txtDiaChi)
        form.addRow("Hoàn Cảnh Khó Khăn Cần Cứu Trợ:", self.txtHoanCanh)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        self.btnHuy = QPushButton("Hủy")
        self.btnHuy.setStyleSheet("background-color: #334155; color: white;")
        self.btnLuu = QPushButton("+ Lưu Người Thụ Hưởng")
        self.btnLuu.setStyleSheet("background-color: #0284c7; color: white;")

        btn_layout.addWidget(self.btnHuy)
        btn_layout.addWidget(self.btnLuu)
        layout.addLayout(btn_layout)

        self.btnHuy.clicked.connect(self.reject)
        self.btnLuu.clicked.connect(self.luu_nguoi_thu_huong)

    def luu_nguoi_thu_huong(self):
        hoten = self.txtHoTen.text().strip()
        cccd = self.txtCCCD.text().strip() or None
        sdt = self.txtSDT.text().strip()
        diachi = self.txtDiaChi.text().strip()
        hoancanh = self.txtHoanCanh.toPlainText().strip()

        if not hoten or not diachi:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng nhập Họ tên và Địa chỉ cư trú!")
            return

        try:
            res = self.db.fetch_all("SELECT MaNTH FROM NGUOI_THU_HUONG ORDER BY MaNTH DESC LIMIT 1")
            num = int(res[0]['MaNTH'].replace("NTH", "")) + 1 if res else 1
            ma_nth = f"NTH{num:02d}"

            q = "INSERT INTO NGUOI_THU_HUONG (MaNTH, CCCD, HoTen, DiaChi, HoanCanhMoTa) VALUES (%s, %s, %s, %s, %s)"
            self.db.execute_query(q, (ma_nth, cccd, hoten, diachi, hoancanh))

            if sdt:
                for p in [s.strip() for s in sdt.split(",") if s.strip()]:
                    self.db.execute_query("INSERT INTO NGUOI_THU_HUONG_SDT (MaNTH, SDT) VALUES (%s, %s)", (ma_nth, p))

            QMessageBox.information(self, "Thành công", f"Đã thêm người thụ hưởng: {hoten} ({ma_nth})")
            self.ma_nth_vua_them = ma_nth
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi CSDL", f"Không thể lưu người thụ hưởng: {e}")


# =========================================================================
# 3. DIALOG BIÊN NHẬN ỦNG HỘ
# =========================================================================
class DialogBienNhan(QDialog):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("BIÊN NHẬN ỦNG HỘ TỪ THIỆN")
        self.setFixedSize(480, 520)
        self.setStyleSheet("QDialog { background-color: #0f172a; color: white; font-family: Arial; } QLabel { font-size: 13px; color: #e2e8f0; }")

        layout = QVBoxLayout(self)

        title = QLabel("BIÊN NHẬN ỦNG HỘ TỪ THIỆN")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #38bdf8; margin-top: 10px;")
        
        sub = QLabel("Hệ thống Quản lý Từ thiện Minh bạch - CharityMS")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet("color: #94a3b8; font-size: 11px;")

        ma_phieu = QLabel(f"Mã Phiếu: {data.get('MaQG', 'N/A')}")
        ma_phieu.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ma_phieu.setStyleSheet("background-color: #1e293b; color: #38bdf8; padding: 6px; border-radius: 4px; font-weight: bold; font-size: 14px;")

        layout.addWidget(title); layout.addWidget(sub); layout.addSpacing(10); layout.addWidget(ma_phieu)

        form = QFormLayout()
        form.setContentsMargins(20, 15, 20, 15)
        form.setSpacing(12)

        form.addRow("Nhà Hảo Tâm:", QLabel(str(data.get('TenNHT') or 'Nhà hảo tâm ẩn danh')))
        form.addRow("Mã Số Thuế:", QLabel(str(data.get('MaSoThue') or 'N/A')))
        form.addRow("Chiến Dịch Tiếp Nhận:", QLabel(str(data.get('TenChienDich') or 'N/A')))
        
        ht_map = {"ChuyenKhoan": "Chuyển khoản Ngân hàng", "TienMat": "Tiền mặt", "HienVat": "Hiện vật"}
        form.addRow("Hình Thức Ủng Hộ:", QLabel(ht_map.get(data.get('HinhThuc'), 'N/A')))
        form.addRow("Mã Giao Dịch Ngân Hàng:", QLabel(str(data.get('MaGiaoDichNganHang') or 'N/A')))
        
        so_tien = data.get('SoTien')
        hinh_thuc = data.get('HinhThuc')
        mo_ta_hien_vat = data.get('MoTaHienVat')

        st_val = str(mo_ta_hien_vat) if hinh_thuc == 'HienVat' or (so_tien is not None and float(so_tien) == 0) else f"{float(so_tien):,.0f} đ"
        lbl_st = QLabel(st_val)
        lbl_st.setStyleSheet("color: #4ade80; font-size: 15px; font-weight: bold;")
        form.addRow("Giá Trị / Số Tiền:", lbl_st)

        form.addRow("Ngày Tiếp Nhận:", QLabel(str(data.get('NgayQuyenGop') or 'N/A')))
        form.addRow("Kế Toán Xác Nhận:", QLabel(str(data.get('TenKT') or 'Chờ xác nhận đối soát')))
        
        lbl_tt = QLabel(str(data.get('TrangThaiDoiSoat') or 'Chờ đối soát'))
        if data.get('TrangThaiDoiSoat') == 'Đã đối soát':
            lbl_tt.setStyleSheet("color: #4ade80; font-weight: bold;")
        elif data.get('TrangThaiDoiSoat') == 'Từ chối':
            lbl_tt.setStyleSheet("color: #f87171; font-weight: bold;")
        form.addRow("Trạng Thái Đối Soát:", lbl_tt)

        layout.addLayout(form)

        btn_close = QPushButton("Đóng / In biên nhận")
        btn_close.setStyleSheet("background-color: #0284c7; color: white; padding: 10px; font-weight: bold; border-radius: 4px; font-size: 13px;")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)


# =========================================================================
# 4. DIALOG BIÊN BẢN GIẢI NGÂN
# =========================================================================
class DialogBienBanGiaiNgan(QDialog):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("BIÊN BẢN BÀN GIAO KINH PHÍ / HÀNG CỨU TRỢ")
        self.setFixedSize(540, 580)
        self.setStyleSheet("QDialog { background-color: #090d16; color: white; font-family: Arial; } QLabel { font-size: 13px; color: #cbd5e1; }")

        layout = QVBoxLayout(self)

        title_header = QLabel("CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM\nĐộc lập - Tự do - Hạnh phúc")
        title_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_header.setStyleSheet("font-size: 11px; font-weight: bold; color: #94a3b8;")

        title = QLabel("BIÊN BẢN BÀN GIAO KINH PHÍ / HÀNG CỨU TRỢ THIỆN NGUYỆN")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 15px; font-weight: bold; color: #f8fafc; margin-top: 5px;")

        ma_phieu = QLabel(f"Mã Phiếu Giải Ngân: {data.get('MaGN', 'N/A')} (Căn cứ HS: {data.get('MaHS', 'N/A')})")
        ma_phieu.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ma_phieu.setStyleSheet("color: #38bdf8; font-weight: bold; font-size: 13px; margin-bottom: 10px;")

        layout.addWidget(title_header); layout.addWidget(title); layout.addWidget(ma_phieu)

        form = QFormLayout()
        form.setContentsMargins(20, 5, 20, 5)
        form.setSpacing(10)

        lbl_cd = QLabel(str(data.get('TenChienDich') or 'N/A'))
        lbl_cd.setStyleSheet("color: #38bdf8; font-weight: bold;")
        form.addRow("Chiến Dịch:", lbl_cd)

        lbl_nth = QLabel(str(data.get('TenNTH') or 'N/A'))
        lbl_nth.setStyleSheet("color: #f8fafc; font-weight: bold; font-size: 14px;")
        form.addRow("Người Thụ Hưởng Tiếp Nhận:", lbl_nth)

        cccd_sdt = f"{data.get('CCCD_NTH') or 'N/A'}  •  {data.get('SDT_NTH') or 'N/A'}"
        form.addRow("Số CCCD / ĐT:", QLabel(cccd_sdt))
        form.addRow("Địa Chỉ Cứu Trợ:", QLabel(str(data.get('DiaChi_NTH') or 'N/A')))

        loai_hinh_map = {"TienMat": "Tiền mặt cứu trợ trực tiếp", "HienVat": "Hiện vật cứu trợ"}
        form.addRow("Hình Thức Trao Phát:", QLabel(loai_hinh_map.get(data.get('LoaiHinh'), 'N/A')))

        st_gn = data.get('SoTienGiaiNgan') or 0
        lbl_st = QLabel(f"{float(st_gn):,.0f} đ")
        lbl_st.setStyleSheet("color: #4ade80; font-size: 16px; font-weight: bold;")
        form.addRow("Số Tiền Giải Ngân Thực Tế:", lbl_st)

        form.addRow("Hiện Vật Bàn Giao:", QLabel(str(data.get('MoTaHienVatTrao') or 'Không có')))
        form.addRow("Ngày Thực Hiện:", QLabel(str(data.get('NgayThucHien') or 'N/A')))

        layout.addLayout(form)
        layout.addSpacing(15)

        sign_layout = QHBoxLayout()
        sign_layout.addWidget(self.create_sign_box("NGƯỜI THỤ HƯỞNG", "(Ký & Ghi rõ họ tên)", data.get('TenNTH')))
        sign_layout.addWidget(self.create_sign_box("TNV THỰC ĐỊA", f"({data.get('MaTNV') or 'TNV'})", data.get('TenTNV')))
        sign_layout.addWidget(self.create_sign_box("KẾ TOÁN CHI TIỀN", f"({data.get('MaKT') or 'KT'})", data.get('TenKT')))
        sign_layout.addWidget(self.create_sign_box("BAN ĐIỀU HÀNH", "(Phê duyệt)", data.get('MaBDH') or 'BDH'))
        layout.addLayout(sign_layout)

        btn_layout = QHBoxLayout()
        btn_close = QPushButton("Đóng")
        btn_close.setStyleSheet("background-color: #334155; color: white; padding: 8px;")
        btn_close.clicked.connect(self.accept)

        btn_print = QPushButton("In Biên Bản Trao Nhận")
        btn_print.setStyleSheet("background-color: #10b981; color: white; font-weight: bold; padding: 8px;")
        btn_print.clicked.connect(self.accept)

        btn_layout.addWidget(btn_close)
        btn_layout.addWidget(btn_print)
        layout.addLayout(btn_layout)

    def create_sign_box(self, title, sub, name):
        box = QVBoxLayout()
        lbl_t = QLabel(title)
        lbl_t.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_t.setStyleSheet("font-size: 10px; font-weight: bold; color: #f8fafc;")

        lbl_s = QLabel(sub)
        lbl_s.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_s.setStyleSheet("font-size: 9px; color: #64748b;")

        lbl_n = QLabel(str(name or ''))
        lbl_n.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_n.setStyleSheet("font-size: 11px; font-weight: bold; color: #e2e8f0; margin-top: 25px;")

        box.addWidget(lbl_t); box.addWidget(lbl_s); box.addWidget(lbl_n)
        w = QWidget(); w.setLayout(box)
        return w


# =========================================================================
# 5. MAIN APP
# =========================================================================
class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("giaodien.ui", self)
        self.db = Database()

        self.check_database_connection()

        if hasattr(self, 'btnThemNHTQuick'): self.btnThemNHTQuick.clicked.connect(self.mo_popup_them_nht)
        if hasattr(self, 'btnThemNTHQuick'): self.btnThemNTHQuick.clicked.connect(self.mo_popup_them_nguoi_thu_huong)

        # Tab 1
        self.tblChienDich.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tblPhanCong.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.btnThemCD.clicked.connect(self.them_chien_dich)
        self.btnCapNhat.clicked.connect(self.cap_nhat_chien_dich)
        self.btnLamMoi.clicked.connect(self.reset_form_tab1)
        if hasattr(self, 'btnXoa'): self.btnXoa.clicked.connect(self.xoa_chien_dich)
        self.tblChienDich.itemClicked.connect(self.hien_thi_chi_tiet_chien_dich)

        self.load_cbo_bdh()
        self.reset_form_tab1()
        self.load_data_tbl_chien_dich()
        self.setup_tab_1_phan_cong_events()

        # Tab 2, 3, 4
        self.setup_tab_2_events()
        self.setup_tab_3_events()
        self.setup_tab_4_events()

        # Tab 5
        self.setup_tab_5_events()

        # Đồng bộ dữ liệu khi người dùng chuyển đổi Tab
        if hasattr(self, 'tabWidget'):
            self.tabWidget.currentChanged.connect(self.on_tab_changed)


    # =========================================================================
    # SỰ KIỆN CHUYỂN TAB ĐỒNG BỘ DỮ LIỆU
    # =========================================================================
    def on_tab_changed(self, index):
        if index == 4:  # Tab 5
            self.cap_nhat_tab_5()


    # =========================================================================
    # TAB 1
    # ========================================================================= 
    def load_cbo_bdh(self):
        if not hasattr(self, 'cboBDHQuanLy'): return
        ds_bdh = self.db.fetch_all("SELECT bdh.MaBDH, COALESCE(n.HoTen, 'Thành viên BDH') AS HoTen FROM NGUOI_DIEU_HANH bdh LEFT JOIN NGUOI n ON bdh.CCCD = n.CCCD")
        self.cboBDHQuanLy.clear()
        for bdh in ds_bdh:
            self.cboBDHQuanLy.addItem(f"{bdh['MaBDH']} - {bdh['HoTen']}", bdh['MaBDH'])

    def generate_ma_cd(self):
        row = self.db.fetch_one("SELECT MaCD FROM CHIEN_DICH ORDER BY MaCD DESC LIMIT 1")
        if row and row[0]:
            try:
                return f"CD{int(str(row[0]).replace('CD', '')) + 1:02d}"
            except ValueError:
                return "CD01"
        return "CD01"

    def load_data_tbl_chien_dich(self):
        data = self.db.fetch_all("SELECT MaCD, TenChienDich, LoaiChienDich, MucTieuTien, TrangThai FROM CHIEN_DICH ORDER BY MaCD DESC")
        self.tblChienDich.setRowCount(0)
        for row_idx, row_data in enumerate(data):
            self.tblChienDich.insertRow(row_idx)
            self.tblChienDich.setItem(row_idx, 0, QTableWidgetItem(str(row_data['MaCD'])))
            self.tblChienDich.setItem(row_idx, 1, QTableWidgetItem(str(row_data['TenChienDich'])))
            self.tblChienDich.setItem(row_idx, 2, QTableWidgetItem(str(row_data['LoaiChienDich'])))
            self.tblChienDich.setItem(row_idx, 3, QTableWidgetItem(f"{row_data['MucTieuTien']:,.0f}" if row_data['MucTieuTien'] else "0"))
            self.tblChienDich.setItem(row_idx, 4, QTableWidgetItem(str(row_data['TrangThai'])))

    def them_chien_dich(self):
        ma_cd, ten_cd, loai_cd = self.txtMaCD.text().strip(), self.txtTenCD.text().strip(), self.cboLoaiCD.currentText()
        muc_tieu, ngay_bd, ngay_kt, trang_thai = self.spnMucTieu.value(), self.dtNgayBD.date().toString("yyyy-MM-dd"), self.dtNgayKT.date().toString("yyyy-MM-dd"), self.cboTrangThai.currentText()
        ma_bdh = self.cboBDHQuanLy.currentData() or 'BDH01'

        if not ten_cd: return
        q = "INSERT INTO CHIEN_DICH (MaCD, MaBDH, TenChienDich, LoaiChienDich, MucTieuTien, NgayBatDau, NgayKetThuc, TrangThai) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        if self.db.execute_query(q, (ma_cd, ma_bdh, ten_cd, loai_cd, muc_tieu, ngay_bd, ngay_kt, trang_thai)):
            self.load_data_tbl_chien_dich(); self.reset_form_tab1()
            self.load_cbo_chien_dich_tab3(); self.load_cbo_chien_dich_tab4(); self.load_cbo_filter_tab5()

    def cap_nhat_chien_dich(self):
        ma_cd, ten_cd, loai_cd = self.txtMaCD.text().strip(), self.txtTenCD.text().strip(), self.cboLoaiCD.currentText()
        muc_tieu, ngay_bd, ngay_kt, trang_thai = self.spnMucTieu.value(), self.dtNgayBD.date().toString("yyyy-MM-dd"), self.dtNgayKT.date().toString("yyyy-MM-dd"), self.cboTrangThai.currentText()
        ma_bdh = self.cboBDHQuanLy.currentData()

        q = "UPDATE CHIEN_DICH SET TenChienDich = %s, LoaiChienDich = %s, MucTieuTien = %s, NgayBatDau = %s, NgayKetThuc = %s, TrangThai = %s, MaBDH = COALESCE(%s, MaBDH) WHERE MaCD = %s"
        if self.db.execute_query(q, (ten_cd, loai_cd, muc_tieu, ngay_bd, ngay_kt, trang_thai, ma_bdh, ma_cd)):
            self.load_data_tbl_chien_dich()

    def xoa_chien_dich(self):
        ma_cd = self.txtMaCD.text().strip()
        if ma_cd and QMessageBox.question(self, "Xác nhận", f"Xóa chiến dịch {ma_cd}?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            self.db.execute_query("DELETE FROM THAM_GIA WHERE MaCD = %s", (ma_cd,))
            self.db.execute_query("DELETE FROM GIA_NHAP WHERE MaCD = %s", (ma_cd,))
            if self.db.execute_query("DELETE FROM CHIEN_DICH WHERE MaCD = %s", (ma_cd,)):
                self.load_data_tbl_chien_dich(); self.reset_form_tab1()

    def reset_form_tab1(self):
        self.txtMaCD.setText(self.generate_ma_cd()); self.txtTenCD.clear(); self.spnMucTieu.setValue(0)
        self.dtNgayBD.setDate(QDate.currentDate()); self.dtNgayKT.setDate(QDate.currentDate().addMonths(1))
        self.tblPhanCong.setRowCount(0)
        if hasattr(self, 'labelCD'): self.labelCD.setText("Chưa chọn chiến dịch")

    def setup_tab_1_phan_cong_events(self):
        self.tblChienDich.itemClicked.connect(self.hien_thi_chi_tiet_chien_dich)
        if hasattr(self, 'cboVaiTroPhanCong'):
            self.cboVaiTroPhanCong.clear(); self.cboVaiTroPhanCong.addItems(["Tình nguyện viên", "Kế toán"])
            self.cboVaiTroPhanCong.currentIndexChanged.connect(self.load_cbo_nhan_su_phan_cong)
        if hasattr(self, 'btnPhanCong'): self.btnPhanCong.clicked.connect(self.thuc_hien_phan_cong)
        if hasattr(self, 'btnHuyPhanCong'): self.btnHuyPhanCong.clicked.connect(self.huy_phan_cong)
        self.load_cbo_nhan_su_phan_cong()

    def load_cbo_nhan_su_phan_cong(self):
        if not hasattr(self, 'cboVaiTroPhanCong') or not hasattr(self, 'cboNhanSuRanh'): return
        current_row_cd = self.tblChienDich.currentRow()
        ma_cd = self.tblChienDich.item(current_row_cd, 0).text().strip() if current_row_cd >= 0 else None
        vaitro = self.cboVaiTroPhanCong.currentText()
        
        q = """
            SELECT tnv.MaTNV AS MaNS, n.HoTen FROM TINH_NGUYEN_VIEN tnv JOIN NGUOI n ON tnv.CCCD = n.CCCD
            WHERE (%s IS NULL OR tnv.MaTNV NOT IN (SELECT MaTNV FROM THAM_GIA WHERE MaCD = %s))
        """ if vaitro == "Tình nguyện viên" else """
            SELECT kt.MaKT AS MaNS, n.HoTen FROM KE_TOAN kt JOIN NGUOI n ON kt.CCCD = n.CCCD
            WHERE (%s IS NULL OR kt.MaKT NOT IN (SELECT MaKT FROM GIA_NHAP WHERE MaCD = %s))
        """
        self.cboNhanSuRanh.clear()
        for ns in self.db.fetch_all(q, (ma_cd, ma_cd)):
            self.cboNhanSuRanh.addItem(f"{ns['MaNS']} - {ns['HoTen']}", ns['MaNS'])

    def hien_thi_chi_tiet_chien_dich(self, item):
        ma_cd = self.tblChienDich.item(item.row(), 0).text().strip()
        cd = self.db.fetch_all("SELECT * FROM CHIEN_DICH WHERE MaCD = %s", (ma_cd,))
        if cd:
            d = cd[0]
            self.txtMaCD.setText(str(d['MaCD'])); self.txtTenCD.setText(str(d['TenChienDich'])); self.cboLoaiCD.setCurrentText(str(d['LoaiChienDich']))
            if hasattr(self, 'labelCD'): self.labelCD.setText(f"{d['MaCD']} - {d['TenChienDich']}")
            if hasattr(self, 'spnMucTieu'): self.spnMucTieu.setValue(float(d['MucTieuTien']))
            self.cboTrangThai.setCurrentText(str(d['TrangThai']))
            if hasattr(self, 'cboBDHQuanLy') and d.get('MaBDH'):
                idx = self.cboBDHQuanLy.findData(d['MaBDH'])
                if idx >= 0: self.cboBDHQuanLy.setCurrentIndex(idx)

        q = """
            SELECT 'Tình nguyện viên' AS VaiTro, tg.MaTNV AS MaNS, n.HoTen FROM THAM_GIA tg JOIN TINH_NGUYEN_VIEN tnv ON tg.MaTNV = tnv.MaTNV JOIN NGUOI n ON tnv.CCCD = n.CCCD WHERE tg.MaCD = %s
            UNION ALL
            SELECT 'Kế toán' AS VaiTro, gn.MaKT AS MaNS, n.HoTen FROM GIA_NHAP gn JOIN KE_TOAN kt ON gn.MaKT = kt.MaKT JOIN NGUOI n ON kt.CCCD = n.CCCD WHERE gn.MaCD = %s
        """
        self.tblPhanCong.setRowCount(0)
        for r_idx, r_data in enumerate(self.db.fetch_all(q, (ma_cd, ma_cd))):
            self.tblPhanCong.insertRow(r_idx)
            self.tblPhanCong.setItem(r_idx, 0, QTableWidgetItem(str(r_data['VaiTro'])))
            self.tblPhanCong.setItem(r_idx, 1, QTableWidgetItem(str(r_data['MaNS'])))
            self.tblPhanCong.setItem(r_idx, 2, QTableWidgetItem(str(r_data['HoTen'])))

            btn_xoa = QPushButton("Xóa")
            btn_xoa.setStyleSheet("background-color: #e53935; color: white; border-radius: 3px;")
            btn_xoa.clicked.connect(lambda checked, v=r_data['VaiTro'], m=r_data['MaNS'], h=r_data['HoTen']: self.go_nhan_su_truc_tiep(v, m, h))
            c = QWidget(); l = QHBoxLayout(); l.addWidget(btn_xoa); l.setContentsMargins(0,0,0,0); c.setLayout(l)
            self.tblPhanCong.setCellWidget(r_idx, 3, c)

        self.load_cbo_nhan_su_phan_cong()

    def go_nhan_su_truc_tiep(self, vaitro, ma_ns, hoten):
        current_row_cd = self.tblChienDich.currentRow()
        if current_row_cd < 0: return
        ma_cd = self.tblChienDich.item(current_row_cd, 0).text().strip()
        q = "DELETE FROM THAM_GIA WHERE MaCD = %s AND MaTNV = %s" if vaitro == "Tình nguyện viên" else "DELETE FROM GIA_NHAP WHERE MaCD = %s AND MaKT = %s"
        if self.db.execute_query(q, (ma_cd, ma_ns)):
            self.hien_thi_chi_tiet_chien_dich(self.tblChienDich.currentItem())

    def thuc_hien_phan_cong(self):
        current_row_cd = self.tblChienDich.currentRow()
        if current_row_cd < 0: return
        ma_cd = self.tblChienDich.item(current_row_cd, 0).text().strip()
        vaitro, ma_ns = self.cboVaiTroPhanCong.currentText(), self.cboNhanSuRanh.currentData()
        ma_bdh = self.cboBDHQuanLy.currentData() or 'BDH01'

        if not ma_ns: return
        q = "INSERT INTO THAM_GIA (MaBDH, MaCD, MaTNV) VALUES (%s, %s, %s)" if vaitro == "Tình nguyện viên" else "INSERT INTO GIA_NHAP (MaBDH, MaCD, MaKT) VALUES (%s, %s, %s)"
        if self.db.execute_query(q, (ma_bdh, ma_cd, ma_ns)):
            self.hien_thi_chi_tiet_chien_dich(self.tblChienDich.currentItem())

    def huy_phan_cong(self):
        row = self.tblPhanCong.currentRow()
        if row >= 0: self.go_nhan_su_truc_tiep(self.tblPhanCong.item(row, 0).text(), self.tblPhanCong.item(row, 1).text(), self.tblPhanCong.item(row, 2).text())


    # =========================================================================
    # TAB 2
    # =========================================================================
    def setup_tab_2_events(self):
        if hasattr(self, 'cboLoaiNhanSu'):
            self.cboLoaiNhanSu.clear(); self.cboLoaiNhanSu.addItems(["Người điều hành", "Kế toán / Thủ quỹ ", "Tình nguyện viên "])
            self.cboLoaiNhanSu.currentIndexChanged.connect(self.thay_doi_giao_dien_subtype)

        if hasattr(self, 'spnNamBatDau'): self.spnNamBatDau.setRange(2000, 2100); self.spnNamBatDau.setValue(2026)
        if hasattr(self, 'spnNamKetThuc'): self.spnNamKetThuc.setRange(2000, 2100); self.spnNamKetThuc.setValue(2026)

        if hasattr(self, 'cboLoc'):
            self.cboLoc.clear(); self.cboLoc.addItems(["Tất cả Vai trò", "Người điều hành", "Kế toán", "Tình nguyện viên"])
            self.cboLoc.currentIndexChanged.connect(self.loc_nhan_su)

        if hasattr(self, 'txtLoc'): self.txtLoc.textChanged.connect(self.loc_nhan_su)
        if hasattr(self, 'btnThemNhanSu'): self.btnThemNhanSu.clicked.connect(self.them_nhan_su)
        if hasattr(self, 'btnSuaNhanSu'): self.btnSuaNhanSu.clicked.connect(self.sua_nhan_su)
        if hasattr(self, 'btnXoaNhanSu'): self.btnXoaNhanSu.clicked.connect(self.xoa_nhan_su)
        btn_lm = getattr(self, 'btnLamMoiForm', None)
        if btn_lm: btn_lm.clicked.connect(self.reset_form_tab2)

        if hasattr(self, 'tblNhanSu'): self.tblNhanSu.itemClicked.connect(self.hien_thi_chi_tiet_nhan_su)
        self.load_data_tbl_nhan_su(); self.thay_doi_giao_dien_subtype()

    def reset_form_tab2(self):
        for attr in ['txtCCCD', 'txtHoTen', 'txtSDT', 'txtEmail', 'txtDiaChi', 'txtChucVu', 'txtQuyenHan', 'txtTrinhDo', 'txtViTri', 'txtKVHoatDong']:
            if hasattr(self, attr): getattr(self, attr).clear()
        if hasattr(self, 'cboLoaiNhanSu'): self.cboLoaiNhanSu.setCurrentIndex(0)
        if hasattr(self, 'tblNhanSu'): self.tblNhanSu.clearSelection()

    def thay_doi_giao_dien_subtype(self):
        if hasattr(self, 'stackedSubtype'): self.stackedSubtype.setCurrentIndex(self.cboLoaiNhanSu.currentIndex())

    def load_data_tbl_nhan_su(self, keyword="", vaitro_filter="Tất cả Vai trò"):
        if not hasattr(self, 'tblNhanSu'): return
        query = """
            SELECT n.CCCD,
                CASE WHEN bdh.MaBDH IS NOT NULL THEN 'Người điều hành' WHEN kt.MaKT IS NOT NULL THEN 'Kế toán' WHEN tnv.MaTNV IS NOT NULL THEN 'Tình nguyện viên' ELSE 'Khác' END AS VaiTro,
                COALESCE(bdh.MaBDH, kt.MaKT, tnv.MaTNV, 'N/A') AS MaDinhDanh, n.HoTen, COALESCE(sdt_group.SDT, '') AS SDT, COALESCE(n.Email, '') AS Email, COALESCE(n.DiaChi, '') AS DiaChi
            FROM NGUOI n
            LEFT JOIN NGUOI_DIEU_HANH bdh ON n.CCCD = bdh.CCCD
            LEFT JOIN KE_TOAN kt ON n.CCCD = kt.CCCD
            LEFT JOIN TINH_NGUYEN_VIEN tnv ON n.CCCD = tnv.CCCD
            LEFT JOIN (SELECT CCCD, GROUP_CONCAT(SDT SEPARATOR ', ') AS SDT FROM NGUOI_DUNG_SDT GROUP BY CCCD) sdt_group ON n.CCCD = sdt_group.CCCD
            WHERE (bdh.MaBDH IS NOT NULL OR kt.MaKT IS NOT NULL OR tnv.MaTNV IS NOT NULL)
        """
        params = []
        if "điều hành" in vaitro_filter.lower(): query += " AND bdh.MaBDH IS NOT NULL"
        elif "kế toán" in vaitro_filter.lower(): query += " AND kt.MaKT IS NOT NULL"
        elif "tình nguyện" in vaitro_filter.lower(): query += " AND tnv.MaTNV IS NOT NULL"

        if keyword:
            query += " AND (n.CCCD LIKE %s OR n.HoTen LIKE %s OR sdt_group.SDT LIKE %s OR bdh.MaBDH LIKE %s OR kt.MaKT LIKE %s OR tnv.MaTNV LIKE %s)"
            params.extend([f"%{keyword}%"] * 6)

        query += " ORDER BY n.CCCD DESC"
        ds = self.db.fetch_all(query, tuple(params) if params else None)
        self.tblNhanSu.setRowCount(0)
        for r_idx, r in enumerate(ds):
            self.tblNhanSu.insertRow(r_idx)
            for c_idx, key in enumerate(['CCCD', 'VaiTro', 'MaDinhDanh', 'HoTen', 'SDT', 'Email', 'DiaChi']):
                self.tblNhanSu.setItem(r_idx, c_idx, QTableWidgetItem(str(r[key])))

    def loc_nhan_su(self):
        kw = self.txtLoc.text().strip() if hasattr(self, 'txtLoc') else ""
        vt = self.cboLoc.currentText() if hasattr(self, 'cboLoc') else "Tất cả Vai trò"
        self.load_data_tbl_nhan_su(kw, vt)

    def hien_thi_chi_tiet_nhan_su(self, item):
        row = item.row()
        cccd, vaitro = self.tblNhanSu.item(row, 0).text(), self.tblNhanSu.item(row, 1).text()
        self.txtCCCD.setText(cccd); self.txtHoTen.setText(self.tblNhanSu.item(row, 3).text())
        self.txtSDT.setText(self.tblNhanSu.item(row, 4).text()); self.txtEmail.setText(self.tblNhanSu.item(row, 5).text()); self.txtDiaChi.setText(self.tblNhanSu.item(row, 6).text())

        if "điều hành" in vaitro.lower():
            self.cboLoaiNhanSu.setCurrentIndex(0)
            d = self.db.fetch_all("SELECT * FROM NGUOI_DIEU_HANH WHERE CCCD = %s", (cccd,))
            if d:
                if hasattr(self, 'txtChucVu'): self.txtChucVu.setText(str(d[0].get('ChucVu') or ''))
                if hasattr(self, 'txtQuyenHan'): self.txtQuyenHan.setText(str(d[0].get('QuyenHanCapDuyet') or ''))
        elif "kế toán" in vaitro.lower():
            self.cboLoaiNhanSu.setCurrentIndex(1)
            d = self.db.fetch_all("SELECT * FROM KE_TOAN WHERE CCCD = %s", (cccd,))
            if d:
                if hasattr(self, 'txtTrinhDo'): self.txtTrinhDo.setText(str(d[0].get('TrinhDoChuyenMon') or ''))
                if hasattr(self, 'txtViTri'): self.txtViTri.setText(str(d[0].get('ViTriChuyenTrach') or ''))
        elif "tình nguyện" in vaitro.lower():
            self.cboLoaiNhanSu.setCurrentIndex(2)

    def tao_ma_dinh_danh_moi(self, loai):
        m = {'BanDieuHanh': ('BDH', 'NGUOI_DIEU_HANH', 'MaBDH'), 'KeToan': ('KT', 'KE_TOAN', 'MaKT'), 'TinhNguyenVien': ('TNV', 'TINH_NGUYEN_VIEN', 'MaTNV')}
        p, t, c = m[loai]
        res = self.db.fetch_all(f"SELECT {c} FROM {t} ORDER BY {c} DESC LIMIT 1")
        return f"{p}{int(res[0][c].replace(p, '')) + 1:02d}" if res else f"{p}01"

    def them_nhan_su(self):
        cccd, hoten, sdt, email, diachi = self.txtCCCD.text().strip(), self.txtHoTen.text().strip(), self.txtSDT.text().strip(), self.txtEmail.text().strip(), self.txtDiaChi.text().strip()
        idx = self.cboLoaiNhanSu.currentIndex()
        if not cccd or not hoten: return

        try:
            self.db.execute_query("INSERT INTO NGUOI (CCCD, HoTen, Email, DiaChi) VALUES (%s, %s, %s, %s)", (cccd, hoten, email, diachi))
            if sdt:
                for p in [s.strip() for s in sdt.split(",") if s.strip()]:
                    self.db.execute_query("INSERT INTO NGUOI_DUNG_SDT (CCCD, SDT) VALUES (%s, %s)", (cccd, p))

            if idx == 0:
                m = self.tao_ma_dinh_danh_moi('BanDieuHanh')
                self.db.execute_query("INSERT INTO NGUOI_DIEU_HANH (MaBDH, CCCD, ChucVu, QuyenHanCapDuyet, NamBatDau) VALUES (%s, %s, %s, %s, %s)", (m, cccd, self.txtChucVu.text().strip(), self.txtQuyenHan.text().strip(), self.spnNamBatDau.value()))
            elif idx == 1:
                m = self.tao_ma_dinh_danh_moi('KeToan')
                self.db.execute_query("INSERT INTO KE_TOAN (MaKT, CCCD, TrinhDoChuyenMon, ViTriChuyenTrach) VALUES (%s, %s, %s, %s)", (m, cccd, self.txtTrinhDo.text().strip(), self.txtViTri.text().strip()))
            elif idx == 2:
                m = self.tao_ma_dinh_danh_moi('TinhNguyenVien')
                self.db.execute_query("INSERT INTO TINH_NGUYEN_VIEN (MaTNV, CCCD) VALUES (%s, %s)", (m, cccd))
                for kv in [k.strip() for k in self.txtKVHoatDong.text().split(",") if k.strip()]:
                    self.db.execute_query("INSERT INTO TINH_NGUYEN_VIEN_KVHDONG (MaTNV, KVHoatDong) VALUES (%s, %s)", (m, kv))

            QMessageBox.information(self, "Thành công", "Đã thêm nhân sự!")
            self.load_data_tbl_nhan_su(); self.load_cbo_bdh(); self.reset_form_tab2()
            self.load_cbo_bdh_tab4(); self.load_cbo_kt_tab4(); self.load_cbo_tnv_tab4()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", str(e))

    def sua_nhan_su(self):
        cccd, hoten, sdt, email, diachi = self.txtCCCD.text().strip(), self.txtHoTen.text().strip(), self.txtSDT.text().strip(), self.txtEmail.text().strip(), self.txtDiaChi.text().strip()
        if not cccd: return
        self.db.execute_query("UPDATE NGUOI SET HoTen = %s, Email = %s, DiaChi = %s WHERE CCCD = %s", (hoten, email, diachi, cccd))
        self.db.execute_query("DELETE FROM NGUOI_DUNG_SDT WHERE CCCD = %s", (cccd,))
        if sdt:
            for p in [s.strip() for s in sdt.split(",") if s.strip()]:
                self.db.execute_query("INSERT INTO NGUOI_DUNG_SDT (CCCD, SDT) VALUES (%s, %s)", (cccd, p))
        QMessageBox.information(self, "Thành công", "Đã cập nhật nhân sự!")
        self.load_data_tbl_nhan_su()

    def xoa_nhan_su(self):
        cccd = self.txtCCCD.text().strip()
        if cccd and self.db.execute_query("DELETE FROM NGUOI WHERE CCCD = %s", (cccd,)):
            QMessageBox.information(self, "Thành công", "Đã xóa nhân sự!")
            self.load_data_tbl_nhan_su(); self.reset_form_tab2()


    # =========================================================================
    # TAB 3: TIẾP NHẬN QUYÊN GÓP & ĐỐI SOÁT
    # =========================================================================
    def setup_tab_3_events(self):
        self.load_cbo_nha_hao_tam(); self.load_cbo_chien_dich_tab3(); self.load_cbo_ke_toan_tab3()

        if hasattr(self, 'cboHinhThuc'):
            self.cboHinhThuc.clear(); self.cboHinhThuc.addItems(["Chuyển khoản", "Tiền mặt", "Hiện vật"])
            self.cboHinhThuc.currentIndexChanged.connect(self.xuly_thay_doi_hinh_thuc)

        if hasattr(self, 'cboLocHinhThuc'):
            self.cboLocHinhThuc.clear(); self.cboLocHinhThuc.addItems(["Tất cả hình thức", "Chuyển khoản", "Tiền mặt", "Hiện vật"])
            self.cboLocHinhThuc.currentIndexChanged.connect(self.loc_quyen_gop)

        if hasattr(self, 'cboLocTrangThai'):
            self.cboLocTrangThai.clear(); self.cboLocTrangThai.addItems(["Tất cả trạng thái", "Chờ đối soát", "Đã đối soát", "Từ chối"])
            self.cboLocTrangThai.currentIndexChanged.connect(self.loc_quyen_gop)

        if hasattr(self, 'txtTimKiemQG'): self.txtTimKiemQG.textChanged.connect(self.loc_quyen_gop)

        btn_xuat = getattr(self, 'btnXuatBienNhan', getattr(self, 'btnXuatBienNhanDienTu', None))
        if btn_xuat: btn_xuat.clicked.connect(self.xuat_bien_nhan)

        btn_lm = getattr(self, 'btnLamMoiQG', None)
        if btn_lm: btn_lm.clicked.connect(self.reset_form_tab3)

        if hasattr(self, 'btnLuuQG'): self.btnLuuQG.clicked.connect(self.luu_quyen_gop_moi)
        if hasattr(self, 'btnDoiSoat'): self.btnDoiSoat.clicked.connect(self.xac_nhan_doi_soat)
        if hasattr(self, 'btnTuChoi'): self.btnTuChoi.clicked.connect(self.tu_choi_giao_dich)

        if hasattr(self, 'tblQuyenGop'): self.tblQuyenGop.itemClicked.connect(self.hien_thi_chi_tiet_quyen_gop)

        self.reset_form_tab3(); self.load_data_tbl_quyen_gop()

    def xuly_thay_doi_hinh_thuc(self):
        ht = self.cboHinhThuc.currentText()
        if ht == "Chuyển khoản":
            if hasattr(self, 'txtMaGiaoDich'): self.txtMaGiaoDich.setEnabled(True)
            if hasattr(self, 'txtGhiChuQG'): self.txtGhiChuQG.clear(); self.txtGhiChuQG.setEnabled(False)
        elif ht == "Tiền mặt":
            if hasattr(self, 'txtMaGiaoDich'): self.txtMaGiaoDich.clear(); self.txtMaGiaoDich.setEnabled(False)
            if hasattr(self, 'txtGhiChuQG'): self.txtGhiChuQG.clear(); self.txtGhiChuQG.setEnabled(False)
        elif ht == "Hiện vật":
            if hasattr(self, 'txtMaGiaoDich'): self.txtMaGiaoDich.clear(); self.txtMaGiaoDich.setEnabled(False)
            if hasattr(self, 'txtGhiChuQG'): self.txtGhiChuQG.setEnabled(True)

    def reset_form_tab3(self):
        if hasattr(self, 'txtMaGiaoDich'): self.txtMaGiaoDich.clear()
        if hasattr(self, 'txtGhiChuQG'): self.txtGhiChuQG.clear()
        if hasattr(self, 'spnSoTienQG'): self.spnSoTienQG.setValue(0)
        
        if hasattr(self, 'btnLuuQG'): self.btnLuuQG.setEnabled(True)
        if hasattr(self, 'btnDoiSoat'): self.btnDoiSoat.setEnabled(False)
        if hasattr(self, 'btnTuChoi'): self.btnTuChoi.setEnabled(False)

        if hasattr(self, 'tblQuyenGop'): self.tblQuyenGop.clearSelection()
        self.xuly_thay_doi_hinh_thuc()

    def load_cbo_nha_hao_tam(self):
        if not hasattr(self, 'cboNhaHaoTam'): return
        ds = self.db.fetch_all("SELECT MaNHT, TenNHT, LoaiNHT FROM NHA_HAO_TAM ORDER BY MaNHT ASC")
        self.cboNhaHaoTam.clear()
        for d in ds:
            self.cboNhaHaoTam.addItem(f"{d['MaNHT']} - {d['TenNHT'] or 'Nhà hảo tâm ẩn danh'} [{d['LoaiNHT']}]", d['MaNHT'])

    def load_cbo_chien_dich_tab3(self):
        if not hasattr(self, 'cboChienDich'): return
        ds = self.db.fetch_all("SELECT MaCD, TenChienDich FROM CHIEN_DICH WHERE TrangThai = 'Đang thực hiện'")
        self.cboChienDich.clear()
        for d in ds:
            self.cboChienDich.addItem(f"{d['MaCD']} - {d['TenChienDich']}", d['MaCD'])

    def load_cbo_ke_toan_tab3(self):
        if not hasattr(self, 'cboKeToanDuyet'): return
        ds = self.db.fetch_all("SELECT kt.MaKT, n.HoTen FROM KE_TOAN kt JOIN NGUOI n ON kt.CCCD = n.CCCD")
        self.cboKeToanDuyet.clear()
        for d in ds:
            self.cboKeToanDuyet.addItem(f"{d['MaKT']} - {d['HoTen']}", d['MaKT'])

    def load_data_tbl_quyen_gop(self, keyword="", ht_filter="Tất cả hình thức", tt_filter="Tất cả trạng thái"):
        if not hasattr(self, 'tblQuyenGop'): return
        q = """
            SELECT qg.MaQG, COALESCE(nht.TenNHT, 'Nhà hảo tâm ẩn danh') AS TenNHT, cd.TenChienDich, 
                   qg.HinhThuc, qg.SoTien, qg.MoTaHienVat, qg.NgayQuyenGop, qg.MaGiaoDichNganHang, qg.TrangThaiDoiSoat
            FROM QUYEN_GOP qg
            JOIN NHA_HAO_TAM nht ON qg.MaNHT = nht.MaNHT
            JOIN CHIEN_DICH cd ON qg.MaCD = cd.MaCD
            WHERE 1=1
        """
        params = []
        if ht_filter != "Tất cả hình thức":
            q += " AND qg.HinhThuc = %s"
            params.append({"Chuyển khoản": "ChuyenKhoan", "Tiền mặt": "TienMat", "Hiện vật": "HienVat"}.get(ht_filter, ht_filter))

        if tt_filter != "Tất cả trạng thái":
            q += " AND qg.TrangThaiDoiSoat = %s"
            params.append(tt_filter)

        if keyword:
            q += " AND (qg.MaQG LIKE %s OR nht.TenNHT LIKE %s OR cd.TenChienDich LIKE %s OR qg.MaGiaoDichNganHang LIKE %s)"
            params.extend([f"%{keyword}%"] * 4)

        q += " ORDER BY qg.NgayQuyenGop DESC"
        ds = self.db.fetch_all(q, tuple(params) if params else None)

        self.tblQuyenGop.setRowCount(0)
        for r_idx, r in enumerate(ds):
            self.tblQuyenGop.insertRow(r_idx)
            self.tblQuyenGop.setItem(r_idx, 0, QTableWidgetItem(str(r['MaQG'])))
            self.tblQuyenGop.setItem(r_idx, 1, QTableWidgetItem(str(r['TenNHT'])))
            self.tblQuyenGop.setItem(r_idx, 2, QTableWidgetItem(str(r['TenChienDich'])))
            self.tblQuyenGop.setItem(r_idx, 3, QTableWidgetItem(str(r['HinhThuc'])))
            
            st_str = str(r['MoTaHienVat']) if r['HinhThuc'] == 'HienVat' or (r['SoTien'] is not None and float(r['SoTien']) == 0) else f"{float(r['SoTien']):,.0f} đ"
            self.tblQuyenGop.setItem(r_idx, 4, QTableWidgetItem(st_str))
            self.tblQuyenGop.setItem(r_idx, 5, QTableWidgetItem(str(r['NgayQuyenGop'])))
            self.tblQuyenGop.setItem(r_idx, 6, QTableWidgetItem(str(r['MaGiaoDichNganHang'] or 'N/A')))
            self.tblQuyenGop.setItem(r_idx, 7, QTableWidgetItem(str(r['TrangThaiDoiSoat'])))

    def loc_quyen_gop(self):
        kw = self.txtTimKiemQG.text().strip() if hasattr(self, 'txtTimKiemQG') else ""
        ht = self.cboLocHinhThuc.currentText() if hasattr(self, 'cboLocHinhThuc') else "Tất cả hình thức"
        tt = self.cboLocTrangThai.currentText() if hasattr(self, 'cboLocTrangThai') else "Tất cả trạng thái"
        self.load_data_tbl_quyen_gop(kw, ht, tt)

    def hien_thi_chi_tiet_quyen_gop(self, item):
        row_idx = item.row()
        ma_qg = self.tblQuyenGop.item(row_idx, 0).text()

        data = self.db.fetch_all("SELECT * FROM QUYEN_GOP WHERE MaQG = %s", (ma_qg,))
        if data:
            d = data[0]
            if hasattr(self, 'cboNhaHaoTam'):
                idx = self.cboNhaHaoTam.findData(d['MaNHT'])
                if idx >= 0: self.cboNhaHaoTam.setCurrentIndex(idx)
            if hasattr(self, 'cboChienDich'):
                idx = self.cboChienDich.findData(d['MaCD'])
                if idx >= 0: self.cboChienDich.setCurrentIndex(idx)

            ht_map_rev = {"ChuyenKhoan": "Chuyển khoản", "TienMat": "Tiền mặt", "HienVat": "Hiện vật"}
            self.cboHinhThuc.setCurrentText(ht_map_rev.get(d['HinhThuc'], "Chuyển khoản"))

            if hasattr(self, 'spnSoTienQG'): self.spnSoTienQG.setValue(float(d['SoTien']))
            if hasattr(self, 'txtMaGiaoDich'): self.txtMaGiaoDich.setText(str(d.get('MaGiaoDichNganHang') or ''))
            if hasattr(self, 'txtGhiChuQG'): self.txtGhiChuQG.setText(str(d.get('MoTaHienVat') or ''))

            # Khóa nút bấm khi giao dịch đã ĐỐI SOÁT hoặc TỪ CHỐI
            trang_thai_doi_soat = str(d.get('TrangThaiDoiSoat'))
            if hasattr(self, 'btnLuuQG'): self.btnLuuQG.setEnabled(False)

            if trang_thai_doi_soat == 'Chờ đối soát':
                if hasattr(self, 'btnDoiSoat'): self.btnDoiSoat.setEnabled(True)
                if hasattr(self, 'btnTuChoi'): self.btnTuChoi.setEnabled(True)
            else:
                if hasattr(self, 'btnDoiSoat'): self.btnDoiSoat.setEnabled(False)
                if hasattr(self, 'btnTuChoi'): self.btnTuChoi.setEnabled(False)

    def luu_quyen_gop_moi(self):
        ma_nht, ma_cd, ht_text = self.cboNhaHaoTam.currentData(), self.cboChienDich.currentData(), self.cboHinhThuc.currentText()
        so_tien = self.spnSoTienQG.value() if hasattr(self, 'spnSoTienQG') else 0
        ma_gd = self.txtMaGiaoDich.text().strip() if hasattr(self, 'txtMaGiaoDich') else None
        ghi_chu = self.txtGhiChuQG.text().strip() if hasattr(self, 'txtGhiChuQG') else None

        if not ma_nht or not ma_cd: return
        ht_val = {"Chuyển khoản": "ChuyenKhoan", "Tiền mặt": "TienMat", "Hiện vật": "HienVat"}[ht_text]

        try:
            res = self.db.fetch_all("SELECT MaQG FROM QUYEN_GOP ORDER BY MaQG DESC LIMIT 1")
            num = int(res[0]['MaQG'].replace("QG", "")) + 1 if res else 1
            ma_qg = f"QG{num:02d}"

            q = "INSERT INTO QUYEN_GOP (MaQG, MaNHT, MaCD, HinhThuc, SoTien, MoTaHienVat, MaGiaoDichNganHang, TrangThaiDoiSoat) VALUES (%s, %s, %s, %s, %s, %s, %s, 'Chờ đối soát')"
            self.db.execute_query(q, (ma_qg, ma_nht, ma_cd, ht_val, so_tien, ghi_chu, ma_gd))
            QMessageBox.information(self, "Thành công", f"Đã ghi nhận Quyên góp mới! Mã: {ma_qg}")
            self.load_data_tbl_quyen_gop(); self.reset_form_tab3()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", str(e))

    def xac_nhan_doi_soat(self):
        row_idx = self.tblQuyenGop.currentRow()
        if row_idx < 0: return
        ma_qg = self.tblQuyenGop.item(row_idx, 0).text().strip()
        ma_kt = self.cboKeToanDuyet.currentData() if hasattr(self, 'cboKeToanDuyet') else 'KT01'
        if self.db.execute_query("UPDATE QUYEN_GOP SET TrangThaiDoiSoat = 'Đã đối soát', MaKT = %s WHERE MaQG = %s", (ma_kt, ma_qg)):
            QMessageBox.information(self, "Thành công", f"Đã đối soát phiếu {ma_qg}!")
            self.load_data_tbl_quyen_gop(); self.reset_form_tab3()

    def tu_choi_giao_dich(self):
        row_idx = self.tblQuyenGop.currentRow()
        if row_idx < 0: return
        ma_qg = self.tblQuyenGop.item(row_idx, 0).text().strip()
        if self.db.execute_query("UPDATE QUYEN_GOP SET TrangThaiDoiSoat = 'Từ chối' WHERE MaQG = %s", (ma_qg,)):
            QMessageBox.information(self, "Thành công", f"Đã từ chối giao dịch {ma_qg}!")
            self.load_data_tbl_quyen_gop(); self.reset_form_tab3()

    def mo_popup_them_nht(self):
        dlg = DialogThemNHT(self.db, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.load_cbo_nha_hao_tam()
            if hasattr(dlg, 'ma_nht_vua_them'):
                idx = self.cboNhaHaoTam.findData(dlg.ma_nht_vua_them)
                if idx >= 0: self.cboNhaHaoTam.setCurrentIndex(idx)

    def xuat_bien_nhan(self):
        row_idx = self.tblQuyenGop.currentRow()
        if row_idx < 0: return
        ma_qg = self.tblQuyenGop.item(row_idx, 0).text().strip()
        q = """
            SELECT qg.MaQG, nht.TenNHT, nht.MaSoThue, cd.TenChienDich, qg.HinhThuc, qg.SoTien, 
                   qg.MoTaHienVat, qg.NgayQuyenGop, qg.MaGiaoDichNganHang, qg.TrangThaiDoiSoat, kt_n.HoTen AS TenKT
            FROM QUYEN_GOP qg
            LEFT JOIN NHA_HAO_TAM nht ON qg.MaNHT = nht.MaNHT
            LEFT JOIN CHIEN_DICH cd ON qg.MaCD = cd.MaCD
            LEFT JOIN KE_TOAN kt ON qg.MaKT = kt.MaKT
            LEFT JOIN NGUOI kt_n ON kt.CCCD = kt_n.CCCD
            WHERE qg.MaQG = %s
        """
        ds = self.db.fetch_all(q, (ma_qg,))
        if ds: DialogBienNhan(ds[0], self).exec()


    # =========================================================================
    # TAB 4: HỒ SƠ CỨU TRỢ & GIẢI NGÂN
    # =========================================================================
    def setup_tab_4_events(self):
        if hasattr(self, 'tblHoSo'): self.tblHoSo.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        if hasattr(self, 'tblGiaiNgan'): self.tblGiaiNgan.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        self.load_cbo_nth_tab4()
        self.load_cbo_chien_dich_tab4()
        self.load_cbo_bdh_tab4()
        self.load_cbo_kt_tab4()
        self.load_cbo_tnv_tab4()
        self.load_cbo_ho_so_da_duyet_tab4()

        if hasattr(self, 'cboLoaiHinh'):
            self.cboLoaiHinh.clear(); self.cboLoaiHinh.addItems(["Tiền mặt", "Hiện vật"])
            self.cboLoaiHinh.currentIndexChanged.connect(self.xuly_thay_doi_loai_hinh_gn)

        if hasattr(self, 'cboLocHS'):
            self.cboLocHS.clear(); self.cboLocHS.addItems(["Tất cả hồ sơ", "Chờ duyệt", "Đã duyệt", "Từ chối"])
            self.cboLocHS.currentIndexChanged.connect(self.loc_ho_so)

        if hasattr(self, 'cboChienDichHS'):
            self.cboChienDichHS.currentIndexChanged.connect(self.thay_doi_chien_dich_hs)

        if hasattr(self, 'tblHoSo'): 
            self.tblHoSo.itemClicked.connect(self.hien_thi_chi_tiet_ho_so)

        if hasattr(self, 'cboHoSoDaDuyet'):
            self.cboHoSoDaDuyet.currentIndexChanged.connect(self.thay_doi_ho_so_da_duyet)

        if hasattr(self, 'btnTaoHS'): self.btnTaoHS.clicked.connect(self.tao_ho_so_cuu_tro)
        if hasattr(self, 'btnDuyetHS'): self.btnDuyetHS.clicked.connect(self.duyet_ho_so_cuu_tro)
        if hasattr(self, 'btnTuChoiHS'): self.btnTuChoiHS.clicked.connect(self.tu_choi_ho_so_cuu_tro)
        if hasattr(self, 'btnHuyHS'): self.btnHuyHS.clicked.connect(self.huy_ho_so_cuu_tro)
        if hasattr(self, 'btnLamMoiHS'): self.btnLamMoiHS.clicked.connect(self.reset_form_tab4)

        if hasattr(self, 'btnXanNhanGiaiNgan'):
            self.btnXanNhanGiaiNgan.clicked.connect(self.xac_nhan_giai_ngan)

        self.reset_form_tab4()
        self.load_data_tbl_ho_so()
        self.load_data_tbl_giai_ngan()

    def load_cbo_nth_tab4(self):
        if not hasattr(self, 'cboNguoiThuHuong'): return
        ds = self.db.fetch_all("SELECT MaNTH, HoTen FROM NGUOI_THU_HUONG ORDER BY MaNTH ASC")
        self.cboNguoiThuHuong.clear()
        for d in ds: self.cboNguoiThuHuong.addItem(f"{d['MaNTH']} - {d['HoTen']}", d['MaNTH'])

    def load_cbo_chien_dich_tab4(self):
        if not hasattr(self, 'cboChienDichHS'): return
        ds = self.db.fetch_all("SELECT MaCD, TenChienDich FROM CHIEN_DICH WHERE TrangThai = 'Đang thực hiện'")
        self.cboChienDichHS.clear()
        for d in ds: self.cboChienDichHS.addItem(f"{d['MaCD']} - {d['TenChienDich']}", d['MaCD'])

    def load_cbo_bdh_tab4(self):
        if not hasattr(self, 'cboBDHDuyet'): return
        ds = self.db.fetch_all("SELECT bdh.MaBDH, n.HoTen FROM NGUOI_DIEU_HANH bdh JOIN NGUOI n ON bdh.CCCD = n.CCCD")
        self.cboBDHDuyet.clear()
        for d in ds: self.cboBDHDuyet.addItem(f"{d['MaBDH']} - {d['HoTen']}", d['MaBDH'])

    def load_cbo_kt_tab4(self):
        if not hasattr(self, 'cboKTChi'): return
        ds = self.db.fetch_all("SELECT kt.MaKT, n.HoTen FROM KE_TOAN kt JOIN NGUOI n ON kt.CCCD = n.CCCD")
        self.cboKTChi.clear()
        for d in ds: self.cboKTChi.addItem(f"{d['MaKT']} - {d['HoTen']}", d['MaKT'])

    def load_cbo_tnv_tab4(self):
        if not hasattr(self, 'cboTNVPhat'): return
        ds = self.db.fetch_all("SELECT tnv.MaTNV, n.HoTen FROM TINH_NGUYEN_VIEN tnv JOIN NGUOI n ON tnv.CCCD = n.CCCD")
        self.cboTNVPhat.clear()
        for d in ds: self.cboTNVPhat.addItem(f"{d['MaTNV']} - {d['HoTen']}", d['MaTNV'])

    def load_cbo_ho_so_da_duyet_tab4(self):
        if not hasattr(self, 'cboHoSoDaDuyet'): return
        q = """
            SELECT hs.MaHS, nth.HoTen AS TenNTH, hs.SoTienDeXuat
            FROM HO_SO_CUU_TRO hs
            JOIN NGUOI_THU_HUONG nth ON hs.MaNTH = nth.MaNTH
            WHERE hs.TrangThaiDuyet = 'Đã duyệt'
            ORDER BY hs.MaHS DESC
        """
        ds = self.db.fetch_all(q)
        self.cboHoSoDaDuyet.clear()
        for d in ds:
            self.cboHoSoDaDuyet.addItem(f"{d['MaHS']} - {d['TenNTH']} ({float(d['SoTienDeXuat']):,.0f} đ)", d['MaHS'])

    def reset_form_tab4(self):
        if hasattr(self, 'spnSoTienDeXuat'): self.spnSoTienDeXuat.setValue(0)
        if hasattr(self, 'txtHienVatDeXuat'): self.txtHienVatDeXuat.clear()
        if hasattr(self, 'cboTrangThaiHS'): self.cboTrangThaiHS.setCurrentText("Chờ duyệt")

        if hasattr(self, 'btnTaoHS'): self.btnTaoHS.setEnabled(True)
        if hasattr(self, 'btnDuyetHS'): self.btnDuyetHS.setEnabled(False)
        if hasattr(self, 'btnTuChoiHS'): self.btnTuChoiHS.setEnabled(False)
        if hasattr(self, 'btnHuyHS'): self.btnHuyHS.setEnabled(False)

        if hasattr(self, 'tblHoSo'): self.tblHoSo.clearSelection()

    def tinh_ngan_kho_chien_dich(self, ma_cd):
        q_thu_tien = """
            SELECT COALESCE(SUM(SoTien), 0) AS TongThu 
            FROM QUYEN_GOP 
            WHERE MaCD = %s AND TrangThaiDoiSoat = 'Đã đối soát' AND HinhThuc != 'HienVat'
        """
        res_thu = self.db.fetch_all(q_thu_tien, (ma_cd,))
        tong_thu = float(res_thu[0]['TongThu']) if res_thu else 0.0

        q_chi_tien = """
            SELECT COALESCE(SUM(gn.SoTienGiaiNgan), 0) AS TongChi 
            FROM GIAI_NGAN_PHAT_HANG gn
            JOIN HO_SO_CUU_TRO hs ON gn.MaHS = hs.MaHS
            WHERE hs.MaCD = %s AND gn.LoaiHinh = 'TienMat'
        """
        res_chi = self.db.fetch_all(q_chi_tien, (ma_cd,))
        tong_chi = float(res_chi[0]['TongChi']) if res_chi else 0.0

        so_du_tien = tong_thu - tong_chi

        q_hv_nhan = """
            SELECT MoTaHienVat 
            FROM QUYEN_GOP 
            WHERE MaCD = %s AND TrangThaiDoiSoat = 'Đã đối soát' AND HinhThuc = 'HienVat'
        """
        res_hv_nhan = self.db.fetch_all(q_hv_nhan, (ma_cd,))
        hv_nhan_list = [r['MoTaHienVat'] for r in res_hv_nhan if r.get('MoTaHienVat')]

        return tong_thu, tong_chi, so_du_tien, hv_nhan_list

    def cap_nhat_ngan_kho_ui(self, ma_cd):
        if not ma_cd:
            if hasattr(self, 'txtSoTienConLai'): self.txtSoTienConLai.setText("Chưa có")
            if hasattr(self, 'cboHienVatConLai'): self.cboHienVatConLai.clear()
            return

        tong_thu, tong_chi, so_du_tien, ds_hv = self.tinh_ngan_kho_chien_dich(ma_cd)

        if hasattr(self, 'txtSoTienConLai'):
            if tong_thu == 0:
                st_str, style = "Chưa có quyên góp", "color: #eab308; font-weight: bold;"
            elif so_du_tien <= 0:
                st_str, style = "0 đ (Hết quỹ)", "color: #f87171; font-weight: bold;"
            else:
                st_str, style = f"{so_du_tien:,.0f} đ", "color: #4ade80; font-weight: bold;"

            if isinstance(self.txtSoTienConLai, (QLineEdit, QLabel)):
                self.txtSoTienConLai.setText(st_str)
                self.txtSoTienConLai.setStyleSheet(style)

        if hasattr(self, 'cboHienVatConLai'):
            self.cboHienVatConLai.clear()
            if ds_hv:
                for hv_item in ds_hv: self.cboHienVatConLai.addItem(str(hv_item))
            else:
                self.cboHienVatConLai.addItem("Không có hiện vật tồn")

    def thay_doi_chien_dich_hs(self):
        ma_cd = self.cboChienDichHS.currentData()
        self.cap_nhat_ngan_kho_ui(ma_cd)

    def hien_thi_chi_tiet_ho_so(self, item):
        ma_hs = self.tblHoSo.item(item.row(), 0).text().strip()
        data = self.db.fetch_all("SELECT * FROM HO_SO_CUU_TRO WHERE MaHS = %s", (ma_hs,))
        if data:
            d = data[0]
            if hasattr(self, 'cboNguoiThuHuong'):
                idx = self.cboNguoiThuHuong.findData(d['MaNTH'])
                if idx >= 0: self.cboNguoiThuHuong.setCurrentIndex(idx)

            if hasattr(self, 'cboChienDichHS'):
                idx = self.cboChienDichHS.findData(d['MaCD'])
                if idx >= 0: self.cboChienDichHS.setCurrentIndex(idx)

            if hasattr(self, 'spnSoTienDeXuat'): self.spnSoTienDeXuat.setValue(float(d['SoTienDeXuat']))

            if hasattr(self, 'cboBDHDuyet') and d.get('MaBDH'):
                idx = self.cboBDHDuyet.findData(d['MaBDH'])
                if idx >= 0: self.cboBDHDuyet.setCurrentIndex(idx)

            if hasattr(self, 'cboTrangThaiHS'): self.cboTrangThaiHS.setCurrentText(str(d['TrangThaiDuyet']))

            if hasattr(self, 'btnTaoHS'): self.btnTaoHS.setEnabled(False)
            if hasattr(self, 'btnDuyetHS'): self.btnDuyetHS.setEnabled(True)
            if hasattr(self, 'btnTuChoiHS'): self.btnTuChoiHS.setEnabled(True)
            if hasattr(self, 'btnHuyHS'): self.btnHuyHS.setEnabled(True)

            self.cap_nhat_ngan_kho_ui(d['MaCD'])

    def thay_doi_ho_so_da_duyet(self):
        ma_hs = self.cboHoSoDaDuyet.currentData()
        if not ma_hs:
            self.cap_nhat_ngan_kho_ui(None)
            return
        
        q = "SELECT hs.SoTienDeXuat, hs.MaCD FROM HO_SO_CUU_TRO hs WHERE hs.MaHS = %s"
        data = self.db.fetch_all(q, (ma_hs,))
        if data:
            d = data[0]
            if hasattr(self, 'spnSoTienGN'):
                self.spnSoTienGN.setValue(float(d['SoTienDeXuat']))
            self.cap_nhat_ngan_kho_ui(d['MaCD'])

    def load_data_tbl_ho_so(self, tt_filter="Tất cả hồ sơ"):
        if not hasattr(self, 'tblHoSo'): return
        q = """
            SELECT hs.MaHS, nth.HoTen AS TenNTH, cd.TenChienDich, hs.SoTienDeXuat, 
                   COALESCE(bdh_n.HoTen, 'Chưa kiểm') AS TenBDH, hs.TrangThaiDuyet
            FROM HO_SO_CUU_TRO hs
            JOIN NGUOI_THU_HUONG nth ON hs.MaNTH = nth.MaNTH
            JOIN CHIEN_DICH cd ON hs.MaCD = cd.MaCD
            LEFT JOIN NGUOI_DIEU_HANH bdh ON hs.MaBDH = bdh.MaBDH
            LEFT JOIN NGUOI bdh_n ON bdh.CCCD = bdh_n.CCCD
            WHERE 1=1
        """
        params = []
        if tt_filter != "Tất cả hồ sơ":
            q += " AND hs.TrangThaiDuyet = %s"
            params.append(tt_filter)

        q += " ORDER BY hs.MaHS DESC"
        ds = self.db.fetch_all(q, tuple(params) if params else None)

        self.tblHoSo.setRowCount(0)
        for r_idx, r in enumerate(ds):
            self.tblHoSo.insertRow(r_idx)
            self.tblHoSo.setItem(r_idx, 0, QTableWidgetItem(str(r['MaHS'])))
            self.tblHoSo.setItem(r_idx, 1, QTableWidgetItem(str(r['TenNTH'])))
            self.tblHoSo.setItem(r_idx, 2, QTableWidgetItem(str(r['TenChienDich'])))
            self.tblHoSo.setItem(r_idx, 3, QTableWidgetItem(f"{float(r['SoTienDeXuat']):,.0f} đ"))
            self.tblHoSo.setItem(r_idx, 4, QTableWidgetItem(str(r['TenBDH'])))
            self.tblHoSo.setItem(r_idx, 5, QTableWidgetItem(str(r['TrangThaiDuyet'])))

    def loc_ho_so(self):
        tt = self.cboLocHS.currentText() if hasattr(self, 'cboLocHS') else "Tất cả hồ sơ"
        self.load_data_tbl_ho_so(tt)

    def tao_ho_so_cuu_tro(self):
        ma_nth, ma_cd, so_tien, ma_bdh = self.cboNguoiThuHuong.currentData(), self.cboChienDichHS.currentData(), self.spnSoTienDeXuat.value(), self.cboBDHDuyet.currentData()
        if not ma_nth or not ma_cd: return

        try:
            res = self.db.fetch_all("SELECT MaHS FROM HO_SO_CUU_TRO ORDER BY MaHS DESC LIMIT 1")
            ma_hs = f"HS{int(res[0]['MaHS'].replace('HS', '')) + 1:02d}" if res else "HS01"

            q = "INSERT INTO HO_SO_CUU_TRO (MaHS, MaNTH, MaCD, MaBDH, NgayNop, SoTienDeXuat, TrangThaiDuyet) VALUES (%s, %s, %s, %s, CURRENT_DATE(), %s, 'Chờ duyệt')"
            self.db.execute_query(q, (ma_hs, ma_nth, ma_cd, ma_bdh, so_tien))
            QMessageBox.information(self, "Thành công", f"Đã tạo hồ sơ cứu trợ mới: {ma_hs}")
            self.load_data_tbl_ho_so(); self.reset_form_tab4()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi CSDL", str(e))

    def duyet_ho_so_cuu_tro(self):
        row_idx = self.tblHoSo.currentRow()
        if row_idx < 0: return
        ma_hs = self.tblHoSo.item(row_idx, 0).text().strip()
        ma_bdh = self.cboBDHDuyet.currentData() or 'BDH01'

        if self.db.execute_query("UPDATE HO_SO_CUU_TRO SET TrangThaiDuyet = 'Đã duyệt', MaBDH = %s WHERE MaHS = %s", (ma_bdh, ma_hs)):
            QMessageBox.information(self, "Thành công", f"Đã duyệt hồ sơ {ma_hs}!")
            self.load_data_tbl_ho_so(); self.load_cbo_ho_so_da_duyet_tab4(); self.reset_form_tab4()

    def tu_choi_ho_so_cuu_tro(self):
        row_idx = self.tblHoSo.currentRow()
        if row_idx < 0: return
        ma_hs = self.tblHoSo.item(row_idx, 0).text().strip()
        ma_bdh = self.cboBDHDuyet.currentData() or 'BDH01'

        if self.db.execute_query("UPDATE HO_SO_CUU_TRO SET TrangThaiDuyet = 'Từ chối', MaBDH = %s WHERE MaHS = %s", (ma_bdh, ma_hs)):
            QMessageBox.information(self, "Thành công", f"Đã từ chối hồ sơ {ma_hs}!")
            self.load_data_tbl_ho_so(); self.load_cbo_ho_so_da_duyet_tab4(); self.reset_form_tab4()

    def huy_ho_so_cuu_tro(self):
        row_idx = self.tblHoSo.currentRow()
        if row_idx < 0: return
        ma_hs = self.tblHoSo.item(row_idx, 0).text().strip()

        if QMessageBox.question(self, "Xác nhận xóa", f"Hủy/Xóa hồ sơ {ma_hs}?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            if self.db.execute_query("DELETE FROM HO_SO_CUU_TRO WHERE MaHS = %s", (ma_hs,)):
                self.load_data_tbl_ho_so(); self.load_cbo_ho_so_da_duyet_tab4(); self.reset_form_tab4()

    def xuly_thay_doi_loai_hinh_gn(self):
        lh = self.cboLoaiHinh.currentText()
        if lh == "Tiền mặt":
            if hasattr(self, 'spnSoTienGN'): self.spnSoTienGN.setEnabled(True)
            if hasattr(self, 'txtHienVatGN'): self.txtHienVatGN.clear(); self.txtHienVatGN.setEnabled(False)
        else:
            if hasattr(self, 'spnSoTienGN'): self.spnSoTienGN.setValue(0); self.spnSoTienGN.setEnabled(False)
            if hasattr(self, 'txtHienVatGN'): self.txtHienVatGN.setEnabled(True)

    def xac_nhan_giai_ngan(self):
        ma_hs = self.cboHoSoDaDuyet.currentData()
        lh_text = self.cboLoaiHinh.currentText()
        lh_val = 'TienMat' if lh_text == 'Tiền mặt' else 'HienVat'
        ma_kt = self.cboKTChi.currentData()
        ma_tnv = self.cboTNVPhat.currentData()
        so_tien = self.spnSoTienGN.value() if lh_val == 'TienMat' else 0
        hien_vat = self.txtHienVatGN.text().strip() if lh_val == 'HienVat' else None

        if not ma_hs:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn Hồ sơ đã duyệt để giải ngân!")
            return

        data_hs = self.db.fetch_all("SELECT MaCD FROM HO_SO_CUU_TRO WHERE MaHS = %s", (ma_hs,))
        if data_hs:
            ma_cd = data_hs[0]['MaCD']
            _, _, so_du_tien, _ = self.tinh_ngan_kho_chien_dich(ma_cd)

            if lh_val == 'TienMat' and so_tien > so_du_tien:
                QMessageBox.warning(
                    self, "Cảnh báo Ngân khố",
                    f"Không đủ ngân sách tiền mặt để giải ngân!\n\n"
                    f"- Số tiền giải ngân đề xuất: {so_tien:,.0f} đ\n"
                    f"- Quỹ tiền còn lại của Chiến dịch: {so_du_tien:,.0f} đ\n\n"
                    f"Vui lòng điều chỉnh lại số tiền hoặc đối soát thêm đợt quyên góp mới!"
                )
                return

        try:
            res = self.db.fetch_all("SELECT MaGN FROM GIAI_NGAN_PHAT_HANG ORDER BY MaGN DESC LIMIT 1")
            ma_gn = f"GN{int(res[0]['MaGN'].replace('GN', '')) + 1:02d}" if res else "GN01"

            q = "INSERT INTO GIAI_NGAN_PHAT_HANG (MaGN, MaHS, MaKT, MaTNV, LoaiHinh, SoTienGiaiNgan, MoTaHienVatTrao, NgayThucHien) VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_DATE())"
            self.db.execute_query(q, (ma_gn, ma_hs, ma_kt, ma_tnv, lh_val, so_tien, hien_vat))
            
            QMessageBox.information(self, "Thành công", f"Đã giải ngân thành công! Mã phiếu GN: {ma_gn}")
            self.load_data_tbl_giai_ngan()
            self.thay_doi_ho_so_da_duyet()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi CSDL", f"Không thể giải ngân: {e}")

    def load_data_tbl_giai_ngan(self):
        if not hasattr(self, 'tblGiaiNgan'): return
        q = """
            SELECT gn.MaGN, gn.MaHS, COALESCE(tnv_n.HoTen, 'N/A') AS TenTNV, 
                   gn.LoaiHinh, gn.SoTienGiaiNgan, gn.MoTaHienVatTrao, gn.NgayThucHien
            FROM GIAI_NGAN_PHAT_HANG gn
            LEFT JOIN TINH_NGUYEN_VIEN tnv ON gn.MaTNV = tnv.MaTNV
            LEFT JOIN NGUOI tnv_n ON tnv.CCCD = tnv_n.CCCD
            ORDER BY gn.MaGN DESC
        """
        ds = self.db.fetch_all(q)

        self.tblGiaiNgan.setRowCount(0)
        for r_idx, r in enumerate(ds):
            self.tblGiaiNgan.insertRow(r_idx)
            self.tblGiaiNgan.setItem(r_idx, 0, QTableWidgetItem(str(r['MaGN'])))
            self.tblGiaiNgan.setItem(r_idx, 1, QTableWidgetItem(str(r['MaHS'])))
            self.tblGiaiNgan.setItem(r_idx, 2, QTableWidgetItem(str(r['TenTNV'])))

            st_str = str(r['MoTaHienVatTrao']) if r['LoaiHinh'] == 'HienVat' or (r['SoTienGiaiNgan'] is not None and float(r['SoTienGiaiNgan']) == 0) else f"{float(r['SoTienGiaiNgan']):,.0f} đ"
            self.tblGiaiNgan.setItem(r_idx, 3, QTableWidgetItem(st_str))
            self.tblGiaiNgan.setItem(r_idx, 4, QTableWidgetItem(str(r['NgayThucHien'])))

            btn_in = QPushButton("In BB")
            btn_in.setStyleSheet("background-color: #0284c7; color: white; border-radius: 3px; padding: 2px 5px;")
            btn_in.clicked.connect(lambda checked, m=r['MaGN']: self.in_bien_ban_giai_ngan(m))

            c = QWidget(); l = QHBoxLayout(); l.addWidget(btn_in); l.setContentsMargins(0,0,0,0); c.setLayout(l)
            self.tblGiaiNgan.setCellWidget(r_idx, 5, c)

    def in_bien_ban_giai_ngan(self, ma_gn):
        q = """
            SELECT 
                gn.MaGN, gn.MaHS, cd.TenChienDich, nth.HoTen AS TenNTH, nth.CCCD AS CCCD_NTH,
                COALESCE(nth_sdt.SDT, 'N/A') AS SDT_NTH, nth.DiaChi AS DiaChi_NTH,
                gn.LoaiHinh, gn.SoTienGiaiNgan, gn.MoTaHienVatTrao, gn.NgayThucHien,
                gn.MaTNV, tnv_n.HoTen AS TenTNV, gn.MaKT, kt_n.HoTen AS TenKT, hs.MaBDH
            FROM GIAI_NGAN_PHAT_HANG gn
            JOIN HO_SO_CUU_TRO hs ON gn.MaHS = hs.MaHS
            JOIN CHIEN_DICH cd ON hs.MaCD = cd.MaCD
            JOIN NGUOI_THU_HUONG nth ON hs.MaNTH = nth.MaNTH
            LEFT JOIN (SELECT MaNTH, GROUP_CONCAT(SDT SEPARATOR ', ') AS SDT FROM NGUOI_THU_HUONG_SDT GROUP BY MaNTH) nth_sdt ON nth.MaNTH = nth_sdt.MaNTH
            LEFT JOIN TINH_NGUYEN_VIEN tnv ON gn.MaTNV = tnv.MaTNV
            LEFT JOIN NGUOI tnv_n ON tnv.CCCD = tnv_n.CCCD
            LEFT JOIN KE_TOAN kt ON gn.MaKT = kt.MaKT
            LEFT JOIN NGUOI kt_n ON kt.CCCD = kt_n.CCCD
            WHERE gn.MaGN = %s
        """
        ds = self.db.fetch_all(q, (ma_gn,))
        if ds: DialogBienBanGiaiNgan(ds[0], self).exec()

    def mo_popup_them_nguoi_thu_huong(self):
        dlg = DialogThemNTH(self.db, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.load_cbo_nth_tab4()
            if hasattr(dlg, 'ma_nth_vua_them') and hasattr(self, 'cboNguoiThuHuong'):
                idx = self.cboNguoiThuHuong.findData(dlg.ma_nth_vua_them)
                if idx >= 0: self.cboNguoiThuHuong.setCurrentIndex(idx)


    # =========================================================================
    # TAB 5: TRUNG TÂM BÁO CÁO, THỐNG KÊ (NÂNG CẤP TOÀN DIỆN MỚI)
    # =========================================================================
    def setup_tab_5_events(self):
        if hasattr(self, 'tblBaoCao'):
            self.tblBaoCao.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        if hasattr(self, 'dtTuNgay'):
            self.dtTuNgay.setDate(QDate(2000, 1, 1))
        if hasattr(self, 'dtDenNgay'):
            self.dtDenNgay.setDate(QDate.currentDate())

        # Lắng nghe sự kiện thay đổi lựa chọn chiến dịch
        if hasattr(self, 'cboLocChienDich'):
            self.cboLocChienDich.currentIndexChanged.connect(self.tai_bao_cao_tab5)

        if hasattr(self, 'btnTaiBaoCao'):
            self.btnTaiBaoCao.clicked.connect(self.tai_bao_cao_tab5)
        if hasattr(self, 'btnXuatFile'):
            self.btnXuatFile.clicked.connect(self.xuat_file_bao_cao_tab5)

        self.load_cbo_filter_tab5()
        self.cap_nhat_tab_5()

    def load_cbo_filter_tab5(self):
        """Đổ danh sách chiến dịch vào ComboBox bộ lọc cboLocChienDich ở Tab 5"""
        if not hasattr(self, 'cboLocChienDich'): return
        cbo = getattr(self, 'cboLocChienDich')
        cbo.clear()
        cbo.addItem("Tất cả chiến dịch", "ALL")
        
        ds = self.db.fetch_all("SELECT MaCD, TenChienDich FROM CHIEN_DICH ORDER BY MaCD ASC")
        for d in ds:
            cbo.addItem(f"{d['MaCD']} - {d['TenChienDich']}", d['MaCD'])

    def cap_nhat_tab_5(self):
        """Hàm tổng tải dữ liệu tổng quan, tiến độ từng chiến dịch và bảng báo cáo"""
        self.load_card_overview_tab5()
        self.load_tien_do_chien_dich_tab5()
        self.tai_bao_cao_tab5()

    def load_card_overview_tab5(self):
        """1. Cập nhật 4 thẻ thông số tổng quan"""
        # Quyên góp (Đã đối soát)
        q_qg = "SELECT COALESCE(SUM(SoTien), 0) AS TongTien, COUNT(*) AS SoGD FROM QUYEN_GOP WHERE TrangThaiDoiSoat = 'Đã đối soát'"
        r_qg = self.db.fetch_all(q_qg)
        tong_qg = float(r_qg[0]['TongTien']) if r_qg else 0.0
        so_gd = int(r_qg[0]['SoGD']) if r_qg else 0

        if hasattr(self, 'lblTongQuyenGop'): self.lblTongQuyenGop.setText(f"{tong_qg:,.0f} đ")
        if hasattr(self, 'lblSubQuyenGop'): self.lblSubQuyenGop.setText(f"{so_gd} giao dịch tiếp nhận")

        # Giải ngân thực tế
        q_gn = "SELECT COALESCE(SUM(SoTienGiaiNgan), 0) AS TongChi, COUNT(*) AS SoDot FROM GIAI_NGAN_PHAT_HANG"
        r_gn = self.db.fetch_all(q_gn)
        tong_gn = float(r_gn[0]['TongChi']) if r_gn else 0.0
        so_dot = int(r_gn[0]['SoDot']) if r_gn else 0

        if hasattr(self, 'lblTongGiaiNgan'): self.lblTongGiaiNgan.setText(f"{tong_gn:,.0f} đ")
        if hasattr(self, 'lblSub2'): self.lblSub2.setText(f"{so_dot} đợt trao phát")

        # Số dư khả dụng
        so_du = tong_qg - tong_gn
        if hasattr(self, 'lblSoDuKhaDung'): self.lblSoDuKhaDung.setText(f"{so_du:,.0f} đ")

        # Chiến dịch đang hoạt động / Tổng
        q_cd = "SELECT COUNT(*) AS TongCD, SUM(CASE WHEN TrangThai = 'Đang thực hiện' THEN 1 ELSE 0 END) AS DangChay FROM CHIEN_DICH"
        r_cd = self.db.fetch_all(q_cd)
        tong_cd = int(r_cd[0]['TongCD']) if r_cd else 0
        dang_chay = int(r_cd[0]['DangChay']) if r_cd and r_cd[0]['DangChay'] else 0

        if hasattr(self, 'label_58'): self.label_58.setText(f"{dang_chay}/{tong_cd} CD")

    def load_tien_do_chien_dich_tab5(self):
        """2. Code hiển thị danh sách thanh tiến độ tài chính từng chiến dịch vào scrollAreaChienDich"""
        if not hasattr(self, 'layoutListChienDich'): return
        
        # Xóa các widget cũ
        layout = self.layoutListChienDich.layout()
        if layout is None:
            layout = QVBoxLayout(self.layoutListChienDich)
        else:
            while layout.count():
                item = layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

        layout.setSpacing(15)

        # Lấy danh sách Chiến dịch
        q_cd = "SELECT MaCD, TenChienDich, MucTieuTien FROM CHIEN_DICH ORDER BY MaCD ASC"
        ds_cd = self.db.fetch_all(q_cd)

        # Thêm Header Tiêu đề & Ghi chú (Mục tiêu, Đã quyên góp, Đã giải ngân)
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 5)

        title_lbl = QLabel("Tiến Độ Tài Chính Từng Chiến Dịch")
        title_lbl.setStyleSheet("font-size: 15px; font-weight: bold; color: #38bdf8;")

        legend_lbl = QLabel("● Mục tiêu   ● Đã quyên góp   ● Đã giải ngân")
        legend_lbl.setStyleSheet("font-size: 11px; font-weight: bold; color: #94a3b8;")

        header_layout.addWidget(title_lbl)
        header_layout.addStretch()
        header_layout.addWidget(legend_lbl)
        layout.addWidget(header_widget)

        for cd in ds_cd:
            ma_cd = cd['MaCD']
            ten_cd = cd['TenChienDich']
            muc_tieu = float(cd['MucTieuTien'] or 0)

            # Tính đã quyên góp
            q_qg = "SELECT COALESCE(SUM(SoTien), 0) AS TongQG FROM QUYEN_GOP WHERE MaCD = %s AND TrangThaiDoiSoat = 'Đã đối soát'"
            r_qg = self.db.fetch_all(q_qg, (ma_cd,))
            da_qg = float(r_qg[0]['TongQG']) if r_qg else 0.0

            # Tính đã giải ngân
            q_gn = "SELECT COALESCE(SUM(gn.SoTienGiaiNgan), 0) AS TongGN FROM GIAI_NGAN_PHAT_HANG gn JOIN HO_SO_CUU_TRO hs ON gn.MaHS = hs.MaHS WHERE hs.MaCD = %s"
            r_gn = self.db.fetch_all(q_gn, (ma_cd,))
            da_gn = float(r_gn[0]['TongGN']) if r_gn else 0.0

            pct_dat = (da_qg / muc_tieu * 100) if muc_tieu > 0 else 0

            # Widget Card cho từng CD
            card = QFrame()
            card.setStyleSheet("QFrame { background-color: #1e293b; border-radius: 8px; padding: 8px; } QLabel { color: white; }")
            card_layout = QVBoxLayout(card)
            card_layout.setSpacing(6)

            # Tên chiến dịch + Phần trăm
            top_layout = QHBoxLayout()
            lbl_name = QLabel(f"<b>{ma_cd}</b>: {ten_cd}")
            lbl_name.setStyleSheet("color: #38bdf8; font-size: 13px;")
            lbl_pct = QLabel(f"<b>{pct_dat:.0f}%</b> đạt mục tiêu")
            lbl_pct.setStyleSheet("color: #4ade80; font-size: 12px;")

            top_layout.addWidget(lbl_name)
            top_layout.addStretch()
            top_layout.addWidget(lbl_pct)
            card_layout.addLayout(top_layout)

            # Thanh Mục tiêu (Xám/Lam)
            card_layout.addLayout(self.create_progress_row("Mục tiêu:", muc_tieu, muc_tieu, "#475569"))
            # Thanh Quyên góp (Xanh lá)
            card_layout.addLayout(self.create_progress_row("Quyên góp:", da_qg, muc_tieu, "#10b981"))
            # Thanh Giải ngân (Xanh dương)
            card_layout.addLayout(self.create_progress_row("Giải ngân:", da_gn, muc_tieu, "#0284c7"))

            layout.addWidget(card)

        layout.addStretch()

    def create_progress_row(self, label_text, val, max_val, color_hex):
        """Hàm phụ trợ vẽ hàng gồm Nhãn - Thanh ProgressBar - Giá trị tiền"""
        row = QHBoxLayout()
        row.setSpacing(8)

        lbl = QLabel(label_text)
        lbl.setFixedWidth(70)
        lbl.setStyleSheet("font-size: 11px; color: #94a3b8;")

        bar = QProgressBar()
        bar.setFixedHeight(12)
        bar.setTextVisible(False)
        bar.setMaximum(100)
        
        pct = int((val / max_val * 100)) if max_val > 0 else 0
        bar.setValue(min(pct, 100))
        bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: #0f172a;
                border-radius: 6px;
                border: none;
            }}
            QProgressBar::chunk {{
                background-color: {color_hex};
                border-radius: 6px;
            }}
        """)

        val_lbl = QLabel(f"{val:,.0f} đ")
        val_lbl.setFixedWidth(110)
        val_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        val_lbl.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {color_hex};")

        row.addWidget(lbl)
        row.addWidget(bar)
        row.addWidget(val_lbl)
        return row

    def tai_bao_cao_tab5(self):
        """Tải danh sách quyên góp theo bộ lọc Ngày & Chiến dịch vào tblBaoCao"""
        if not hasattr(self, 'tblBaoCao'): return

        cbo_cd = getattr(self, 'cboLocChienDich', None)
        ma_cd_filter = cbo_cd.currentData() if cbo_cd else "ALL"

        tu_ngay = self.dtTuNgay.date().toString("yyyy-MM-dd") if hasattr(self, 'dtTuNgay') else "2000-01-01"
        den_ngay = self.dtDenNgay.date().toString("yyyy-MM-dd") if hasattr(self, 'dtDenNgay') else QDate.currentDate().toString("yyyy-MM-dd")

        q = """
            SELECT qg.MaQG, qg.NgayQuyenGop, COALESCE(nht.TenNHT, 'Nhà hảo tâm ẩn danh') AS TenNHT,
                   cd.TenChienDich, qg.HinhThuc, qg.MaGiaoDichNganHang, qg.SoTien, qg.TrangThaiDoiSoat, qg.MoTaHienVat
            FROM QUYEN_GOP qg
            LEFT JOIN NHA_HAO_TAM nht ON qg.MaNHT = nht.MaNHT
            LEFT JOIN CHIEN_DICH cd ON qg.MaCD = cd.MaCD
            WHERE qg.NgayQuyenGop BETWEEN %s AND %s
        """
        params = [tu_ngay, den_ngay]

        if ma_cd_filter and ma_cd_filter != "ALL":
            q += " AND qg.MaCD = %s"
            params.append(ma_cd_filter)

        q += " ORDER BY qg.NgayQuyenGop DESC"
        ds = self.db.fetch_all(q, tuple(params))

        self.tblBaoCao.setRowCount(0)
        tong_kinh_phi = 0.0

        for r_idx, r in enumerate(ds):
            self.tblBaoCao.insertRow(r_idx)
            self.tblBaoCao.setItem(r_idx, 0, QTableWidgetItem(str(r['MaQG'])))
            self.tblBaoCao.setItem(r_idx, 1, QTableWidgetItem(str(r['NgayQuyenGop'])))
            self.tblBaoCao.setItem(r_idx, 2, QTableWidgetItem(str(r['TenNHT'])))
            self.tblBaoCao.setItem(r_idx, 3, QTableWidgetItem(str(r['TenChienDich'])))
            self.tblBaoCao.setItem(r_idx, 4, QTableWidgetItem(str(r['HinhThuc'])))
            self.tblBaoCao.setItem(r_idx, 5, QTableWidgetItem(str(r['MaGiaoDichNganHang'] or 'N/A')))

            so_tien = float(r['SoTien'] or 0)
            st_str = str(r['MoTaHienVat']) if r['HinhThuc'] == 'HienVat' or so_tien == 0 else f"{so_tien:,.0f} đ"
            self.tblBaoCao.setItem(r_idx, 6, QTableWidgetItem(st_str))
            self.tblBaoCao.setItem(r_idx, 7, QTableWidgetItem(str(r['TrangThaiDoiSoat'])))

            if r['TrangThaiDoiSoat'] == 'Đã đối soát':
                tong_kinh_phi += so_tien

        if hasattr(self, 'txtBanGhi'): self.txtBanGhi.setText(str(len(ds)))
        if hasattr(self, 'txtTongQuyenGop'): self.txtTongQuyenGop.setText(f"{tong_kinh_phi:,.0f} đ")

    def xuat_file_bao_cao_tab5(self):
        """4. Xuất dữ liệu từ bảng tblBaoCao ra tệp Excel (.xlsx) hoặc CSV (.csv)"""
        if not hasattr(self, 'tblBaoCao') or self.tblBaoCao.rowCount() == 0:
            QMessageBox.warning(self, "Cảnh báo", "Không có dữ liệu trong bảng để xuất file!")
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "Xuất Báo Cáo", "", "Excel Files (*.csv *.xlsx);;All Files (*)")
        if not file_path:
            return

        try:
            with open(file_path, mode='w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                # Ghi Tiêu đề cột
                headers = []
                for col in range(self.tblBaoCao.columnCount()):
                    headers.append(self.tblBaoCao.horizontalHeaderItem(col).text())
                writer.writerow(headers)

                # Ghi dữ liệu dòng
                for row in range(self.tblBaoCao.rowCount()):
                    row_data = []
                    for col in range(self.tblBaoCao.columnCount()):
                        item = self.tblBaoCao.item(row, col)
                        row_data.append(item.text() if item else "")
                    writer.writerow(row_data)

            QMessageBox.information(self, "Thành công", f"Đã xuất file báo cáo thành công!\nĐường dẫn: {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi xuất file", f"Không thể xuất file: {e}")


    # =========================================================================
    # TIỆN ÍCH KHÁC
    # =========================================================================
    def check_database_connection(self):
        if self.db.connect():
            print(">>> Kết nối CSDL MySQL thành công!")
            self.db.disconnect()
        else:
            QMessageBox.critical(self, "Lỗi CSDL", "Không thể kết nối đến CSDL MySQL!")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    try:
        with open("style.qss", "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    except Exception as e:
        print(f"Lỗi nạp stylesheet: {e}")
    window = MainApp()
    window.show()
    sys.exit(app.exec())