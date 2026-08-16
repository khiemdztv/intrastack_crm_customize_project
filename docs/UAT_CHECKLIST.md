# UAT checklist — IntraStack CRM Platform

Chạy trên database staging với Odoo 17 Community, module `intrastack_crm` và
không có demo data. Người kiểm thử ghi **Pass/Fail**, ngày, người thực hiện và
đính kèm ảnh hoặc ID bản ghi.

| ID | Kịch bản nghiệm thu | Kết quả mong đợi | Bằng chứng |
|---|---|---|---|
| UAT-01 | Import công ty/liên hệ bằng CSV mẫu | Bản ghi tạo đúng; tìm được email/điện thoại; External ID không trùng | |
| UAT-02 | Import opportunity Consulting/Cloud | Tự vào P2 Consulting, stage đầu tiên và owner đúng | |
| UAT-03 | Import opportunity Staffing | Tự vào P1 Staffing; tạo được Requirement liên kết | |
| UAT-04 | Đổi classification sau khi tạo | Team/stage được định tuyến lại, không còn sai pipeline | |
| UAT-05 | Chuyển Won khi thiếu dữ liệu | Odoo chặn và chỉ rõ các trường còn thiếu | |
| UAT-06 | Tạo quotation từ opportunity Staffing | Template Rate Card, customer và dòng dịch vụ được điền | |
| UAT-07 | Tạo quotation Consulting | Template SOW đúng; ngày hợp đồng đồng bộ | |
| UAT-08 | Confirm Sales Order | Opportunity Won; đúng một delivery project được tạo; liên kết CRM ↔ SO ↔ Project | |
| UAT-09 | Project task template | Task mẫu của Staffing/Consulting/Managed Services được clone | |
| UAT-10 | Staffing requirement → sourcing | Các trạng thái Open/Sourcing/Interview chuyển được; hoạt động được giao đúng recruiter | |
| UAT-11 | Candidate submission | Có resume, screening, bill/cost rate và margin | |
| UAT-12 | Interview schedule | Có interviewer, lịch, meeting link, outcome/feedback | |
| UAT-13 | Offer/placement | Placement liên kết order/project; không active trước Contract Start | |
| UAT-14 | Tạo nhân viên + user | User nội bộ nhận role bundle, nhận email mời và đăng nhập được sau kích hoạt | |
| UAT-15 | Phân quyền Sales/Recruiter/PM | Mỗi role thấy đúng CRM/Sales/Project/Timesheet; không thấy dữ liệu ngoài phạm vi | |
| UAT-16 | Activities/automation | Activity tạo đúng owner opportunity, đúng classification và deadline | |
| UAT-17 | CEO filters/dashboard | Các filter 4 pipeline, forecast, overdue activity trả đúng dữ liệu | |
| UAT-18 | Backup/restore rehearsal | Dump PostgreSQL + filestore khôi phục được trên DB test độc lập | |
| UAT-19 | Reverse proxy/TLS | HTTP redirect HTTPS; websocket `/websocket` tới port 8072; không lộ DB manager | |
| UAT-20 | Email outgoing | SMTP gửi invitation, activity notification và quotation; catchall hoạt động | |

## Tiêu chí ký duyệt

- UAT-01 đến UAT-17 và UAT-19/UAT-20 phải **Pass** trước go-live.
- UAT-18 phải có ít nhất một lần restore thành công và người phụ trách backup
  được chỉ định.
- Mọi Fail phải có issue ID, người xử lý và retest date; không nghiệm thu bằng
  cách bỏ qua lỗi dữ liệu hoặc phân quyền.
