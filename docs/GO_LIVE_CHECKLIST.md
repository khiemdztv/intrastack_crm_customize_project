# Go-live checklist

## Trước khi copy lên Ubuntu

- [ ] Ubuntu đã cập nhật bản vá; Docker Engine/Compose plugin tương thích.
- [ ] DNS trỏ về server; firewall chỉ mở 80/443 (không mở trực tiếp 8069/8072).
- [ ] Đã tạo `deploy/.env` từ `.env.example`, thay toàn bộ secret, `chmod 600`.
- [ ] Đã quyết định database name, timezone công ty, currency và multi-company.
- [ ] Đã cấu hình SMTP thật, catchall domain và email alias.
- [ ] Đã chuẩn bị TLS (Nginx/Traefik), route `/websocket` tới gevent port 8072.
- [ ] Đã test dung lượng đĩa, inode, RAM; đặt lịch backup off-host.

## Cài đặt lần đầu

```bash
cd /opt/intrastack-crm/deploy
cp .env.example .env
chmod 600 .env
nano .env
docker compose pull
./deploy.sh
docker compose ps
```

`deploy.sh` tạo database nếu mới, backup database + filestore nếu đã tồn tại,
cài/nâng cấp module và luôn chạy `--without-demo=all`. Không chạy script đồng
thời với người dùng đang thao tác; hãy dùng maintenance window.

## Sau khi Odoo healthy

- [ ] Đăng nhập bằng master/admin; đổi password admin mặc định.
- [ ] Cài module `intrastack_crm` ở Apps nếu đây là database trống.
- [ ] Tạo công ty, Sales Manager, Sales Executive, Recruiter, PM và Consultant;
  gửi invitation rồi kiểm tra đăng nhập từng role.
- [ ] Import customer/contact bằng CSV; kiểm tra External ID và duplicate policy.
- [ ] Chạy UAT-02, UAT-06, UAT-08 và UAT-10 đến UAT-15 với dữ liệu thật đã ẩn danh.
- [ ] Xác nhận quotation template, project task template, activities và dashboard.
- [ ] Kiểm tra SMTP invitation/quotation, timezone và chữ ký email.
- [ ] Kiểm tra TLS, websocket, rate limit/reverse proxy, log rotation và alert.
- [ ] Chụp backup đầu tiên, kiểm tra file mode 600 và xác nhận restore rehearsal.

## Phạm vi Community cần vận hành thủ công

Odoo 17 Community không có subscription billing tự động như Enterprise. Managed
Services vẫn tạo được quotation, contract dates, monthly service line và project;
chu kỳ invoice cần người dùng lập/xác nhận theo lịch hoặc triển khai thêm module
OCA subscription phù hợp trước khi cam kết tự động hóa.

## Rollback

Không xóa volume hay addon directory khi rollback. Dừng Odoo, giữ nguyên dump và
filestore backup của lần deploy, sau đó restore vào database/volume kiểm thử trước
khi thay thế production. Ghi nhận thời điểm, người thực hiện và checksum backup.
