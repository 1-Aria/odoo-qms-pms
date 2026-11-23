# Contract Forms — Research and Drafts

v0.1 (draft for review) · Nov 20, 2026 · @Peter

What Vietnamese law requires a labour contract, a probation contract, a training contract and an annex to state,
and a draft of each form's Vietnamese wording for Peter and HR to check. The company owns the wording; a labour
lawyer should read it once before first use. How Odoo holds and prints these forms is the subject of
*Contract Documents — Design Note* (v0.2 to follow, built on this document); this document says nothing about
modules.

This is research for drafting, not legal advice.

**Supersedes** §2 (*The forms*) of *Contract Documents — Design Note v0.1*, with these corrections:

| v0.1 said | Correct | Source |
| --- | --- | --- |
| The employer's signer is set by Decree 145/2020 Art. 18 | Decree 145 Art. 18 concerns deposits of labour-leasing firms. The signer is set by **Labor Code Art. 18.3**: the enterprise's legal representative or a person lawfully authorised, who may not authorise anyone further (18.5) | Labor Code Art. 18; Decree 145 text |
| Circular 10/2020 Art. 3, from memory | Read in full. It adds the parties' phone and e-mail (if any), the classification of allowances and supplements (b1, b2, c1, c2), and requires bonuses and welfare items in **a separate section** of the contract | Circular 10 Art. 3 |
| Whether to state each side's insurance rates was open | Circular 10 Art. 3.9 states the insurance item as "theo quy định của pháp luật…": a reference to the law is the content. No rates | Circular 10 Art. 3.9 |
| An SI exposure on training and casual work, to confirm | Dropped: neither is subject to compulsory SI (Peter, 2026-11-20) | — |
| The training contract's repayment clause, to decide | Part of the training form by design, used per contract; not used for garment workers (Peter, 2026-11-20) | §6.4 |
| The probation clause as its own article, renumbering the rest | A clause inside article 1, so every form keeps fixed article numbers and an annex can cite them | §5.1 |

---

## 1. Sources

| Text | Articles | Read from |
| --- | --- | --- |
| Labor Code 2019 (45/2019/QH14) | 14, 18, 20, 21, 22, 24–27, 33, 61, 62, 97 | hethongphapluat.com, one page per article (third-party copy, 2026-11-20) |
| Circular 10/2020/TT-BLĐTBXH | 3, 12 | Peter's copy, `Odoo-Build/labor-law/Thông-tư-10-2020-TT-BLĐTBXH.docx` |
| Decree 145/2020/NĐ-CP | 3, 10, 54, the sample domestic-work contract in its annex | Peter's copy, `Odoo-Build/labor-law/Nghị-định-145-2020-NĐ-CP.docx` |
| Vocational Education Law 2025 (124/2025/QH15) | 43 (amends Labor Code Art. 61.3, from 1 Jan 2026) | hethongphapluat.com (third-party copy). **The official text is still to be checked** |

thuvienphapluat.vn refuses automated reads. No amendment to Circular 10/2020 was found.

## 2. What every labour contract must state

Labor Code Art. 21.1 lists the items; Circular 10/2020 Art. 3 details each one. Quotations are from the Circular.

| Item | Art. 21.1 | Circular 10 Art. 3 | For the form |
| --- | --- | --- | --- |
| Employer | a | 3.1.a–b: the name and address as in the enterprise registration certificate; "số điện thoại, địa chỉ thư điện tử (nếu có)" | Name, enterprise code, head-office address, phone, e-mail if any |
| Employer's signer | a | 3.1.c: name and title of the person with authority under Labor Code Art. 18.3 | The legal representative (the director), or a person authorised in writing: then the authorisation's number and date |
| Employee | b | 3.2.a: "họ tên, ngày tháng năm sinh, giới tính, địa chỉ nơi cư trú, số điện thoại, địa chỉ thư điện tử (nếu có), số thẻ Căn cước công dân … do cơ quan có thẩm quyền cấp"; 3.2.b: work permit for a foreigner; 3.2.c: the legal representative of a person under 15 | Name, date of birth, sex, residence, phone and e-mail if any, ID number. Issue date and place are not required by the Circular; Decree 145's own sample contract prints them ("cấp ngày … tại"), so the form follows it |
| Work and workplace | c | 3.3: the work the employee must do; the workplace, and every place where the employee works regularly | Job title and duties; workplace address |
| Term | d | 3.4: duration in months or days, start and end (fixed-term); start (indefinite) | |
| Salary | đ | 3.5.a: "mức lương tính theo thời gian của công việc hoặc chức danh theo thang lương, bảng lương"; for piece-rate pay, the time-based salary from which the unit price is set | The base salary, as an amount |
| Allowances | đ | 3.5.b: **b1** compensating conditions, complexity, living conditions, attraction; **b2** linked to the work and its results | As amounts where fixed |
| Other supplements | đ | 3.5.c: **c1** "xác định được mức tiền cụ thể … trả thường xuyên"; **c2** "không xác định được mức tiền cụ thể … gắn với quá trình làm việc, kết quả thực hiện công việc của người lao động" | c1 as amounts; **c2 named, with the rule by reference: productivity and performance pay** (§3) |
| Bonuses and welfare | — | 3.5, last paragraph: Art. 104 bonuses, meal allowance, fuel, phone, travel, housing, childcare, family events and similar "thì ghi thành mục riêng trong hợp đồng lao động" | A separate article |
| Payment form and period | đ | 3.5.d–đ, by Labor Code Art. 96 and 97 | Transfer or cash (Decree 145 Art. 54.2: by transfer, the employer pays the bank fees); monthly, on a fixed date (Art. 97.2) |
| Raises | e | 3.6: conditions, timing, the salary after the raise, by agreement or by the collective agreement or the employer's rules | By reference to the pay regulation |
| Working and rest time | g | 3.7: by agreement, or by the work rules, the employer's rules, the collective agreement and the law | By reference to the work rules, with the weekly norm |
| Protective equipment | h | 3.8: the kinds of personal protective equipment, by agreement or the employer's rules and safety law | By reference to the company's rules |
| SI, HI, UI | i | 3.9: "theo quy định của pháp luật về lao động, bảo hiểm xã hội, bảo hiểm y tế và bảo hiểm thất nghiệp" | A reference to the law |
| Training | k | 3.10: each side's rights, duties and benefits in time and cost of training | A short clause; employer-funded training by a separate Art. 62 contract |

**Also relevant:**

- **Form** (Art. 14): written, two copies, one for each side. An electronic contract under the e-transactions law has
  the same effect.
- **Term** (Art. 20): indefinite, or fixed-term up to 36 months. After a fixed-term contract one more fixed-term
  contract may follow, then only indefinite.
- **Annex** (Art. 22): part of the contract with the same effect. It may detail or amend clauses, **never the term**.
  An amending annex states the clauses changed and the date it takes effect.
- **Changes** (Art. 33): the side asking gives at least 3 working days' notice; agreed changes are made by an annex
  or a new contract; without agreement the contract continues.
- **The employee's side** (Art. 18.4): an employee aged 15 to under 18 signs with their legal representative's
  written consent. The form needs a variant if the company hires anyone under 18 (§7).
- **Severance base** (Circular 10 Art. 12.3): the average of the base salary, the b1 allowances and the c1
  supplements over the last 6 months. Productivity and performance pay, as c2, are outside it.
- **Labour register** (Decree 145 Art. 3): every employer keeps one, on paper or electronically, with name, sex,
  date of birth, nationality, residence, ID, qualification and skill level, position, contract type, start date, SI,
  salary, raises, leave days, OT hours, training, discipline, accidents, end date and reason. Most of it will be in
  Odoo once the contract data is entered; a printable register is a natural later report.

## 3. The salary clause, and what it leaves to the pay regulation

**Peter's decision (2026-11-20):** the contract discloses productivity pay but not its detail, which changes; the
detail lives in a separate document, the company's pay regulation, and the contract refers to it in general terms.

The law's own category fits exactly: productivity pay and performance pay are **c2 supplements**, amounts that
cannot be fixed in advance and depend on the work and its results (Circular 10 Art. 3.5.c2). The contract therefore
names them and states that they are paid under the pay regulation. It states no level, grade or amount: a level
review every 6 months changes nothing in the contract, and no fixed amount sits in the contract to be counted in the
SI base. This replaces Pay Policy §3.6's "productivity pay at her certified level" in the appendix; the change goes
into Pay Policy v0.8.

| Pay item (garment scheme) | Category | In the contract |
| --- | --- | --- |
| Base salary `BASE` (workers 4,500,000 from 1 Nov 2026; staff by grade) | 3.5.a | The amount, in figures and words |
| Fixed allowances (none today; `DUTY` and `PHONE` are inactive options) | b1 / c1, or welfare | The amount; a phone allowance under welfare |
| Productivity pay `PROD`, performance pay `PERF` | c2 | Named, "theo Quy chế trả lương của Công ty" |
| Efficiency bonus, one-time bonus, annual bonus | Art. 104 bonuses | The separate bonus and welfare article, by reference to the bonus regulation |
| Overtime and night pay | Statutory | By reference to the Labor Code |
| Training allowance `TRAIN` (training contract) | Pay of a learner who works (Art. 61.5) | The amount, as agreed |

**The document referred to** must exist and be published before the contracts refer to it. The Pay Policy names its
official form: the *salary scale and pay table* (Art. 93), the *pay regulation* (quy chế lương) and the *bonus
regulation* (Art. 104), discussed with the worker representative organisation and published. The drafts call them
*Quy chế trả lương* and *Quy chế thưởng*; HR replaces these with the titles the company actually issues.

## 4. Which form for which contract

| Contract type | Form | Notes |
| --- | --- | --- |
| Labour contract (`VN_LABOUR`) | Labour contract | Fixed-term or indefinite by its end date. With a probation clause when probation is agreed inside it (skilled workers: 6 working days, Pay Policy §14.2) |
| Probation contract (`VN_PROBATION`) | Probation contract | Office and management (Pay Policy §14.2). Contents: Art. 24.2 |
| Training contract (`VN_TRAINING`) | Training contract | Learners and unskilled workers, 2–3 months, practice at most 3 months (Art. 61.2) |
| Casual (`VN_CASUAL`) | None | Peter, 2026-11-20 |
| Any of the three above, changed | Annex | Never for a change of term, type or probation form: a new contract instead (Art. 22.2) |

## 5. Conventions of the drafts

### 5.1 Layout and markers

- `[G]`: generic wording, valid for any company. `[C]`: the garment company's wording, for HR to check against the
  work rules and regulations actually in force.
- `{…}`: a value filled from Odoo (§5.2). `{nếu …} … {hết}`: printed only when the condition holds.
- **Fixed article numbers:** each form's articles are numbered once and never shift. Optional content (the probation
  clause, the repayment clause) is a clause inside an article, or an article left out at the end, so an annex can
  cite "Điều 4" and mean the same article in every contract of that form.
- A4 portrait, Times New Roman 13, the national motto centred, two copies.

### 5.2 Values

| Placeholder | Meaning |
| --- | --- |
| `{so_hd}` | The contract's number, e.g. `0012/2026/HĐLĐ-QP` |
| `{noi_ky}`, `{ngay_ky}` | Place (the company's province) and date of signing |
| `{ten_cong_ty}`, `{mst}`, `{dia_chi_cong_ty}`, `{dt_cong_ty}`, `{email_cong_ty}` | The employer, as registered |
| `{nguoi_dai_dien}`, `{chuc_danh_dai_dien}`, `{uy_quyen}` | The signer, their title, and the authorisation (number, date) when the signer is not the legal representative |
| `{ho_ten}`, `{gioi_tinh}`, `{ngay_sinh}`, `{quoc_tich}` | The employee |
| `{so_cccd}`, `{ngay_cap}`, `{noi_cap}` | ID number, issue date, issuing authority |
| `{thuong_tru}`, `{noi_o}` | Permanent address; current address when different |
| `{dt_nld}`, `{email_nld}` | Employee's phone and e-mail, when known |
| `{chuc_danh}`, `{dia_diem_lam_viec}` | Job title; workplace address |
| `{ngay_bat_dau}`, `{ngay_ket_thuc}`, `{so_thang}` | Term |
| `{ngay_het_thu_viec}`, `{thoi_gian_thu_viec}`, `{ty_le_thu_viec}`, `{nhom_cong_viec}` | Probation: end, length (days or working days), pay rate, the job category of Art. 25 |
| `{luong}`, `{luong_bang_chu}` | Base salary, in figures and words |
| `{phu_cap}` | Each fixed allowance with its amount; "Không" when none |
| `{bo_sung_c1}`, `{bo_sung_c2}` | Fixed supplements with amounts; variable supplements by name |
| `{hinh_thuc_tra_luong}` | "chuyển khoản vào tài khoản ngân hàng mang tên Bên B" or "tiền mặt" |
| `{thoi_gian_cam_ket}`, `{chi_phi_dao_tao}` | Training contract: commitment period in months and the training cost, when the repayment clause is used |

### 5.3 Common header `[G]`

```text
                    CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM
                        Độc lập – Tự do – Hạnh phúc
                        ───────────────────────────
                                                   {noi_ky}, ngày {dd} tháng {mm} năm {yyyy}

                                  {TÊN MẪU}
                                Số: {so_hd}

Căn cứ Bộ luật Lao động số 45/2019/QH14 ngày 20 tháng 11 năm 2019 và các văn bản hướng dẫn thi hành;
{căn cứ riêng của mẫu}
Căn cứ nhu cầu và năng lực của hai bên,

Chúng tôi gồm:

BÊN A: NGƯỜI SỬ DỤNG LAO ĐỘNG
Tên doanh nghiệp:     {ten_cong_ty}
Mã số doanh nghiệp:   {mst}
Địa chỉ trụ sở chính: {dia_chi_cong_ty}
Điện thoại:           {dt_cong_ty}            {nếu có email}Email: {email_cong_ty}{hết}
Người đại diện:       Ông/Bà {nguoi_dai_dien}          Chức danh: {chuc_danh_dai_dien}
{nếu ủy quyền}(Theo Giấy ủy quyền số {uy_quyen}){hết}

BÊN B: {NGƯỜI LAO ĐỘNG | NGƯỜI HỌC NGHỀ, TẬP NGHỀ}
Họ và tên:            {ho_ten}                         Giới tính: {gioi_tinh}
Ngày sinh:            {ngay_sinh}                      Quốc tịch: {quoc_tich}
Số CCCD:              {so_cccd}    Ngày cấp: {ngay_cap}    Nơi cấp: {noi_cap}
Nơi thường trú:       {thuong_tru}
{nếu khác}Nơi ở hiện tại:       {noi_o}{hết}
{nếu có}Điện thoại:           {dt_nld}{hết}            {nếu có}Email: {email_nld}{hết}
```

### 5.4 Common closing `[G]`

```text
Điều {cuối}. Điều khoản thi hành
1. Những vấn đề không ghi trong hợp đồng này thực hiện theo Nội quy lao động, các quy chế của Công ty,
   thỏa ước lao động tập thể (nếu có) và quy định của pháp luật.
2. Phụ lục hợp đồng do hai bên ký kết là một bộ phận của hợp đồng này và có hiệu lực như hợp đồng này.
3. Hợp đồng này được lập thành 02 bản có giá trị pháp lý như nhau, mỗi bên giữ 01 bản, và có hiệu lực
   từ ngày {ngay_bat_dau}.

             BÊN B                                                  BÊN A
   {NGƯỜI LAO ĐỘNG | NGƯỜI HỌC NGHỀ, TẬP NGHỀ}                {chuc_danh_dai_dien}
       (Ký, ghi rõ họ tên)                              (Ký, ghi rõ họ tên, đóng dấu)




          {ho_ten}                                         {nguoi_dai_dien}
```

---

## 6. Drafts

### 6.1 Labour contract

Title *HỢP ĐỒNG LAO ĐỘNG*; number `{nnnn}/{yyyy}/HĐLĐ-{mã công ty}`. Twelve articles, always the same numbers.

```text
Hai bên thỏa thuận giao kết hợp đồng lao động và cam kết thực hiện đúng các điều khoản sau đây:

Điều 1. Loại hợp đồng, thời hạn hợp đồng và thử việc                                         [G]
1. Loại hợp đồng: {Hợp đồng lao động xác định thời hạn {so_thang} tháng
                  | Hợp đồng lao động không xác định thời hạn}.
2. Thời hạn hợp đồng: {từ ngày {ngay_bat_dau} đến hết ngày {ngay_ket_thuc}
                       | bắt đầu từ ngày {ngay_bat_dau}}.
3. Thử việc: {nếu có thử việc}
   a) Thời gian thử việc: {thoi_gian_thu_viec}, từ ngày {ngay_bat_dau} đến hết ngày {ngay_het_thu_viec}.
   b) Tiền lương thử việc bằng {ty_le_thu_viec}% mức lương của công việc quy định tại Điều 3.
   c) Trong thời gian thử việc, mỗi bên có quyền hủy bỏ hợp đồng này mà không cần báo trước và không
      phải bồi thường.
   d) Khi kết thúc thời gian thử việc, Bên A thông báo kết quả thử việc cho Bên B. Trường hợp đạt yêu cầu,
      hai bên tiếp tục thực hiện hợp đồng này; trường hợp không đạt yêu cầu, hợp đồng này chấm dứt.
   {không có thử việc} Không áp dụng.

Điều 2. Công việc và địa điểm làm việc
1. Chức danh công việc: {chuc_danh}.                                                          [G]
2. Công việc phải làm: các công việc của chức danh theo bản mô tả công việc, định mức lao động và sự
   phân công, điều hành của người quản lý trực tiếp.                                          [C]
3. Địa điểm làm việc: {dia_diem_lam_viec}.                                                    [G]

Điều 3. Tiền lương, phụ cấp lương và các khoản bổ sung khác                                   [G]
1. Mức lương theo công việc hoặc chức danh: {luong} đồng/tháng (Bằng chữ: {luong_bang_chu}).
2. Phụ cấp lương: {phu_cap}.
3. Các khoản bổ sung khác:
   {mỗi khoản c1: - {tên}: {số tiền} đồng/tháng.}
   {mỗi khoản c2: - {tên}: trả theo năng suất, kết quả thực hiện công việc của Bên B, theo Quy chế trả
     lương của Công ty.}
4. Tiền lương làm thêm giờ, làm việc vào ban đêm: theo quy định của Bộ luật Lao động.
5. Hình thức trả lương: {hinh_thuc_tra_luong}.
6. Kỳ hạn trả lương: mỗi tháng một lần, vào ngày 10 của tháng kế tiếp; nếu trùng ngày nghỉ thì trả vào
   ngày làm việc liền trước.                                                                   [C]

Điều 4. Tiền thưởng và phúc lợi                                                               [G]
1. Tiền thưởng: theo Quy chế thưởng của Công ty, căn cứ kết quả sản xuất, kinh doanh và mức độ hoàn
   thành công việc của Bên B.
2. Phúc lợi và các khoản hỗ trợ khác: {mỗi khoản: - {tên}: {số tiền hoặc "theo quy định của Công ty"}}
   | theo quy định của Công ty.

Điều 5. Chế độ nâng bậc, nâng lương                                                           [C]
Bên B được xem xét nâng bậc, nâng lương theo điều kiện, thời gian và mức quy định trong Quy chế trả lương
và thang lương, bảng lương của Công ty. Công ty thông báo kết quả cho Bên B bằng văn bản.

Điều 6. Thời giờ làm việc, thời giờ nghỉ ngơi                                                  [C]
1. Thời giờ làm việc bình thường không quá 08 giờ trong 01 ngày và không quá 48 giờ trong 01 tuần; ca làm
   việc, giờ bắt đầu, giờ kết thúc và thời gian nghỉ giữa ca theo Nội quy lao động và lịch làm việc của
   bộ phận.
2. Làm thêm giờ: khi có nhu cầu, Bên A được tổ chức làm thêm giờ khi Bên B đồng ý, trong giới hạn của
   pháp luật.
3. Nghỉ hằng tuần, nghỉ hằng năm, nghỉ lễ, tết, nghỉ việc riêng và nghỉ không hưởng lương: theo Bộ luật
   Lao động và Nội quy lao động của Công ty.

Điều 7. Trang bị bảo hộ lao động                                                               [C]
Bên B được cấp phát trang bị bảo hộ lao động và đồng phục phù hợp với công việc theo quy định của Công ty
và pháp luật về an toàn, vệ sinh lao động. Đồng phục và trang bị được cấp là tài sản của Công ty; Bên B
bảo quản, sử dụng đúng mục đích và hoàn trả khi chấm dứt hợp đồng theo Nội quy lao động.

Điều 8. Bảo hiểm xã hội, bảo hiểm y tế, bảo hiểm thất nghiệp                                  [G]
Hai bên tham gia bảo hiểm xã hội bắt buộc, bảo hiểm y tế và bảo hiểm thất nghiệp theo quy định của pháp
luật về lao động, bảo hiểm xã hội, bảo hiểm y tế và bảo hiểm thất nghiệp. Phần đóng của Bên B được Bên A
khấu trừ vào tiền lương hằng tháng.

Điều 9. Đào tạo, bồi dưỡng, nâng cao trình độ, kỹ năng nghề                                    [G]
Bên A đào tạo, bồi dưỡng Bên B theo yêu cầu công việc. Bên B tham gia đầy đủ các chương trình do Bên A
tổ chức. Khi Bên B được đào tạo bằng kinh phí của Bên A, hai bên ký hợp đồng đào tạo nghề theo Điều 62
Bộ luật Lao động.

Điều 10. Quyền và nghĩa vụ của Bên B                                                          [C]
1. Được trả lương đầy đủ, đúng hạn và hưởng các chế độ theo hợp đồng này, các quy chế của Công ty và
   pháp luật.
2. Hoàn thành công việc được giao; chấp hành Nội quy lao động, quy định về an toàn, vệ sinh lao động và
   sự điều hành hợp pháp của Bên A.
3. Bồi thường thiệt hại khi làm hư hỏng, mất tài sản của Công ty theo Nội quy lao động và pháp luật.
4. Thông báo cho Bên A khi thay đổi nơi cư trú, số điện thoại hoặc tài khoản ngân hàng.

Điều 11. Quyền và nghĩa vụ của Bên A                                                          [C]
1. Bố trí, điều hành công việc; khen thưởng và xử lý kỷ luật lao động theo Nội quy lao động và pháp luật.
2. Trả lương đầy đủ, đúng hạn; bảo đảm điều kiện làm việc, an toàn, vệ sinh lao động.
3. Đóng bảo hiểm xã hội, bảo hiểm y tế, bảo hiểm thất nghiệp và thực hiện các nghĩa vụ khác theo hợp đồng
   này và pháp luật.

Điều 12. Điều khoản thi hành                                                    (common closing)
```

### 6.2 Probation inside the labour contract

Article 1, clause 3 above. Art. 25 caps the length by job: 6 working days for other work (skilled workers, Pay
Policy §14.2), 30 days for intermediate-level, technical and clerical work, 60 days for college level and above,
180 days for enterprise managers; once per job. Art. 26: at least 85% of the job's salary. The garment company pays
100% to every pay group (Peter, 2026-11-21; `vn.policy.probation_rate` 1.0 from garment step 9). The form prints
whatever the parameter holds on the start date. Clause 3.b is kept at 100% too, so the clause reads the same for
every rate.

### 6.3 Probation contract

Title *HỢP ĐỒNG THỬ VIỆC*; number `{nnnn}/{yyyy}/HĐTV-{mã công ty}`. Art. 24.2: the period and items a, b, c, đ, g, h
of Art. 21.1. No raise, insurance or training article. Seven articles.

```text
Hai bên thỏa thuận giao kết hợp đồng thử việc với các điều khoản sau đây:

Điều 1. Thời gian thử việc                                                                    [G]
Từ ngày {ngay_bat_dau} đến hết ngày {ngay_ket_thuc} ({thoi_gian_thu_viec}), đối với công việc
{chuc_danh}, thuộc nhóm {nhom_cong_viec}. Thời gian thử việc không vượt quá thời gian tối đa quy định
tại Điều 25 Bộ luật Lao động đối với công việc này.

Điều 2. Công việc và địa điểm làm việc                              (as the labour contract, Điều 2)

Điều 3. Tiền lương thử việc                                                                   [G]
1. Mức lương của công việc: {luong} đồng/tháng; phụ cấp lương: {phu_cap}.
2. Tiền lương thử việc bằng {ty_le_thu_viec}% mức lương của công việc, tức {luong_thu_viec} đồng/tháng
   (Bằng chữ: {…}).
3. Các khoản bổ sung khác: {mỗi khoản c2: - {tên}: theo Quy chế trả lương của Công ty.}
4. Hình thức trả lương: {hinh_thuc_tra_luong}. Kỳ hạn trả lương: mỗi tháng một lần, vào ngày 10 của
   tháng kế tiếp; nếu trùng ngày nghỉ thì trả vào ngày làm việc liền trước.                    [C]

Điều 4. Thời giờ làm việc, thời giờ nghỉ ngơi                       (as the labour contract, Điều 6)
Điều 5. Trang bị bảo hộ lao động                                    (as the labour contract, Điều 7)

Điều 6. Kết thúc thời gian thử việc                                                            [G]
1. Trong thời gian thử việc, mỗi bên có quyền hủy bỏ hợp đồng này mà không cần báo trước và không phải
   bồi thường.
2. Khi kết thúc thời gian thử việc, Bên A thông báo kết quả thử việc cho Bên B. Trường hợp đạt yêu cầu,
   hai bên giao kết hợp đồng lao động; trường hợp không đạt yêu cầu, hợp đồng này chấm dứt.

Điều 7. Điều khoản thi hành                                                     (common closing)
```

### 6.4 Training contract

Title *HỢP ĐỒNG ĐÀO TẠO* (học nghề, tập nghề để làm việc cho Công ty); number `{nnnn}/{yyyy}/HĐĐT-{mã công ty}`.

**Basis.** Labor Code Art. 61: the employer takes people in to learn (học nghề) or practise (tập nghề, at most 3
months) a trade in order to work for it; learners are at least 14, and 18 for heavy or hazardous work on the
Ministry's list; a learner who works is paid as agreed (61.5); at the end, the two sides sign a labour contract when
the conditions are met (61.6). From 1 Jan 2026, Art. 61.3 reads only that the employer may not charge tuition
(Vocational Education Law 2025, Art. 43.1.b, third-party copy); the 2019 text also required a training contract
under the vocational education law. The company keeps a written contract regardless (Pay Policy §14.2).

**Contents.** No list applies to Art. 61 any more; the draft takes Art. 62.2's list for employer-funded training
(trade; place, duration and pay during training; commitment period; cost and repayment; each side's duties) where
it fits, and Pay Policy §14.2's terms.

**Repayment** (Peter, 2026-11-20): part of the form by design, used per contract. When a contract has no commitment
period, article 7 is left out and the closing becomes article 7. The garment company's worker trainees have none.
For the lawyer: Art. 62's repayment is written for employees trained at the employer's cost, while Art. 61 forbids
tuition. A repayment clause for a learner is therefore safest as a commitment to work after the labour contract is
signed, with the cost stated in advance, which is how the draft words it.

```text
Căn cứ Điều 61 Bộ luật Lao động;                                                               [G]

Hai bên thỏa thuận giao kết hợp đồng đào tạo với các điều khoản sau đây:

Điều 1. Nghề, công việc đào tạo; thời gian và địa điểm                                        [G]
1. Hình thức: {học nghề | tập nghề} để làm việc cho Bên A.
2. Nghề, công việc: {chuc_danh}.
3. Thời gian: từ ngày {ngay_bat_dau} đến hết ngày {ngay_ket_thuc}.
4. Địa điểm: {dia_diem_lam_viec}.
5. Bên A không thu học phí của Bên B.

Điều 2. Nội dung và tổ chức đào tạo                                                            [C]
Bên B được hướng dẫn thực hành các công đoạn của công việc {chuc_danh} tại chuyền sản xuất, dưới sự
hướng dẫn của người được Bên A phân công, theo chương trình và tiêu chuẩn tay nghề của Công ty.

Điều 3. Tiền lương trong thời gian học nghề, tập nghề                                          [G]
Khi trực tiếp hoặc tham gia lao động, Bên B được trả:
1. Trợ cấp đào tạo: {số tiền} đồng/tháng (Bằng chữ: {…}), tính theo số ngày làm việc thực tế trong tháng.
2. {mỗi khoản c2: {tên}: theo Quy chế trả lương của Công ty.}
3. Hình thức trả lương: {hinh_thuc_tra_luong}. Kỳ hạn trả lương: mỗi tháng một lần, vào ngày 10 của
   tháng kế tiếp.                                                                              [C]

Điều 4. Thời giờ học nghề, tập nghề và nghỉ ngơi                    (as the labour contract, Điều 6)
Điều 5. Trang bị bảo hộ lao động                                    (as the labour contract, Điều 7)

Điều 6. Đánh giá và kết thúc                                                                   [C]
1. Bên A đánh giá tay nghề của Bên B trong và khi kết thúc thời gian đào tạo theo tiêu chuẩn của Công ty
   và thông báo kết quả cho Bên B.
2. Bên A có quyền chấm dứt hợp đồng này trong thời gian đào tạo hoặc khi kết thúc nếu Bên B không đạt
   tiêu chuẩn tay nghề, sau khi thông báo kết quả đánh giá cho Bên B.
3. Khi kết thúc thời gian đào tạo, nếu Bên B đạt tiêu chuẩn và đủ điều kiện theo Bộ luật Lao động, hai
   bên giao kết hợp đồng lao động.

{nếu có thời gian cam kết}
Điều 7. Cam kết làm việc và hoàn trả chi phí đào tạo                                           [G]
1. Sau khi giao kết hợp đồng lao động theo Điều 6, Bên B cam kết làm việc cho Bên A ít nhất
   {thoi_gian_cam_ket} tháng.
2. Chi phí đào tạo Bên A bỏ ra cho Bên B là {chi_phi_dao_tao} đồng, gồm: {các khoản chi phí}.
3. Trường hợp Bên B đơn phương chấm dứt hợp đồng lao động trái pháp luật hoặc tự ý nghỉ việc trước khi
   hết thời gian cam kết, Bên B hoàn trả chi phí đào tạo tương ứng với thời gian cam kết còn lại. Khoản
   hoàn trả không khấu trừ vào tiền lương.
{hết}

Điều {7 | 8}. Điều khoản thi hành                                                (common closing)
```

### 6.5 Annex

Title *PHỤ LỤC HỢP ĐỒNG {LAO ĐỘNG | THỬ VIỆC | ĐÀO TẠO}*; number `{nn}/{so_hd}`, `nn` counting the contract's annexes.
Art. 22.2: it states each clause amended and the date it takes effect, and never the term.

```text
Căn cứ Bộ luật Lao động số 45/2019/QH14;                                                       [G]
Căn cứ Hợp đồng {lao động | thử việc | đào tạo} số {so_hd} ký ngày {ngay_ky_hd};
Căn cứ thỏa thuận của hai bên,

{common header, parties}

Hai bên thỏa thuận sửa đổi, bổ sung Hợp đồng số {so_hd} như sau:

Điều 1. Nội dung sửa đổi, bổ sung
{mỗi nội dung thay đổi:}
{i}. Sửa đổi {khoản …} Điều {n} ({tên điều}) như sau:
   {the new text of that clause, as the contract form prints it}

Điều 2. Hiệu lực
1. Phụ lục này là một bộ phận của Hợp đồng số {so_hd} và có hiệu lực kể từ ngày {ngay_hieu_luc}.
2. Các nội dung khác của Hợp đồng số {so_hd} không thay đổi.
3. Phụ lục được lập thành 02 bản có giá trị pháp lý như nhau, mỗi bên giữ 01 bản.

{signatures, as the common closing}
```

Typical annexes: a change of base salary (article 3.1), a new fixed allowance (3.2), a change of job or workplace
(article 2). A change of level or of productivity pay is not an annex: the contract does not state it (§3).

---

## 7. For Peter and HR to check

| # | Point | Note |
| --- | --- | --- |
| 1 | Every `[C]` clause | Against the work rules and regulations actually registered and published |
| 2 | The pay regulation and bonus regulation exist and are published, under which titles | The variable-pay and bonus clauses rest on them (§3) |
| 3 | The payday sentence | Pay Policy §1 sets day 10 of the following month; whether to move to the previous working day when it falls on a day off is a choice |
| 4 | Employees under 18 | If any, the labour contract needs the legal representative's written consent (Art. 18.4) and a line for it |
| 5 | The company's e-mail, and whether to print employees' e-mails | The Circular asks for them "nếu có" |
| 6 | A contract the company uses today | Familiar wording and layout are worth keeping where they do not conflict with these drafts |
| 7 | Labour lawyer, once | The drafts as a whole; the training contract's repayment clause in particular (§6.4); and the official text of Art. 61.3 as amended |

## Change log

| Version | Date | Changes |
| --- | --- | --- |
| 0.1 | 2026-11-20 | First version, split from *Contract Documents — Design Note v0.1* §2 and corrected against Circular 10/2020 and Decree 145/2020 (Peter's copies) and Labor Code Art. 18 and 97; Peter's answers of 2026-11-20 on productivity pay, SI and repayment. |
