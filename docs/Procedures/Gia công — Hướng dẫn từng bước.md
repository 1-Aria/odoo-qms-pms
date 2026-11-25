# Gia công — Hướng dẫn từng bước trên Odoo

Bản tiếng Việt của *Processing — Step-by-step Guide.md*. Mỗi trường hợp ghi: mở màn hình nào, điền gì, bấm nút nào,
và phải thấy gì. Tên menu và nút theo **giao diện tiếng Việt** của Odoo; chỗ nào Odoo vẫn hiện tiếng Anh thì ghi
đúng như trên màn hình.

**Các trường hợp:** **1.** Gia công dài hạn cho Công ty TM · **2.** Gia công theo đơn cho khách hàng ·
**3.** Thuê gia công ngoài (Nhà Bàng) · **4.** Công ty tự sản xuất và tự bán · **5.** Hủy hàng và hạ loại ·
**6.** Kiểm kê · **7.** Công ty dùng hàng của Công ty TM · **8.** Bán hàng loại 2 cho nhân viên.

**Lưu ý về tên trường**
- Chủ hàng (*Owner*) trên màn hình tiếng Việt hiện là **"Người phụ trách"**. Trong hướng dẫn này gọi là **Chủ hàng
  (Người phụ trách)**.
- Các trường mới của hệ thống hiện bằng tiếng Anh: **Goods Owner** (chủ hàng của lệnh sản xuất), **Products Belong to
  the Owner** (thành phẩm thuộc chủ hàng), **Partner Owns the Goods**.
- *Tồn kho → Báo cáo* (Vị trí, Lịch sử điều chuyển, Định giá) và báo cáo *Company Material in Processing* chỉ dành cho
  người có quyền **quản trị Tồn kho**. Nhân viên kho xem chủ hàng ngay trên phiếu.

**Không bao giờ giao hoặc chuyển nhiều hơn số đã giữ hàng khi bấm *Kiểm tra tình trạng còn hàng*.** Odoo không chặn:
phần thừa vẫn xuất ra dưới tên chủ hàng của phiếu và làm tồn kho của chủ đó bị âm, phải kiểm kê lại để sửa.

---

## Xem hàng thuộc chủ nào

| Ở đâu | Thấy gì |
|---|---|
| Trên bất kỳ phiếu nào, một dòng sản phẩm → **biểu tượng chi tiết** (≡) ở cuối dòng | Cột **Người phụ trách**: *Công ty TNHH DV TM Quang Phương* = hàng Công ty TM; tên một khách hàng = hàng của khách đó; **để trống = hàng của công ty**. Trên phiếu xuất và phiếu nội bộ cột này không sửa được: hệ thống tự chọn khi giữ hàng |
| Trên phiếu nhập | Trường **Người phụ trách** ở phần đầu phiếu |
| *Trạng thái thành phần* trên lệnh sản xuất, *Tồn kho hiện có* của sản phẩm | **Không tách theo chủ hàng**: cộng hàng của mọi chủ. Không dùng để xem công ty có đủ hàng của mình không (xem 1.2a) |
| *Tồn kho → Báo cáo → Vị trí*, rồi *Nhóm theo → Người phụ trách* | Tồn kho theo từng chủ |
| *Tồn kho → Báo cáo → Lịch sử điều chuyển*, tìm theo số phiếu | Mọi dòng đã làm, có cột **Người phụ trách** |
| *Tồn kho → Báo cáo → Định giá* | Chỉ có hàng của công ty. Hàng của chủ khác không bao giờ hiện ở đây |

---

## Trường hợp 1 — Gia công dài hạn cho Công ty TM

Công ty TM gửi nguyên phụ liệu (không có đơn mua hàng); công ty sản xuất cho Công ty TM; hàng của Công ty TM xuất đi
không qua đơn bán hàng; mỗi tháng công ty xuất hóa đơn cho Công ty TM phí gia công và phần vật tư của công ty đã dùng.

### 1.1 Nhận nguyên phụ liệu của Công ty TM

1. *Tồn kho → Hoạt động → Lệnh chuyển hàng → Phiếu nhập kho* → **Mới**.
2. **Loại hoạt động**: *Nhận hàng Công ty TM*.
3. **Nhập từ**: *Công ty TNHH DV TM Quang Phương*.
4. Kiểm tra: **Người phụ trách** tự hiện *Công ty TNHH DV TM Quang Phương*.
5. Thẻ *Hoạt động* → **Thêm một sản phẩm**: sản phẩm, **Số lượng** thực nhận. Mỗi sản phẩm một dòng.
6. **Đánh dấu việc cần làm**, rồi **Xác nhận**.
7. In: **In → Phiếu nhập kho**, và **Biên bản giao nhận** nếu giao nhận có ký.

Phải thấy:
- *Vị trí* nhóm theo người phụ trách: số lượng nằm dưới *Công ty TNHH DV TM Quang Phương*.
- *Định giá*: không có gì cho phiếu này.
- *Phiếu nhập kho* in số lượng, **không có đơn giá, thành tiền** (hàng không phải của công ty).

Không được: nhận hàng Công ty TM bằng **đơn mua hàng**. Hàng sẽ thành của công ty và bị ghi giá trị vào sổ.

### 1.2 Tạo lệnh sản xuất cho Công ty TM

1. *Sản xuất → Hoạt động → Lệnh sản xuất* → **Mới**.
2. **Sản phẩm**, **Số lượng**. *Định mực nguyên liệu* tự điền.
3. Thẻ *Thông tin khác* → **Loại hoạt động**: *Gia công dài hạn*.
4. Kiểm tra, cùng thẻ: **Goods Owner** = *Công ty TNHH DV TM Quang Phương*; **Products Belong to the Owner** có đánh dấu.
5. **Xác nhận**.

Phải thấy: một phiếu *Pick Components* (nút ở đầu lệnh sản xuất, số WH/PC/…).

Nếu lỡ tạo lệnh trên *Manufacturing*: đó là lệnh **công ty tự sản xuất**, chỉ giữ hàng của công ty và *Kiểm tra tình
trạng còn hàng* không lấy được hàng Công ty TM. Khi lệnh còn ở trạng thái nháp hoặc đã xác nhận: đổi **Loại hoạt động**
sang *Gia công dài hạn* (*Goods Owner* tự đổi theo). Rồi trên phiếu *Pick Components*: **Hủy dự trữ** → **Kiểm tra
tình trạng còn hàng**.

### 1.2a Tự sản xuất hay gia công? Kiểm tra hàng của công ty trước

Định hướng: hàng của công ty đủ thì công ty tự sản xuất; không đủ mới gia công cho Công ty TM.

1. Tạo lệnh sản xuất trên **Manufacturing** (công ty tự sản xuất) → **Xác nhận**.
2. Mở phiếu *Pick Components* của lệnh → **Kiểm tra tình trạng còn hàng**.
3. Giữ đủ hết (trạng thái **Sẵn sàng**): hàng công ty đủ. Làm tiếp như 4.2.
4. Không giữ đủ: công ty không đủ hàng. Trên lệnh sản xuất → thẻ *Thông tin khác* → **Loại hoạt động**: *Gia công dài
   hạn*. Trên *Pick Components*: **Hủy dự trữ** → **Kiểm tra tình trạng còn hàng**. Lúc này hệ thống lấy hàng Công ty
   TM trước, thiếu mới lấy hàng công ty. Làm tiếp như 1.3.

### 1.3 Cấp nguyên phụ liệu (Pick Components)

1. Mở phiếu *Pick Components* (WH/PC/…).
2. **Kiểm tra tình trạng còn hàng**.
3. Xem **biểu tượng chi tiết** (≡) của từng dòng, cột **Người phụ trách**: hàng Công ty TM trước; dòng để trống (hàng
   công ty) chỉ cho phần Công ty TM thiếu.
4. **Xác nhận**. In **Phiếu xuất kho** nếu cần.

### 1.4 Sản xuất

1. Quay lại lệnh sản xuất: **Kiểm tra tình trạng còn hàng**.
2. Nhập số lượng sản xuất, hoặc bấm **Sản xuất tất cả**.
3. Mở phiếu *Store Finished Product* (WH/SFP/…) sinh ra sau đó → **Xác nhận**.

Phải thấy:
- *Vị trí* nhóm theo người phụ trách: thành phẩm nằm dưới *Công ty TNHH DV TM Quang Phương*.
- *Định giá*: không có dòng nào cho thành phẩm. Chỉ có dòng cho vật tư **của công ty** mà lệnh đã dùng, bút toán
  **Nợ 6320 / Có 1520** (bán cho Công ty TM, xem 1.6).

### 1.5 Xuất hàng của Công ty TM

Giao cho chính Công ty TM, hoặc cho khách của Công ty TM theo chỉ định.

1. *Tồn kho → Hoạt động → Lệnh chuyển hàng → Giao hàng* → **Mới**.
2. **Loại hoạt động**: *Xuất hàng Công ty TM*.
3. **Địa chỉ giao hàng**: người nhận hàng (Công ty TM, hoặc khách của Công ty TM).
4. Kiểm tra: **Người phụ trách** tự hiện *Công ty TNHH DV TM Quang Phương*.
5. **Thêm một sản phẩm**: sản phẩm và số lượng.
6. **Đánh dấu việc cần làm** → **Kiểm tra tình trạng còn hàng**. Hệ thống chỉ giữ hàng của Công ty TM.
7. **Xác nhận** đúng số đã giữ. Nếu giữ được ít hơn yêu cầu: giao số đã giữ, phần còn lại để thành đơn giao sau. In
   **Phiếu xuất kho** (không có giá) và **Biên bản giao nhận**.

Phải thấy: không có dòng *Định giá*, không có bút toán. Công ty TM tự xuất hóa đơn cho khách của mình.

Không được: xuất hàng Công ty TM qua **đơn bán hàng** hoặc bằng *Lệnh giao hàng*. *Lệnh giao hàng* cũng không lấy được
hàng này.

### 1.6 Cuối tháng — kế toán

**Thiết lập một lần**
1. Danh mục sản phẩm: *Tồn kho → Cấu hình → Sản phẩm → Danh mục sản phẩm* → **Mới**: **Danh mục** *Dịch vụ gia công*,
   **Danh mục chính** *All*, **Tài khoản thu nhập** 5110 → lưu.
2. Hai sản phẩm, *Tồn kho → Sản phẩm → Sản phẩm* → **Mới**, mỗi sản phẩm:
   - **Loại sản phẩm**: *Dịch vụ* (không bao giờ là *Hàng hóa*: hàng hóa trên hóa đơn bán sẽ sinh dòng giá vốn);
   - **Bán hàng** đánh dấu, **Mua hàng** bỏ đánh dấu;
   - **Danh mục sản phẩm**: *Dịch vụ gia công*;
   - **Chính sách xuất hóa đơn**: *Số lượng đã đặt*;
   - **Giá bán** 0 (giá ghi trên hóa đơn);
   - **Thuế**: thuế suất kế toán áp dụng (hiện 8%, như hàng của công ty).

   Tên: *Phí gia công* và *Vật tư cung cấp cho gia công*.

Hằng tháng:
1. Số lượng đã gia công: *Sản xuất → Báo cáo → Processed Goods*. Hàng là sản phẩm, cột là tháng.
2. Vật tư của công ty đã dùng: *Sản xuất → Báo cáo → Company Material in Processing*. Dạng xoay (pivot), tổng giá trị
   theo sản phẩm (cần quyền quản trị Tồn kho).
3. *Kế toán → Khách hàng → Hóa đơn* → **Mới**:
   - **Khách hàng**: *Công ty TNHH DV TM Quang Phương*;
   - mỗi mã hàng một dòng *Phí gia công*: mô tả = mã hàng, số lượng = số đã gia công, đơn giá = phí gia công;
   - một dòng *Vật tư cung cấp cho gia công*: số tiền = giá trị vật tư ở bước 2 (cộng mức lãi đã thỏa thuận);
   - thuế như thường lệ → **Xác nhận**, rồi phát hành hóa đơn điện tử.

Không được: xuất hóa đơn vật tư bằng chính sản phẩm tồn kho (vải, chỉ…). Odoo sẽ thêm dòng giá vốn theo giá chuẩn, trong
khi giá vốn đã ghi lúc vật tư được dùng.

Bút toán trong tháng:

| Nghiệp vụ | Bút toán |
|---|---|
| Vật tư của công ty dùng cho đơn của Công ty TM | Nợ 6320 / Có 1520 (tự động khi dùng) |
| Nhân công, chi phí chung | nằm ở 622, 627; cuối tháng kết chuyển vào giá vốn |
| Hóa đơn | Nợ 131 / Có 5110, Có 33311 |
| Nhận, sản xuất, xuất hàng Công ty TM | không có |

---

## Trường hợp 2 — Gia công theo đơn cho khách hàng

Khách đặt hàng làm từ nguyên phụ liệu của khách. Đơn bán hàng ghi phí gia công; xác nhận đơn sẽ tự tạo lệnh sản xuất và
phiếu nhận nguyên phụ liệu của khách. Thành phẩm là của công ty cho tới khi giao và xuất hóa đơn theo phí gia công.

### 2.0 Thiết lập một lần cho mỗi sản phẩm

**Thành phẩm** (mã hàng làm cho khách):
1. *Tồn kho → Sản phẩm → Sản phẩm* → mở sản phẩm (hoặc **Mới**: **Loại sản phẩm** *Hàng hóa*, **Theo dõi hàng tồn kho**
   đánh dấu).
2. **Giá bán**: phí gia công một sản phẩm (cộng vật tư công ty nếu công ty cung cấp thêm).
3. Thẻ *Tồn kho* → **Tuyến cung ứng**: đánh dấu **Bổ sung theo đơn đặt hàng (MTO)** và **Gia công theo đơn**; bỏ đánh
   dấu **Sản xuất** và **Mua**.

**Nguyên phụ liệu khách cung cấp** (vải, phụ liệu của khách):
1. *Tồn kho → Sản phẩm → Sản phẩm* → mở hoặc **Mới** (*Hàng hóa*, **Theo dõi hàng tồn kho** đánh dấu, danh mục *Raw
   Materials*, **Chi phí** 0).
2. Thẻ *Tồn kho* → **Tuyến cung ứng**: đánh dấu **Bổ sung theo đơn đặt hàng (MTO)** và **Resupply From Customer on
   Order**; bỏ đánh dấu **Mua**.

**Vật tư công ty cung cấp** (chỉ, nhãn…): không đổi, vẫn là **Mua**.

**Định mức nguyên liệu**: *Sản xuất → Sản phẩm → Định mực nguyên liệu* → **Mới**: thành phẩm, số lượng, thành phần gồm
nguyên phụ liệu của khách và vật tư của công ty → lưu → **Activate** (chỉ định mức đang dùng mới được áp dụng).

### 2.1 Đơn bán hàng

1. *Bán hàng → Đơn hàng → Báo giá* → **Mới**.
2. **Khách hàng**; dòng đơn: thành phẩm, số lượng, đơn giá = phí gia công.
3. **Xác nhận**.

Phải thấy trên đơn: nút **Sản xuất** (1) và **Giao hàng** (1). Mở lệnh sản xuất:
- **Loại hoạt động** *Gia công theo đơn*;
- thẻ *Thông tin khác*: **Goods Owner** = khách hàng; **Products Belong to the Owner** **không** đánh dấu.

### 2.2 Nhận nguyên phụ liệu của khách

1. *Tồn kho → Hoạt động → Lệnh chuyển hàng → Phiếu nhập kho* → mở phiếu *Resupply From Customer* (WH/SBC/…) do đơn tạo
   ra (**Chứng từ gốc** là lệnh sản xuất).
2. **Số lượng**: số thực nhận (có thể nhiều hơn yêu cầu).
3. **Xác nhận**. In **Phiếu nhập kho** và **Biên bản giao nhận**.

Phải thấy: **Người phụ trách** = khách hàng; *Vị trí* nhóm theo người phụ trách: nguyên phụ liệu nằm dưới tên khách;
không có gì trong *Định giá*.

### 2.3 Cấp liệu và sản xuất

Như 1.3 và 1.4. Trên *Pick Components*, chi tiết dòng: **Người phụ trách** = khách hàng cho hàng của khách, để trống
cho hàng công ty.

Phải thấy sau khi sản xuất:
- thành phẩm **không có người phụ trách** (là của công ty cho tới khi giao);
- *Định giá*: thành phẩm chỉ mang giá trị vật tư **của công ty** (hàng của khách không có giá trị).

### 2.4 Giao hàng và xuất hóa đơn

1. Trên đơn bán hàng → nút **Giao hàng** → **Kiểm tra tình trạng còn hàng** → **Xác nhận**. In như thường lệ.
2. Trên đơn bán hàng → **Tạo hoá đơn** → **Tạo bản nháp** → **Xác nhận**, rồi phát hành hóa đơn điện tử.

Phải thấy trong bút toán của hóa đơn: doanh thu 5110 = phí gia công; giá vốn **Nợ 6320 / Có 1599** = giá trị vật tư của
công ty trong hàng.

### 2.5 Trả nguyên phụ liệu thừa cho khách

1. *Tồn kho → Hoạt động → Lệnh chuyển hàng → Giao hàng* → **Mới**.
2. **Loại hoạt động**: *Trả NPL cho khách*.
3. **Địa chỉ giao hàng**: khách hàng. Kiểm tra: **Người phụ trách** = khách hàng.
4. **Thêm một sản phẩm**: nguyên phụ liệu thừa và số lượng.
5. **Đánh dấu việc cần làm** → **Kiểm tra tình trạng còn hàng** (chỉ lấy hàng của khách này) → **Xác nhận**. In
   **Phiếu xuất kho** và **Biên bản giao nhận**.

Bút toán trường hợp 2:

| Nghiệp vụ | Bút toán |
|---|---|
| Nhận, dùng, trả nguyên phụ liệu của khách | không có |
| Vật tư của công ty đã dùng | Nợ 1541 / Có 1520 |
| Thành phẩm nhập kho | Nợ 1550 / Có 1541 (vật tư công ty, cộng chi phí gia công nếu định mức có số phút) |
| Giao hàng | Nợ 1599 / Có 1550 |
| Hóa đơn | Nợ 131 / Có 5110, Có 33311; Nợ 6320 / Có 1599 |

---

## Trường hợp 3 — Thuê gia công ngoài (Nhà Bàng)

Công ty gửi nguyên phụ liệu của Công ty TM cho Nhà Bàng, Nhà Bàng may võng và tính phí gia công từng chiếc. Võng vẫn là
của Công ty TM; phí là chi phí của công ty, thu lại trong phí gia công công ty xuất cho Công ty TM (1.6).

### 3.0 Thiết lập một lần

- **Định mức của võng**: *Sản xuất → Sản phẩm → Định mực nguyên liệu* → định mức của võng → **Loại BoM**: *Gia công*,
  **Đơn vị gia công**: *Gia Công Võng Mùng (Nhà Bàng)* → **Activate**.
- **Thành phần** (vải, lưới, dây…): thẻ *Tồn kho* → **Tuyến cung ứng**: đánh dấu **Tái cung ứng cho đơn vị gia công
  theo đơn hàng**, để đơn mua tự gửi nguyên phụ liệu cho Nhà Bàng.
- **Vị trí tài chính của Nhà Bàng** đổi 3399 sang 6277 (đã làm khi chuyển đổi). Không cần làm gì.

**Vì sao hàng Nhà Bàng làm là của Công ty TM.** Do hai thiết lập:
1. Loại hoạt động ẩn *Subcontracting* của kho có **Goods Owner** = Công ty TM. Mọi lệnh gia công ngoài, dù đơn vị nào,
   đều tạo trên loại này: lấy hàng Công ty TM trước, thành phẩm là của Công ty TM, không có giá trị.
2. Vị trí tài chính của Nhà Bàng đưa hóa đơn vào 6277 thay vì 3399: phiếu nhận hàng không phải của công ty không ghi gì
   vào 3399 để hóa đơn đối trừ.

**Hiện nay mọi việc thuê gia công ngoài đều là cho Công ty TM.** Thuê gia công hàng **của công ty** (vật tư công ty,
thành phẩm có giá trị = vật tư + phí) cần đơn mua ghi rõ hàng của ai; phần này đang lên kế hoạch. Hỏi trước khi đặt đơn
đầu tiên loại này.

**Thêm một đơn vị gia công mới**
1. Đối tác: nếu là hộ kinh doanh không có hóa đơn VAT, dùng cùng vị trí tài chính với Nhà Bàng. Nếu làm hàng Công ty TM,
   vị trí tài chính cần **3399 → 6277**: chạy lại script thiết lập go-live, script tự thêm cho mọi đơn vị gia công có
   trên định mức gia công.
2. Vị trí riêng: trên đối tác, thẻ *Tồn kho* → **Vị trí gia công** → một vị trí riêng (vd. *Subcontracting / Xưởng X*).
   Không có thì mọi đơn vị dùng chung một vị trí và không biết mỗi nơi đang giữ gì.
3. Định mức: **Loại BoM** *Gia công*, đối tác trong **Đơn vị gia công** → **Activate**.
4. Thành phần: tuyến **Tái cung ứng cho đơn vị gia công theo đơn hàng**.
5. Tùy chọn: ghi phí gia công ở thẻ *Mua hàng* của sản phẩm làm giá của nhà cung cấp đó, để đơn mua tự điền.

### 3.1 Đặt gia công với Nhà Bàng

1. *Mua hàng → Đơn hàng → Yêu cầu báo giá* → **Mới**.
2. **Nhà cung cấp**: *Gia Công Võng Mùng (Nhà Bàng)*. Dòng: võng, số lượng, **Đơn giá** = phí gia công một chiếc
   (16.000).
3. **Xác nhận đơn hàng**.

Phải thấy: một phiếu *Tái cung ứng cho đơn vị gia công* (WH/RES/…) cho nguyên phụ liệu, và một phiếu nhận võng.

### 3.2 Gửi nguyên phụ liệu cho Nhà Bàng

1. *Tồn kho → Hoạt động → Lệnh chuyển hàng → Nội bộ* → mở phiếu WH/RES/….
2. **Kiểm tra tình trạng còn hàng**. Chi tiết dòng (≡): **Người phụ trách** *Công ty TNHH DV TM Quang Phương*, hàng
   Công ty TM được lấy trước.
3. **Xác nhận**. In **Phiếu xuất kho** và **Biên bản giao nhận** cho Nhà Bàng ký.

### 3.3 Nhận võng

1. Trên đơn mua → **Nhận sản phẩm**.
2. **Ghi nhận thành phần** nếu có nút: xác nhận số Nhà Bàng thực dùng. Phần chưa dùng vẫn nằm ở vị trí của Nhà Bàng cho
   tới khi trả về.
3. **Số lượng** nhận → **Xác nhận**.

Phải thấy: *Vị trí* nhóm theo người phụ trách: võng nằm dưới *Công ty TNHH DV TM Quang Phương*; không có gì trong
*Định giá*.

Lấy lại nguyên phụ liệu thừa từ Nhà Bàng: *Tồn kho → Hoạt động → Lệnh chuyển hàng → Nội bộ* → **Mới**, từ *Vị trí gia
công* về *WH/Stock*, sản phẩm và số lượng → **Xác nhận**. Chủ hàng giữ nguyên.

### 3.4 Hóa đơn của Nhà Bàng — kế toán

1. Trên đơn mua → **Tạo hóa đơn**.
2. **Ngày hóa đơn**, **Thông tin hoá đơn** (số chứng từ của Nhà Bàng) → **Xác nhận**.

Phải thấy: **Nợ 6277 / Có 331** cho phí gia công (không có VAT: Nhà Bàng là hộ kinh doanh). Phí này thu lại trong phí
gia công xuất cho Công ty TM (1.6).

---

## Trường hợp 4 — Công ty tự sản xuất và tự bán

Hàng làm từ vật tư của công ty và công ty bán. Vật tư của công ty là hàng công ty mua của người bán thật.

### 4.1 Mua hàng

1. *Mua hàng → Đơn hàng → Yêu cầu báo giá* → **Mới**.
2. **Nhà cung cấp**: người bán thật, người phát hành hóa đơn điện tử. Không bao giờ là Công ty TM cho hàng Công ty TM chỉ
   gửi sang (hàng đó nhận theo 1.1).
3. Các dòng, đơn giá → **Xác nhận đơn hàng** → **Nhận sản phẩm** → số lượng → **Xác nhận**. In **Phiếu nhập kho**.
4. Khi có hóa đơn điện tử: **Tạo hóa đơn** → **Ngày hóa đơn**, **Thông tin hoá đơn** = số hóa đơn điện tử → đính kèm
   file XML hóa đơn → **Xác nhận**.

Bút toán: nhập kho **Nợ 1520 / Có 3399**; hóa đơn **Nợ 3399, Nợ 1331 / Có 331**.

### 4.2 Sản xuất

1. *Sản xuất → Hoạt động → Lệnh sản xuất* → **Mới**, sản phẩm, số lượng.
2. Thẻ *Thông tin khác*: **Loại hoạt động** *Manufacturing*; **Goods Owner** để trống.
3. **Xác nhận** → *Pick Components* như 1.3 → sản xuất như 1.4.

Phải thấy: *Pick Components* chỉ lấy hàng công ty (chi tiết dòng: **Người phụ trách** trống). Hàng công ty thiếu thì
lệnh chờ; không bao giờ lấy hàng Công ty TM hay hàng của khách. Chọn tự sản xuất hay gia công: xem 1.2a.

Bút toán: **Nợ 1541 / Có 1520** (vật tư), **Nợ 1550 / Có 1541** (thành phẩm, gồm chi phí gia công).

### 4.3 Bán hàng

1. *Bán hàng → Đơn hàng → Báo giá* → **Mới** → khách hàng, sản phẩm, giá → **Xác nhận**.
2. Nút **Giao hàng** → **Kiểm tra tình trạng còn hàng** (chỉ hàng công ty) → **Xác nhận**. In **Phiếu xuất kho**.
3. **Tạo hoá đơn** → **Tạo bản nháp** → **Xác nhận**, rồi phát hành hóa đơn điện tử.

Bút toán: giao hàng **Nợ 1599 / Có 1550**; hóa đơn **Nợ 131 / Có 5110, Có 33311**, **Nợ 6320 / Có 1599**.

---

## Trường hợp 5 — Hủy hàng và hạ loại

### 5.1 Từ lệnh sản xuất

1. Trên lệnh sản xuất: ⚙ **Tác vụ → Loại bỏ**.
2. **Sản phẩm**, **Số lượng**, **Vị trí nguồn** (nơi có hàng, vd. *WH/Pre-Production* cho nguyên phụ liệu).
3. **Người phụ trách** tự điền chủ hàng của lệnh khi chủ đó có hàng ở vị trí này. Kiểm tra lại.
4. **Vị trí phế phẩm**:
   - *Scrap* để hủy;
   - *Hạ loại 2* để hạ loại: **Downgrade To** hiện sản phẩm loại 2 (lần đầu thì chọn).
5. Bấm nút xác nhận hủy.

### 5.2 Trong kho

1. *Tồn kho → Hoạt động → Điều chỉnh → Loại bỏ* → **Mới**.
2. **Sản phẩm**, **Số lượng**, **Vị trí nguồn**, **Người phụ trách** = chủ của hàng (để trống nếu là hàng công ty).
3. **Vị trí phế phẩm** như 5.1 → **Xác nhận**.

Phải thấy: hạ loại tạo hàng loại 2 **cùng chủ** với hàng bị hạ loại.

Bút toán: hủy hàng công ty **Nợ 6328 / Có 1520 hoặc 1550**; hạ loại hàng công ty **Nợ 1550 / Có 1550** (giá trị chuyển
sang hàng loại 2); hàng của chủ khác: **không có**.

---

## Trường hợp 6 — Kiểm kê

1. *Tồn kho → Hoạt động → Điều chỉnh → Hàng tồn kho vật lý*.
2. Lọc hoặc tìm theo sản phẩm, vị trí. Mỗi dòng là **một sản phẩm, một vị trí, một chủ hàng**.
3. **Số lượng đã đếm** ghi vào dòng đúng chủ hàng. Sản phẩm có hàng của hai chủ thì có hai dòng: đếm riêng từng dòng.
4. Hàng có thực tế mà chưa có dòng: **Mới** → **Vị trí**, **Sản phẩm**, **Người phụ trách** (chọn ngay: lưu rồi
   không sửa được), **Số lượng đã đếm**.
5. Chọn các dòng → **Áp dụng**.

Bút toán: hàng công ty, thiếu **Nợ 6320 / Có tài khoản kho**, thừa **Nợ tài khoản kho / Có 7110**; hàng của chủ khác:
**không có** (chênh lệch báo cho chủ hàng).

---

## Trường hợp 7 — Công ty dùng hàng của Công ty TM (vd. đồng phục)

Hàng Công ty TM chỉ thành của công ty khi Công ty TM bán cho công ty, có hóa đơn điện tử. Hàng không di chuyển; hai
chứng từ đổi chủ hàng.

1. Thống nhất số lượng, giá; Công ty TM xuất hóa đơn điện tử cho công ty.
2. **Ra khỏi hàng Công ty TM**: *Tồn kho → Hoạt động → Lệnh chuyển hàng → Giao hàng* → **Mới** → **Loại hoạt động**
   *Xuất hàng Công ty TM*, **Địa chỉ giao hàng** *Công ty TNHH DV TM Quang Phương*, sản phẩm, số lượng → **Đánh dấu
   việc cần làm** → **Kiểm tra tình trạng còn hàng** → **Xác nhận**.
3. **Vào hàng công ty**: *Mua hàng → Đơn hàng → Yêu cầu báo giá* → **Mới** → **Nhà cung cấp** *Công ty TNHH DV TM Quang
   Phương*, cùng sản phẩm, đơn giá theo hóa đơn → **Xác nhận đơn hàng** → **Nhận sản phẩm** → **Xác nhận**. Đây là
   trường hợp duy nhất đơn mua ghi Công ty TM: Công ty TM thật sự bán cho công ty, có hóa đơn điện tử.
4. **Tạo hóa đơn** → **Thông tin hoá đơn** = số hóa đơn điện tử → đính kèm XML → **Xác nhận**.
5. Xuất dùng: *Tồn kho → Hoạt động → Lệnh chuyển hàng → Giao hàng* → **Mới** → **Loại hoạt động** *Consumption* →
   sản phẩm → **Đánh dấu việc cần làm** → **Kiểm tra tình trạng còn hàng** → **Xác nhận**.

Bút toán: nhập kho **Nợ 1550 / Có 3399**; hóa đơn **Nợ 3399, Nợ 1331 / Có 331**; xuất dùng **Nợ 6273 / Có 1550**.

---

## Trường hợp 8 — Bán hàng loại 2 cho nhân viên

**Tạm ngưng** cho tới khi Công ty TM sẵn sàng xuất hóa đơn. Hàng loại 2 (SCND…) là hàng của Công ty TM, nên **Công ty TM
bán**, xuất hóa đơn điện tử cho từng nhân viên. Công ty chỉ giao hàng:

1. *Tồn kho → Hoạt động → Lệnh chuyển hàng → Giao hàng* → **Mới** → **Loại hoạt động** *Xuất hàng Công ty TM*.
2. **Địa chỉ giao hàng**: nhân viên. **Người phụ trách** tự hiện *Công ty TNHH DV TM Quang Phương*.
3. Sản phẩm loại 2 và số lượng → **Đánh dấu việc cần làm** → **Kiểm tra tình trạng còn hàng** → **Xác nhận**. In
   **Phiếu xuất kho** và **Biên bản giao nhận**.

Bút toán trong sổ công ty: **không có**. Công ty TM xuất hóa đơn cho nhân viên và thu tiền.
