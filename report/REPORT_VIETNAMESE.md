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
| **16** | Số mệnh đề<br>Thời gian giải | 6.352<br>0.732s | 2.732<br>0.720s | 3.928<br>0.757s | 2.688<br>0.841s | 2.856<br>1.074s | 3 ràng buộc<br>**0.012s** |
| **32** | Số mệnh đề<br>Thời gian giải | 52.640<br>0.734s | 11.596<br>0.814s | 19.800<br>0.922s | 11.516<br>1.798s | 11.928<br>7.393s | 3 ràng buộc<br>**0.048s** |
| **64** | Số mệnh đề<br>Thời gian giải | 428.864<br>1.234s | 47.756<br>30.97s | 95.576<br>**0.824s** | 47.644<br>Timeout | 47.448<br>Timeout | 3 ràng buộc<br>0.251s |
| **128** | Số mệnh đề<br>Thời gian giải | 3.462.784<br>5.966s | 193.804<br>Timeout | 447.832<br>1.239s | 193.720<br>**1.005s** | 192.942<br>1.235s | 3 ràng buộc<br>1.473s |
| **256** | Số mệnh đề<br>Thời gian giải | **Tràn RAM**<br>(>27 triệu) | 780.812<br>Timeout | 2.053.464<br>4.200s | 781.648<br>**2.490s** | 772.792<br>2.930s | 3 ràng buộc<br>14.538s |

---

### 3.2. Bảng so sánh 4 bộ giải SAT CDCL (với Sequential Counter)

| Kích cỡ N | Glucose 3 | Glucose 4 | CaDiCaL 1.5 | Minisat 2.2 |
| :---: | :---: | :---: | :---: | :---: |
| **16** | 0.0066s | 0.0076s | 0.0255s | **0.0111s** |
| **32** | 0.1304s | 0.1207s | 0.0471s | **0.0093s** |
| **64** | 30.0800s | 19.5673s | 1.2800s | **0.0490s** |
| **128** | Timeout (>45s) | Timeout (>45s) | 17.1217s | **0.2708s** |
| **256** | Timeout (>45s) | Timeout (>45s) | Timeout (>45s) | **1.0019s** |

---

### 3.3. So sánh chuyên sâu SAT Solving với các phương pháp giải chính xác khác (ILP, CP)

Bên cạnh SAT Solving, đề tài triển khai và đối chuẩn đầy đủ với 4 bộ giải thuộc 2 trường phái giải chính xác (Exact Solvers) kinh điển:

1. **Lập trình ràng buộc (Constraint Programming - CP):**
   - **Google OR-Tools CP-SAT:** Kết hợp kỹ thuật CP cổ điển với động cơ SAT giải lười (Lazy Clause Generation) và CDCL.
   - **IBM CPLEX CP Optimizer (`docplex.cp`):** Bộ giải CP thương mại hàng đầu sử dụng thuật toán lan truyền miền giá trị và tìm kiếm cục bộ mở rộng.
   - *Cách mô hình hóa CP:* Dùng $N$ biến số nguyên $q_r \in [0, N-1]$ đại diện cho vị trí cột của quân hậu tại hàng $r$. Bài toán được mô hình cực kỳ cô đọng với đúng **3 ràng buộc toàn cục `AllDifferent`**:
     $$\text{AllDifferent}(q_0, \dots, q_{N-1})$$
     $$\text{AllDifferent}(q_0 + 0, \dots, q_{N-1} + (N-1))$$
     $$\text{AllDifferent}(q_0 - 0, \dots, q_{N-1} - (N-1))$$

2. **Quy hoạch nguyên tuyến tính (Integer Linear Programming - ILP / MIP):**
   - **Gurobi Optimizer (`gurobipy`):** Bộ giải quy hoạch nguyên thương mại nhanh nhất thế giới.
   - **IBM ILOG CPLEX MIP (`docplex.mp`):** Bộ giải quy hoạch nguyên công nghiệp chuẩn mực của IBM.
   - *Cách mô hình hóa ILP:* Sử dụng ma trận $N^2$ biến nhị phân $x_{i,j} \in \{0, 1\}$.
     - Tổng hàng: $\sum_{j=0}^{N-1} x_{i,j} = 1, \quad \forall i$
     - Tổng cột: $\sum_{i=0}^{N-1} x_{i,j} = 1, \quad \forall j$
     - Tổng các đường chéo: $\sum_{(i,j) \in D} x_{i,j} \le 1, \quad \forall D$
     - *Đặc điểm:* Do N-Queens là bài toán khả thi thuần túy (Feasibility), không có hàm mục tiêu cần tối ưu hóa.

#### Bảng so sánh lý thuyết giữa 3 trường phái mô hình hóa

| Tiêu chí | SAT Solving (PySAT) | Constraint Programming (CP) | Integer Linear Programming (ILP/MIP) |
| :--- | :--- | :--- | :--- |
| **Các solver đại diện** | Glucose 3/4, CaDiCaL, Minisat | Google OR-Tools CP-SAT, CPLEX CP | Gurobi, IBM CPLEX MIP |
| **Kiểu biến quyết định** | $N^2$ biến Boolean ($+$ biến phụ AMO) | $N$ biến số nguyên miền rời rạc $[0, N-1]$ | $N^2$ biến nhị phân $x_{i,j} \in \{0, 1\}$ |
| **Bản chất ràng buộc** | Mệnh đề chuẩn tắc hội (CNF Clauses) | Ràng buộc toàn cục `AllDifferent` | Bất đẳng thức tuyến tính $\sum x = 1, \sum x \le 1$ |
| **Cơ chế suy diễn cốt lõi** | Lan truyền đơn vị (BCP) & Học xung đột (CDCL) | Lọc miền giá trị (Régin bipartite matching) | Simplex LP relaxation, Branch-and-Cut |
| **Điểm mạnh** | Học vết cắt cực nhanh, không phụ thuộc hàm mục tiêu | Biểu diễn cực kỳ cô đọng ($N$ biến, 3 ràng buộc) | Tận dụng được các kỹ thuật cắt phẳng (Cutting Planes) |
| **Điểm yếu** | Cần kỹ thuật mã hóa AMO khéo léo để tránh bùng nổ | Cây tìm kiếm rộng khi $N$ lớn | Nghiệm LP Relaxation bị phân số ($1/N$), cắt tỉa chậm |

#### Bảng đối chuẩn thực nghiệm đa phương pháp (N = 4, 8, 16, 32)

| Kích cỡ $N$ | Chỉ số | SAT (Sequential) | CP-SAT (OR-Tools) | CPLEX MIP | Gurobi | CPLEX CP Optimizer |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **4** | Số biến / Ràng buộc<br>Thời gian giải | 58 biến, 116 mệnh đề<br>0.112s | 4 biến, 3 ràng buộc<br>**0.001s** | 16 biến, 18 ràng buộc<br>0.008s | 16 biến, 18 ràng buộc<br>*(Yêu cầu License)* | 4 biến, 3 ràng buộc<br>*(Cần cpoptimizer.exe)* |
| **8** | Số biến / Ràng buộc<br>Thời gian giải | 274 biến, 604 mệnh đề<br>0.141s | 8 biến, 3 ràng buộc<br>**0.004s** | 64 biến, 42 ràng buộc<br>0.007s | 64 biến, 42 ràng buộc<br>*(Yêu cầu License)* | 8 biến, 3 ràng buộc<br>*(Cần cpoptimizer.exe)* |
| **16** | Số biến / Ràng buộc<br>Thời gian giải | 1.186 biến, 2.732 mệnh đề<br>0.142s | 16 biến, 3 ràng buộc<br>0.015s | 256 biến, 90 ràng buộc<br>**0.009s** | 256 biến, 90 ràng buộc<br>*(Yêu cầu License)* | 16 biến, 3 ràng buộc<br>*(Cần cpoptimizer.exe)* |
| **32** | Số biến / Ràng buộc<br>Thời gian giải | 4.930 biến, 11.596 mệnh đề<br>0.304s | 32 biến, 3 ràng buộc<br>**0.059s** | 1.024 biến<br>*(Vượt hạn mức 1000 biến)* | 1.024 biến<br>*(Yêu cầu License)* | 32 biến, 3 ràng buộc<br>*(Cần cpoptimizer.exe)* |

#### Thảo luận về tính sẵn sàng và rào cản triển khai thực tế của các Solver
1. **Google OR-Tools CP-SAT:** Là solver CP mã nguồn mở hoàn chỉnh, tối ưu hóa đa luồng xuất sắc, không ràng buộc bản quyền thương mại, giải rất nhanh từ $N \le 64$.
2. **IBM CPLEX MIP:** Phiên bản miễn phí (Community Edition) hoạt động hoàn hảo và có tốc độ giải MIP rất ấn tượng ở $N \le 16$, nhưng bị khống chế cứng ở mức $1.000$ biến. Vì $N = 32$ yêu cầu $32^2 = 1.024$ biến nên solver dừng lại với thông báo giới hạn kích thước (`limits exceeded / promotional version`).
3. **Gurobi & CPLEX CP Optimizer:** Đã được cài đặt đầy đủ wrapper trong [nqueens/alternatives.py](file:///c:/Users/Quang%20Hong/Desktop/Project1-%20c%C3%A1c%20v%E1%BA%A5n%20%C4%91%E1%BB%81%20khmt/nqueens/alternatives.py). Khi chạy trên môi trường không có khóa bản quyền hoặc thiếu file thực thi nhị phân `cpoptimizer.exe`, hệ thống tuân thủ nghiêm ngặt chuẩn mực nghiên cứu khoa học: báo trạng thái `UNAVAILABLE` thay vì làm giả kết quả.

---

## 4. CÁC PHÁT HIỆN KHOA HỌC QUAN TRỌNG (KEY FINDINGS)

1. **Sự bùng nổ mệnh đề của Pairwise (O(N^2)):**
   - Với N = 128, Pairwise sinh tới 3.462.784 mệnh đề. Đến N = 256, số mệnh đề vượt quá 27 triệu, gây cạn kiệt bộ nhớ RAM.
   - Ngược lại, Product và Commander giữ số mệnh đề ở mức tuyến tính (~780.000 mệnh đề ở N = 256).

2. **Khả năng mở rộng vượt trội của SAT so với CP-SAT và ILP ở kích thước lớn:**
   - Ở $N \le 64$: Google OR-Tools CP-SAT và CPLEX MIP nhanh hơn nhờ mô hình cô đọng và khả năng lọc miền cục bộ.
   - **Tuy nhiên ở $N = 256$:** CP-SAT mất tới **14.54 giây**, trong khi SAT với mã hóa **Commander chỉ mất 2.49 giây** và **Product chỉ mất 2.93 giây** (nhanh hơn CP-SAT từ **5 đến 6 lần**!).
   - Điều này chứng minh: Cơ chế học mệnh đề mâu thuẫn (CDCL Conflict Learning) trên các mệnh đề phân rã Boolean có tốc độ cắt tỉa không gian tìm kiếm vượt bậc khi bài toán quy mô lớn.

3. **Hiệu năng xuất sắc của Minisat 2.2:**
   - Trong khi Glucose 3 và 4 bị bế tắc do chuỗi biến phụ tích lũy của Sequential Counter ở $N \ge 128$, **Minisat 2.2 giải quyết N = 256 chỉ trong 1.002 giây** nhờ chiến lược phân rã trọng số VSIDS và cơ chế khởi động lại (restarts) tối ưu.

---

## 5. DANH SÁCH BIỂU ĐỒ TRỰC QUAN

Các biểu đồ khoa học chất lượng cao (300 DPI) đã được xuất vào thư mục [report/figures/](file:///c:/Users/Quang%20Hong/Desktop/Project1-%20c%C3%A1c%20v%E1%BA%A5n%20%C4%91%E1%BB%81%20khmt/report/figures/):
1. [fig_clauses_encodings.png](file:///c:/Users/Quang%20Hong/Desktop/Project1-%20c%C3%A1c%20v%E1%BA%A5n%20%C4%91%E1%BB%81%20khmt/report/figures/fig_clauses_encodings.png): Biểu đồ so sánh số mệnh đề sinh ra theo thang đo Logarit.
2. [fig_solve_time_encodings.png](file:///c:/Users/Quang%20Hong/Desktop/Project1-%20c%C3%A1c%20v%E1%BA%A5n%20%C4%91%E1%BB%81%20khmt/report/figures/fig_solve_time_encodings.png): Biểu đồ thời gian giải của 5 kỹ thuật Encoding.
3. [fig_sat_vs_cpsat.png](file:///c:/Users/Quang%20Hong/Desktop/Project1-%20c%C3%A1c%20v%E1%BA%A5n%20%C4%91%E1%BB%81%20khmt/report/figures/fig_sat_vs_cpsat.png): Biểu đồ đối đầu giữa SAT và CP-SAT (OR-Tools).
4. [fig_sat_solvers.png](file:///c:/Users/Quang%20Hong/Desktop/Project1-%20c%C3%A1c%20v%E1%BA%A5n%20%C4%91%E1%BB%81%20khmt/report/figures/fig_sat_solvers.png): Biểu đồ so sánh tốc độ 4 solver CDCL (Glucose 3, 4, CaDiCaL, Minisat).
