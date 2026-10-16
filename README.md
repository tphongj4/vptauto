# VPT Auto Manager

Ứng dụng desktop tiếng Việt quản lý nhiều link Vua Pháp Thuật. Bản 0.3.0 mở Flash Player và tự thao tác **Bắt buộc → kênh ngẫu nhiên 1–8 → nhân vật đã lưu → Vào game** khi bấm **Đăng nhập** hoặc **Chạy auto**. Có thể chỉnh sửa trực tiếp link/cài đặt rồi bấm **Sửa** để lưu; chưa thực thi nhiệm vụ trong game.

## Các chức năng đã có

- Tạo và lưu nhiều mục link, mỗi mục có tên riêng; sửa, xóa, tìm theo tên và sao chép link.
- Chọn tệp `flashplayer25sa.exe` đang có trên máy và mở từng link bằng trình phát đó.
- Thêm/xóa loại nhiệm vụ, kèm ghi chú; đánh dấu nhiều nhiệm vụ riêng cho từng link.
- Khi chọn link, hiển thị tên, URL, cài đặt auto và bốn nút **Đăng nhập / Sửa / Xóa / Chạy auto**.
- Chọn vị trí nhân vật riêng cho từng link: **1 = trái, 2 = giữa, 3 = phải**. Link cũ mặc định nhân vật 1.
- Bấm **Sửa** để lưu đồng thời tên, URL, vị trí nhân vật và lựa chọn nhiệm vụ của link đang chọn.
- Giữ các thay đổi chưa lưu riêng cho từng link khi chuyển lựa chọn hoặc tìm kiếm; có nút **Hoàn tác** và nhắc trước khi đóng ứng dụng nếu chưa lưu.
- Cả **Đăng nhập** và **Chạy auto** đều khởi động Flash Player với URL đã lưu của link đang chọn, kể cả khi chưa chọn nhiệm vụ. Cần chọn tệp Flash Player một lần trong Cài đặt.
- Sau khi mở Flash, nhận diện các nút trên cửa sổ vừa khởi chạy để tự đăng nhập, hiển thị trạng thái riêng từng link. Các yêu cầu được xử lý lần lượt; **F8** hoặc **Dừng đăng nhập** hủy các yêu cầu đang chờ và đang chạy.
- **Chạy auto** dùng cấu hình đã lưu để đăng nhập; phần thực thi nhiệm vụ sẽ bổ sung sau. Nếu mở Flash hoặc nhận diện màn hình thất bại, ứng dụng báo lỗi và dừng thao tác.
- Dữ liệu được ghi nguyên tử; nếu ghi thất bại, giữ cấu hình cũ và báo lỗi.
- Chỉ cho phép một phiên ứng dụng sử dụng cùng thư mục dữ liệu.

**“Tạo link” tạo mục lưu từ URL bạn nhập.** Ứng dụng chưa có công thức tự sinh link đăng nhập. Các loại nhiệm vụ do người dùng đặt tên, chưa có bộ thực thi auto. Mở được trình phát cũng chưa xác nhận đăng nhập hoặc tải game thành công.

## Dùng trên Windows

Yêu cầu: Windows 10/11 x64. Flash Player 32-bit bạn cung cấp có thể được chọn trên Windows x64. Không cần cài Python khi dùng bộ cài.

### Chạy thử không cần cài đặt

Tải qua GitHub: mở [Actions của kho vptauto](https://github.com/tphongj4/vptauto/actions), chọn lần chạy **Windows checks and installer** của phiên bản này có trạng thái **Success**. Trong **Artifacts** chọn **VPTAuto-Portable-0.3.0** để tải ZIP. Đăng nhập GitHub để tải artifact. Giải nén toàn bộ rồi mở `ChayThu.bat` hoặc `VPTAuto.exe` trong thư mục đã giải nén.

Nếu nhận tệp đóng gói `VPTAuto-Portable-0.3.0.zip` trực tiếp, giải nén **toàn bộ** rồi mở `VPTAuto-0.3.0/VPTAuto.exe`. Gói đã kèm Python và Qt; không cần cài riêng các thành phần này. Giữ nguyên hai thư mục `app` và `runtime` cạnh tệp `.exe`, không chạy từ bên trong ZIP.

Để thử với cấu hình riêng, mở **ChayThu.bat** trong thư mục đã giải nén. Cách này lưu các link/cài đặt thử tại `DuLieuThu` cạnh chương trình. Chạy `VPTAuto.exe` trực tiếp dùng cấu hình mặc định ở LocalAppData, chung với bản cài đặt. Cả hai cách đều cần chọn Flash Player trong Cài đặt trước khi mở game.

Bản portable không tạo shortcut hay mục gỡ cài đặt. Có thể đóng ứng dụng rồi xóa thư mục đã giải nén để ngừng dùng. Workflow kiểm tra mở bản portable và cài/mở/gỡ bộ cài trên Windows; xem kết quả của đúng lần chạy.

### Dùng bộ cài

1. Chạy `VPTAuto-Setup-0.3.0.exe`, cài đặt cho tài khoản Windows hiện tại. Bản này dùng được dữ liệu cấu hình cũ, mặc định nhân vật 1 nếu chưa có lựa chọn.
2. Mở **VPT Auto Manager** từ Desktop hoặc Start Menu.
3. Vào **Cài đặt → Chọn tệp .exe**, chọn tệp Flash Player của bạn.
4. Vào **Liên kết game → Tạo link**, nhập tên, dán link mở game và chọn nhân vật, rồi bấm **Tạo & lưu link**.
5. Bấm một link để hiển thị cấu hình đã lưu. Có thể sửa trực tiếp tên, URL, vị trí nhân vật và đánh dấu nhiệm vụ trong **Cài đặt auto**, sau đó bấm **Sửa** để lưu tất cả cùng lúc. Các chỉnh sửa chưa bấm Sửa chưa được ghi ra đĩa. **Hoàn tác** khôi phục toàn bộ phần đang chỉnh về bản đã lưu.
6. Bấm **Đăng nhập** để mở link đã lưu bằng Flash Player và chạy quy trình tự đăng nhập bên dưới. Khả năng mở nhiều cửa sổ phụ thuộc trình phát và game. Ứng dụng không tự nhập tài khoản hoặc mật khẩu.
7. Vào **Loại nhiệm vụ → Thêm loại nhiệm vụ** để tạo chức năng dự kiến. Quay lại từng link, chọn nhiệm vụ và bấm **Sửa**. Xóa loại nhiệm vụ ở trang danh mục sẽ xóa lựa chọn đó khỏi tất cả link sau khi xác nhận.
8. **Chạy auto** khởi động Flash Player rồi tự đăng nhập với link và nhân vật đã lưu, kể cả khi chưa lưu nhiệm vụ nào. Sau khi bấm Vào game, trạng thái nhắc rằng bộ thực thi nhiệm vụ chưa tích hợp. Các thay đổi đang chỉnh chưa bấm Sửa không được áp dụng.

### Quy trình tự đăng nhập

Giữ cửa sổ Flash ở phía trước, không che các nút. Ứng dụng chờ bố cục ổn định rồi bấm **Bắt buộc**, chọn ngẫu nhiên một trong **8 hàng kênh từ trên xuống** (gồm cả bang hội và đấu giá như ảnh mẫu), chọn nhân vật theo vị trí đã lưu, rồi bấm **Vào game**. Kênh được chọn một lần cho mỗi lượt đăng nhập.

Các điểm bấm được tính từ ảnh hiện tại trong vùng nội dung Flash, có xét thay đổi kích thước/viền đen. Chỉ thao tác trên cửa sổ thuộc tiến trình Flash vừa mở. Chuyển sang cửa sổ khác làm tạm dừng; đưa Flash lên trước để tiếp tục. **F8** hoặc nút **Dừng đăng nhập** hủy toàn bộ hàng chờ, giữ nguyên cửa sổ game. Đóng ứng dụng cũng dừng tự thao tác.

Nếu không tìm thấy cửa sổ sau 25 giây, chờ một bước quá 45 giây hoặc toàn bộ quy trình quá 180 giây, ứng dụng dừng và báo trạng thái. Nếu Flash dùng lại cửa sổ cũ thuộc tiến trình khác, hãy đóng cửa sổ đó rồi chạy lại. Không nhận diện được bố cục sẽ không tạo thao tác bấm.

Nhận diện dựa trên màu và vị trí tương đối của các nút trong ba màn hình mẫu đã cung cấp. Bộ kiểm tra bao gồm bố cục mô phỏng ở nhiều kích thước và chụp ảnh/gửi chuột thật trên Windows với cửa sổ mô phỏng. **Chưa kiểm thử đăng nhập trên game thật**; giao diện hoặc thời gian tải khác có thể cần điều chỉnh. Trạng thái **Đã bấm Vào game** xác nhận đã gửi thao tác, chưa xác nhận nhân vật đã tải vào thế giới game.

Flash Player và game không nằm trong bộ cài. Không cần nhập mật khẩu game vào ứng dụng này. Link được lưu trong tệp cấu hình cục bộ, kể cả tham số phiên nếu link có chứa chúng; link hết hạn cần được thay bằng link mới.

Cấu hình nằm tại `%LOCALAPPDATA%\VPTAuto\settings.json`. Cập nhật hoặc gỡ cài đặt giữ lại tệp này. Đóng ứng dụng trước khi nâng cấp hoặc gỡ cài đặt. Để chuyển cấu hình, đóng ứng dụng trên cả hai máy rồi sao chép tệp này sang đúng vị trí ở máy mới; chọn lại Flash Player nếu đường dẫn khác.

## Chạy từ mã nguồn

Python 3.11 trở lên (khuyến nghị 3.12), Qt for Python 6.8.3.

Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe main.py
```

Linux trong môi trường đám mây:

```bash
cd /workspace/vptauto
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pytest -q
QT_QPA_PLATFORM=offscreen XDG_CACHE_HOME=/tmp/vptauto-cache .venv/bin/python main.py --smoke-test --data-dir /tmp/vptauto-smoke
```

Chạy giao diện trên máy có màn hình bằng `python main.py`. `--data-dir <thư mục>` cho phép dùng dữ liệu thử riêng. Linux kiểm thử được giao diện/lưu dữ liệu; thao tác khởi chạy Flash Player chỉ hoạt động trên Windows.

## Tạo bộ cài Windows từ Linux hoặc Windows

Trình đóng gói dùng NSIS và **runtime Windows Python chính thức**, kèm wheel Qt Windows x64. Không chuyển tệp thực thi Linux thành `.exe`. Mọi gói tải xuống đều dùng TLS và được kiểm tra checksum. Phụ thuộc Windows được khóa phiên bản/hash tại `packaging/windows-requirements.lock`.

Trên Debian Linux có `sqv`, `dpkg-deb` và bộ khóa Debian:

```bash
.venv/bin/python scripts/prepare_nsis.py
.venv/bin/python scripts/build_windows.py
```

`prepare_nsis.py` xác minh chữ ký Debian, checksum danh mục và gói trước khi giải nén NSIS vào `build/nsis`. Không cần quyền root. Có thể dùng `makensis` đã cài trên hệ thống thay thế.

Trên Windows, cài NSIS 3 rồi chạy:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts\build_windows.py --makensis 'C:\Program Files (x86)\NSIS\makensis.exe'
```

Kết quả trong `artifacts/`:

- `VPTAuto-Setup-0.3.0.exe`: bộ cài kèm môi trường chạy, shortcut và trình gỡ cài đặt.
- `VPTAuto-Setup-0.3.0.exe.sha256`: checksum của bộ cài.
- `VPTAuto-Portable-0.3.0.zip`: bản giải nén chạy ngay, kèm hướng dẫn và chế độ dữ liệu thử riêng.
- `VPTAuto-Portable-0.3.0.zip.sha256`: checksum của bản portable.
- `build-manifest.json`: thông tin thành phần và giới hạn kiểm chứng của bản đóng gói.

Khi đã có bundle Windows hợp lệ tại `build/windows-stage`, chỉ cần chạy `.venv/bin/python scripts/package_portable.py` để tạo lại ZIP, không phải nén lại bộ cài. Lệnh kiểm tra mã nguồn bundle khớp mã hiện tại và CRC của các tệp ZIP trước khi xuất checksum.

Đóng gói thành công trên Linux chưa chứng minh bộ cài đã chạy trên Windows. Workflow `.github/workflows/windows.yml` cung cấp kiểm thử trên Windows khi mã nguồn được đưa lên GitHub; không tự động được chạy bởi việc tạo các tệp này. Trước khi phát hành cần kiểm tra cài đặt/mở/gỡ cài đặt trên Windows và mở game thật bằng link hợp lệ. Bộ cài hiện chưa được ký mã số.

## Cấu trúc để bổ sung chức năng

- `src/vptauto/ui.py`: cửa sổ quản lý link, hộp thoại và danh sách chọn nhiệm vụ.
- `models.py`: cấu trúc link và loại nhiệm vụ. Mỗi link lưu `task_ids` và `character_slot` riêng.
- `service.py`: lưu đồng thời link/cài đặt trong một lần ghi; chỉ cập nhật trạng thái sau khi ghi đĩa thành công. `AutoPlan` là ảnh chụp bất biến của cấu hình đã lưu để kết nối bộ thực thi sau này.
- `storage.py`: lưu JSON vào hồ sơ người dùng, không ghi dữ liệu cá nhân vào kho mã nguồn.
- `launcher.py`: gọi Flash bằng danh sách đối số, không ghép lệnh qua shell.
- `login_vision.py`: nhận diện ba bố cục từ ảnh vùng nội dung Flash.
- `login_flow.py`, `login_controller.py`: trình tự đăng nhập, chọn kênh, hàng chờ, dừng và thời gian chờ.
- `windows_desktop.py`: tìm đúng cửa sổ theo tiến trình, chụp ảnh và gửi chuột có kiểm tra cửa sổ đang ở phía trước.
- `tests/`: kiểm tra lưu/khôi phục, lựa chọn nhân vật, lỗi ghi dữ liệu, thao tác giao diện và quy trình đăng nhập mô phỏng.
- `scripts/smoke_login_windows.py`: kiểm tra chụp ảnh và gửi chuột Windows trên cửa sổ game mô phỏng độc lập.

Bộ thực thi nhiệm vụ cần bổ sung sau khi có quy trình game và ảnh/trạng thái cần nhận diện. Không coi tên nhiệm vụ trong cấu hình là mã lệnh; phần thực thi sau này phải ánh xạ ID đến bộ xử lý do ứng dụng cung cấp.
