# Hướng dẫn import CSV/Excel

Tài liệu này dùng cho Odoo 17 Community và các mẫu trong `templates/`. Luôn
thử trên database staging trước khi import production.

## Quy tắc chung

- Odoo 17 Community hỗ trợ import CSV và XLSX trong màn hình Import. CSV UTF-8
  (Comma delimited) là định dạng khuyến nghị để kiểm soát encoding/dấu phân cách;
  nếu dùng XLSX, hãy kiểm tra sheet đang chọn và bỏ các dòng/cột phụ.
- Dùng ngày `YYYY-MM-DD`, số tiền dùng dấu chấm thập phân, không đặt ký hiệu
  tiền tệ trong ô.
- Cột `External ID` là khóa chống trùng. Giữ nguyên ID khi cập nhật; không dùng
  lại ID cho bản ghi khác.
- Trên màn hình Import, bật **Track history during import** khi cần audit, sau
  đó chọn **Test** trước khi bấm **Import**. Lưu lại file lỗi nếu Odoo trả về.
- Trường quan hệ nên dùng `External ID` (ví dụ `Customer/External ID`) để không
  phụ thuộc tên trùng.

## Tải template trực tiếp trong Odoo

Sau khi module IntraStack CRM được nâng cấp lên phiên bản `17.0.2.2.0`, mở màn
hình **Import records** của loại dữ liệu cần import. Trong khối **Need Help?**,
Odoo sẽ hiển thị các nút **IntraStack Template - ...** tương ứng. Bấm nút để tải
file CSV mẫu, thay dữ liệu ví dụ bằng dữ liệu thật, giữ nguyên hàng tiêu đề rồi
upload lại ngay trên màn hình đó.

- Contacts: Customer Companies, Company Contacts, Candidates và Recruiter Vendors.
- CRM: CRM Opportunities.
- Employees: Employees and Roles.
- Staffing Operations: Requirements, Candidate Submissions, Interview Schedule
  và Staffing Placements.
- Banks và Contact Bank Accounts: template riêng để tránh map SWIFT/BIC sai vào
  tên ngân hàng.

Template chuẩn của Odoo cho Customers, Leads/Opportunities và Employees vẫn được
giữ lại. Với quy trình IntraStack, ưu tiên nút có tiền tố **IntraStack Template**
vì file đó có sẵn các cột tùy chỉnh và quan hệ theo BRD.

## Thứ tự import bắt buộc

1. Công ty/khách hàng: `crm_companies_import.csv`.
2. Liên hệ thuộc công ty: `crm_contacts_import_template.csv`.
3. Candidate: `crm_candidates_import.csv`.
4. Recruiter/vendor companies: `crm_recruiter_vendors_import.csv`.
5. Employee master data: `employees_import.csv`; sau đó HR Manager tạo internal
   user, Sync IntraStack Access và gửi invitation thủ công.
6. Cơ hội: `crm_opportunities_import.csv`.
7. Staffing requirements: `staffing_requirements_import.csv`.
8. Candidate submissions: `staffing_candidate_submissions_import.csv`.
9. Interviews: `staffing_interviews_import.csv`.
10. Placements: `staffing_placements_import.csv`.

Nếu cần dữ liệu ngân hàng, import sau Contacts theo hai bước tùy chọn:

11. Banks: `banks_import.csv`.
12. Bank Accounts: `contact_bank_accounts_import.csv`.

Nếu import tất cả trong một file, hãy bảo đảm các bản ghi được tham chiếu đã
tồn tại trước; Odoo không tự suy đoán liên kết theo tên gần giống.
Ở bước mapping, kiểm tra từng cột có dấu tick; nếu ngôn ngữ giao diện không phải
English, map thủ công theo trường tương ứng thay vì dựa hoàn toàn vào tên header.

## CRM và pipeline

Khi tạo opportunity, `Deal Classification` sẽ tự định tuyến sang team và stage
đầu tiên tương ứng: Staffing, Consulting, Subcontracting hoặc Managed Services.
Không ghi đè `Sales Team`/`Stage` sai pipeline; server sẽ từ chối bản ghi hoặc tự
đưa về pipeline đúng. Khi muốn đánh dấu Won, phải có customer, classification,
service category, expected value > 0, sales team, stage và contract start date.

## Staffing

Requirement cần có CRM Opportunity (đã phân loại Staffing), Customer, Role / Job
Title và Positions. Recruiter mặc định là người import; có thể map thêm trường
Recruiter bằng email/login của người dùng nội bộ. Luồng vận hành là
`Open → Sourcing → Interview → Offer → Filled`; placement chỉ được kích hoạt từ
ngày bắt đầu hợp đồng trở đi.

Submission cần Candidate, Requirement và recruiter login đã tồn tại. Interview
cần Submission/Requirement đã tồn tại; thời gian được diễn giải theo timezone
của user import. Placement template cố ý không có Status: bản ghi phải được tạo
ở Draft rồi đi qua Submit for Approval, Confirm và Activate bằng các button để
validation contract/rate/date được thực thi.

Không import trực tiếp Quotation, Sales Order hoặc Delivery Project trong vận
hành thông thường. Hãy tạo quotation từ CRM và confirm Sales Order để hệ thống
tự giữ liên kết CRM → Order → Project và clone task template.

### Lưu ý khi source CSV có `bank_ids/*`

Không map `bank_ids/bank` trực tiếp trong màn hình import Contacts. Các giá trị
như `GEBABEBB` hoặc `BEBABEBB` là mã SWIFT/BIC, nhưng Odoo có thể auto-map cột
này sang một relational/accounting field không đúng và báo “No matching records
found”. Hãy bấm dấu **X** để bỏ map `bank_ids/bank` và
`bank_ids/acc_number`, import Contacts trước, rồi dùng `banks_import.csv` và
`contact_bank_accounts_import.csv` nếu thật sự cần lưu tài khoản ngân hàng.

## Kiểm tra sau import

- Tìm theo External ID và kiểm tra customer/contact, team, stage, owner.
- Mở opportunity và kiểm tra quotation template đúng loại dịch vụ.
- Với Staffing, mở requirement và kiểm tra margin, candidate submissions và
  interview schedule.
- Xuất lại danh sách vừa import để đối chiếu số dòng; không xóa bản ghi trực tiếp
  nếu chưa có backup.

## Export dữ liệu

1. Mở danh sách Contacts, Opportunities hoặc Staffing Requirements và chuyển
   sang **List view**.
2. Lọc đúng phạm vi dữ liệu cần xuất.
3. Chọn checkbox của ít nhất một bản ghi; menu **Action** sẽ xuất hiện.
4. Chọn **Action → Export**. Nếu không thấy Export, quản trị viên cần kiểm tra
   quyền Export của user.
5. Chọn các field cần thiết. Nếu file dùng để cập nhật/import trở lại, luôn thêm
   **External ID** và chọn chế độ export tương thích import.
6. XLSX phù hợp cho business review; CSV phù hợp cho tích hợp/trao đổi có kiểm
   soát. Không lưu dữ liệu khách hàng/candidate tại thiết bị hoặc cloud cá nhân.

Nút Import thường chỉ hiện ở List view trong menu bánh răng/Action cạnh tiêu đề
danh sách (một số giao diện đặt dưới Favorites → Import records). Export chỉ hiện
sau khi đã chọn ít nhất một record.
