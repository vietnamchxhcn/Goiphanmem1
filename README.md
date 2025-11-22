# Goiphanmem1
Bước 1: Thu thập dữ liệu (Data Collection)File thực hiện: Install_Data.pyNguồn dữ liệu: API của CafeF (https://cafef.vn/du-lieu/Ajax/PageNew/DataHistory/PriceHistory.ashx).
Bước 2: Làm sạch và Chuẩn hóa dữ liệu (Data Cleaning & Transformation)File thực hiện: Modify_Data.pyĐầu vào: File Excel thô từ 
Bước 3: Chuẩn bị biến ngoại sinh (External Factors)File dữ liệu: 10ybondyield_filled.xlsxĐây là dữ liệu Lợi suất trái phiếu chính phủ 10 năm.
Bước 4: Phân tích và Mô hình hóa (Analysis & Modeling)File thực hiện: do.ipynb

1.Install_Data.py (Data Crawler) Script này chịu trách nhiệm thu thập dữ liệu lịch sử từ nguồn CafeF API.
Chức năng chính:
Gửi request giả lập User-Agent để lấy dữ liệu giao dịch (OHLCV) của danh sách cổ phiếu HNX30.
Sử dụng Multi-threading (ThreadPoolExecutor) để tải song song dữ liệu cho nhiều mã cổ phiếu, tối ưu hóa tốc độ.
Tự động xử lý phân trang (Paging) để lấy toàn bộ lịch sử giao dịch từ 2020 đến nay.Lưu trữ dữ liệu thô dưới dạng Excel.

2. Modify_Data.py (Data Cleaner / ETL)Script này thực hiện quy trình ETL (Extract - Transform - Load) để biến đổi dữ liệu thô thành dạng sẵn sàng cho phân tích.
Chức năng chính:
- Parsing: Phân tích cú pháp chuỗi dictionary trong Excel thô thành các cột dữ liệu riêng biệt.
- Standardization: Đổi tên cột (Tiếng Việt -> English), định dạng lại kiểu dữ liệu ngày tháng (Datetime) và số thực (Float).
- Data Fix: Tự động phát hiện và xử lý lỗi dữ liệu (ví dụ: thay thế giá Close = 0 bằng giá Open của ngày cuối cùng).
- Export: Xuất dữ liệu sạch ra file Excel mới, mỗi mã cổ phiếu là một Sheet riêng biệt.

3. do.ipynb (Analysis & Modeling Core)Notebook này chứa toàn bộ logic phân tích định lượng và mô hình hóa.
Quy trình thực hiện:Data Loading: Đọc dữ liệu cổ phiếu sạch và dữ liệu vĩ mô (Lợi suất trái phiếu 10 năm).
- Returns Calculation: Tính toán lợi suất tuần (Weekly Log Returns) để khử nhiễu.
- CAPM Model: Hồi quy lợi suất cổ phiếu theo thị trường (Market Index) để tính hệ số Beta ($\beta$), phân loại cổ phiếu phòng thủ (Low Beta) và tấn công (High Beta).
- SML Visualization: Vẽ đường thị trường chứng khoán (Security Market Line) để đánh giá định giá cổ phiếu.
- ARIMAX Forecasting: Xây dựng mô hình dự báo giá (ví dụ: CEO) kết hợp với biến ngoại sinh (Exogenous Variable) là Lợi suất trái phiếu.
- Optimization: Sử dụng Grid Search để tìm tham số (p,d,q) tối ưu theo chỉ số AIC.4.
- 10ybondyield_filled.xlsx (Exogenous Data)Dữ liệu lịch sử Lợi suất Trái phiếu Chính phủ Việt Nam kỳ hạn 10 năm.
Đóng vai trò là biến độc lập (X) trong mô hình ARIMAX để tăng độ chính xác khi dự báo giá cổ phiếu, dựa trên giả thuyết về mối tương quan giữa lãi suất và thị trường chứng khoán.
