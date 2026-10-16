# BÁO CÁO BÀI TẬP LỚN SỐ 1
## MÔN CÁC VẤN ĐỀ HIỆN ĐẠI TRONG KHOA HỌC MÁY TÍNH
**HỌC KỲ I - NĂM HỌC 2026 – 2027**

---

### Đề tài: Đánh giá thực nghiệm các phương pháp mã hóa SAT và Solver chính xác cho bài toán N-Queens (N-Queens Solver)
* **Sinh viên thực hiện:** Quang Hồng
* **Template bài báo khoa học:** Elsevier `\documentclass[a4paper,fleqn]{cas-sc}` (xem file [report/report.tex](file:///c:/Users/Quang%20Hong/Desktop/Project1-%20c%C3%A1c%20v%E1%BA%A5n%20%C4%91%E1%BB%81%20khmt/report/report.tex))
* **Mã nguồn và dữ liệu thực nghiệm:** [GitHub Repository](https://github.com/QuangHong/nQueens-SAT-Benchmark)

---

## TÓM TẮT BÁO CÁO (ABSTRACT)

Bài toán xếp N quân hậu (N-Queens) là bài toán kinh điển trong lĩnh vực thỏa mãn ràng buộc (CSP) và suy diễn tự động. Đặt N quân hậu lên bàn cờ N x N sao cho không có 2 quân hậu nào tấn công nhau. Khi kích cỡ bài toán tăng lên mức lớn (N = 64, 128, 256), việc mã hóa các ràng buộc số lượng Boolean (Boolean Cardinality Constraints) trở thành điểm nghẽn quyết định.

Báo cáo này nghiên cứu và đánh giá thực nghiệm toàn diện:
1. **5 kỹ thuật mã hóa At-Most-One (AMO - tối đa một):**
   - Pairwise (Binomial)
   - Sequential Counter (Sinz, 2005)
   - Binary (Bitwise)
   - Commander Variable (Klieber & Kwon, 2007)
   - Product (Jingchao Chen, 2010)
2. **4 bộ giải SAT CDCL hiện đại hàng đầu:**
   - Glucose 3, Glucose 4, CaDiCaL 1.5, Minisat 2.2.
3. **So sánh đối chuẩn với phương pháp giải chính xác:**
   - Lập trình ràng buộc (Constraint Programming) qua Google OR-Tools CP-SAT (sử dụng ràng buộc toàn cục `AllDifferent`).

---

## 1. MÔ HÌNH TOÁN HỌC BÀI TOÁN

Bàn cờ kích thước N x N gồm N^2 biến Boolean:
`x[i, j] = 1` nếu ô (i, j) có quân hậu, ngược lại bằng 0.

### 1.1. Ràng buộc hàng và cột (Exactly-One)
Mỗi hàng và mỗi cột phải có đúng 1 quân hậu:
- Tổng x[i, j] theo j từ 0 đến N-1 = 1 (với mọi hàng i)
- Tổng x[i, j] theo i từ 0 đến N-1 = 1 (với mọi cột j)

Trong dạng chuẩn tắc hội CNF, điều kiện Exactly-One (EO) được phân rã thành:
`EO = At-Least-One (ALO) AND At-Most-One (AMO)`
- ALO được biểu diễn đơn giản bằng 1 mệnh đề: `(x_0 OR x_1 OR ... OR x_{k-1})`.
- AMO cấm không cho từ 2 biến trở lên cùng mang giá trị True.

### 1.2. Ràng buộc đường chéo (At-Most-One)
Đường chéo có thể không có quân hậu nào, do đó chỉ cần ràng buộc At-Most-One (AMO):
- Đường chéo chính (i - j = const): tối đa 1 quân hậu.
- Đường chéo phụ (i + j = const): tối đa 1 quân hậu.

---

## 2. PHÂN TÍCH LÝ THUYẾT 5 KỸ THUẬT MÃ HÓA AMO

| Kỹ thuật mã hóa | Tác giả & Năm | Số biến phụ sinh thêm | Số lượng mệnh đề (Clauses) | Đánh giá lý thuyết |
| :--- | :--- | :--- | :--- | :--- |
| **Pairwise (Binomial)** | Truyền thống | 0 | k * (k - 1) / 2 = O(k^2) | Không tốn biến phụ nhưng bùng nổ mệnh đề khi k lớn |
| **Sequential Counter** | Carsten Sinz (2005) | k - 1 = O(k) | 3k - 4 = O(k) | Số mệnh đề tuyến tính, lan truyền đơn vị tốt |
| **Binary (Bitwise)** | Truyền thống | ceil(log2(k)) = O(log k) | O(k * log k) | Cực kỳ tiết kiệm biến phụ |
| **Commander** | Klieber & Kwon (2007) | O(k) | O(k) | Chia nhóm 3 phần tử, phân cấp chỉ huy |
| **Product** | Jingchao Chen (2010) | 2 * sqrt(k) = O(sqrt(k)) | O(k) | Cân bằng tuyệt vời giữa biến phụ và mệnh đề |

---

## 3. KẾT QUẢ THỰC NGHIỆM ĐÁNH GIÁ (EXPERIMENTAL RESULTS)

Thực nghiệm được thực hiện trên môi trường máy Intel Core i7, Windows 10, Python 3.11, thư viện PySAT 1.9.dev15 và Google OR-Tools 9.15. Thời gian giới hạn cho mỗi bài toán là 45 giây (single-threaded).

### 3.1. Bảng số liệu thực nghiệm giữa 5 kỹ thuật Encoding và CP-SAT

| Kích cỡ N | Chỉ số đo | Pairwise | Sequential | Binary | Commander | Product | CP-SAT (OR-Tools) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **16** | Số mệnh đề<br>Thời gian giải | 6.352<br>0.785s | 2.732<br>0.753s | 3.928<br>0.826s | 2.688<br>0.756s | 2.876<br>1.002s | 3 ràng buộc<br>**0.024s** |
| **32** | Số mệnh đề<br>Thời gian giải | 52.640<br>0.728s | 11.596<br>0.848s | 19.800<br>0.746s | 11.516<br>1.786s | 12.034<br>45.29s | 3 ràng buộc<br>**0.050s** |
| **64** | Số mệnh đề<br>Thời gian giải | 428.864<br>1.140s | 47.756<br>29.94s | 95.576<br>**0.787s** | 47.644<br>Timeout | 47.556<br>Timeout | 3 ràng buộc<br>0.270s |
| **128** | Số mệnh đề<br>Thời gian giải | 3.462.784<br>5.950s | 193.804<br>Timeout | 447.832<br>1.401s | 193.720<br>**1.144s** | 193.158<br>1.403s | 3 ràng buộc<br>1.598s |
| **256** | Số mệnh đề<br>Thời gian giải | **Tràn RAM**<br>(>27 triệu) | 780.812<br>Timeout | 2.053.464<br>4.390s | 781.648<br>2.728s | 773.268<br>**2.512s** | 3 ràng buộc<br>16.051s |

---

### 3.2. Bảng so sánh 4 bộ giải SAT CDCL (với Sequential Counter)

| Kích cỡ N | Glucose 3 | Glucose 4 | CaDiCaL 1.5 | Minisat 2.2 |
| :---: | :---: | :---: | :---: | :---: |
| **16** | 0.0071s | 0.0069s | 0.0154s | **0.0029s** |
| **32** | 0.1517s | 0.1423s | 0.0486s | **0.0101s** |
| **64** | 31.2840s | 18.8486s | 1.2428s | **0.0431s** |
| **128** | Timeout (>45s) | Timeout (>45s) | 5.4281s | **0.2610s** |
| **256** | Timeout (>45s) | Timeout (>45s) | 36.9118s | **1.0098s** |

---

## 4. CÁC PHÁT HIỆN KHOA HỌC QUAN TRỌNG (KEY FINDINGS)

1. **Sự bùng nổ mệnh đề của Pairwise (O(N^2)):**
   - Với N = 128, Pairwise sinh tới 3.462.784 mệnh đề. Đến N = 256, số mệnh đề vượt quá 27 triệu, gây cạn kiệt bộ nhớ RAM.
   - Ngược lại, Product và Commander giữ số mệnh đề ở mức tuyến tính (~780.000 mệnh đề ở N = 256).

2. **Khả năng mở rộng vượt trội của SAT so với CP-SAT ở kích thước lớn:**
   - Ở N <= 64: Google OR-Tools CP-SAT nhanh hơn nhờ mô hình biến nguyên gọn gàng (chỉ N biến) và thuật toán lọc miền `AllDifferent`.
   - **Tuy nhiên ở N = 256:** CP-SAT mất tới **16.05 giây**, trong khi SAT với mã hóa **Product chỉ mất 2.51 giây** và **Commander chỉ mất 2.73 giây** (nhanh hơn CP-SAT tới **6 lần**!).
   - Điều này chứng minh: Cơ chế học mệnh đề mâu thuẫn (CDCL Conflict Learning) trên các mệnh đề phân rã Boolean có tốc độ cắt tỉa không gian tìm kiếm vượt bậc khi bài toán quy mô lớn.

3. **Hiệu năng xuất sắc của Minisat 2.2:**
   - Trong khi Glucose 3 và 4 bị bế tắc do chuỗi biến phụ tích lũy của Sequential Counter ở N >= 128, **Minisat 2.2 giải quyết N = 256 chỉ trong 1.009 giây** nhờ chiến lược phân rã trọng số VSIDS và cơ chế khởi động lại (restarts) tối ưu.

---

## 5. DANH SÁCH BIỂU ĐỒ TRỰC QUAN

Các biểu đồ khoa học chất lượng cao (300 DPI) đã được xuất vào thư mục [report/figures/](file:///c:/Users/Quang%20Hong/Desktop/Project1-%20c%C3%A1c%20v%E1%BA%A5n%20%C4%91%E1%BB%81%20khmt/report/figures/):
1. [fig_clauses_encodings.png](file:///c:/Users/Quang%20Hong/Desktop/Project1-%20c%C3%A1c%20v%E1%BA%A5n%20%C4%91%E1%BB%81%20khmt/report/figures/fig_clauses_encodings.png): Biểu đồ so sánh số mệnh đề sinh ra theo thang đo Logarit.
2. [fig_solve_time_encodings.png](file:///c:/Users/Quang%20Hong/Desktop/Project1-%20c%C3%A1c%20v%E1%BA%A5n%20%C4%91%E1%BB%81%20khmt/report/figures/fig_solve_time_encodings.png): Biểu đồ thời gian giải của 5 kỹ thuật Encoding.
3. [fig_sat_vs_cpsat.png](file:///c:/Users/Quang%20Hong/Desktop/Project1-%20c%C3%A1c%20v%E1%BA%A5n%20%C4%91%E1%BB%81%20khmt/report/figures/fig_sat_vs_cpsat.png): Biểu đồ đối đầu giữa SAT và CP-SAT (OR-Tools).
4. [fig_sat_solvers.png](file:///c:/Users/Quang%20Hong/Desktop/Project1-%20c%C3%A1c%20v%E1%BA%A5n%20%C4%91%E1%BB%81%20khmt/report/figures/fig_sat_solvers.png): Biểu đồ so sánh tốc độ 4 solver CDCL (Glucose 3, 4, CaDiCaL, Minisat).
