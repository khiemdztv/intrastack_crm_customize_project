# BRD/feedback traceability

| Yêu cầu | Đáp ứng trong sản phẩm | Kiểm thử/UAT |
|---|---|---|
| Customer database, xem contact, import Excel/CSV | Odoo Contacts + External ID templates + import guide | test import, UAT-01 |
| CRM tích hợp khi khởi tạo service contract | Opportunity có contract dates, quotation mapping, confirmed SO và delivery project traceability | `test_crm_delivery.py`, UAT-06–09 |
| Employee account activation và portal/user access | HR employee wizard tạo internal user, role bundles CRM/Sales/Project/Timesheet, invitation qua auth_signup | `test_employee_access.py`, UAT-14–15 |
| Staffing: source → interview → contract/placement | Requirement, submission, interview, placement, resume, rate/margin, order/project links | `test_staffing.py`, UAT-03, UAT-10–13 |
| Cloud transformation: engagement → assessment → proposal → PM | Consulting pipeline, SOW template, contract dates, project template/task cloning | `test_crm_delivery.py`, UAT-07–09 |
| 4 pipeline/service types | P1 Staffing, P2 Consulting, P3 Subcontracting, P4 Managed Services; server-side team/stage routing | `test_crm_lead.py`, UAT-02–04 |
| Automation and management visibility | Activities guarded by classification, CEO saved filters/dashboard | UAT-16–17 |
| Go-live readiness | Docker Compose, no-demo install/upgrade, backups, healthcheck, TLS/websocket checklist | UAT-18–20 |

## Known operational boundary

Community edition không có unattended subscription billing. Nếu BRD yêu cầu tự
động lập hóa đơn định kỳ cho Managed Services, cần quy trình vận hành định kỳ
hoặc module OCA subscription trước khi gọi là fully automated.
