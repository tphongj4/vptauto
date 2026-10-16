# VPT Auto Manager

Ứng dụng desktop tiếng Việt quản lý nhiều link Vua Pháp Thuật. Bản 0.4.1 sửa thao tác đăng nhập nền: khởi tạo Flash bình thường, đồng bộ tọa độ theo DPI của Flash, gửi bấm qua hàng đợi thông điệp và xác nhận game đổi màn. Hỗ trợ **đăng nhập nền nhiều tài khoản đồng thời**, không di chuyển con trỏ hoặc gửi phím. Quy trình: **Bắt buộc → kênh ngẫu nhiên 1–8 → nhân vật đã lưu → Vào game**. Có thể chỉnh sửa trực tiếp link/cài đặt rồi bấm **Sửa** để lưu; chưa thực thi nhiệm vụ trong game.

## Các chức năng đã có

- Tạo và lưu nhiều mục link, mỗi mục có tên riêng; sửa, xóa, tìm theo tên và sao chép link.
- Chọn tệp `flashplayer25sa.exe` đang có trên máy và mở từng link bằng trình phát đó.
- Thêm/xóa loại nhiệm vụ, kèm ghi chú; đánh dấu nhiều nhiệm vụ riêng cho từng link.
- Khi chọn link, hiển thị tên, URL, cài đặt auto và bốn nút **Đăng nhập / Sửa / Xóa / Chạy auto**.
- Chọn vị trí nhân vật riêng cho từng link: **1 = trái, 2 = giữa, 3 = phải**. Link cũ mặc định nhân vật 1.
- Bấm **Sửa** để lưu đồng thời tên, URL, vị trí nhân vật và lựa chọn nhiệm vụ của link đang chọn.
- Giữ các thay đổi chưa lưu riêng cho từng link khi chuyển lựa chọn hoặc tìm kiếm; có nút **Hoàn tác** và nhắc trước khi đóng ứng dụng nếu chưa lưu.
- Cả **Đăng nhập** và **Chạy auto** đều khởi động Flash Player với URL đã lưu của link đang chọn, kể cả khi chưa chọn nhiệm vụ. Cần chọn tệp Flash Player một lần trong Cài đặt.
- Nhân vật 1 là lựa chọn mặc định của game: bấm thẳng **Vào game**, không bấm lại thẻ nhân vật. Nhân vật 2/3 được chọn trước khi vào game.
- Sau khi mở Flash, nhận diện các nút trên cửa sổ vừa khởi chạy để tự đăng nhập, hiển thị trạng thái riêng từng link. Mỗi link có tiến trình xử lý riêng, chạy đồng thời; **F8** hoặc **Dừng đăng nhập** hủy tất cả các lượt tự đăng nhập.
- **Chạy auto** dùng cấu hình đã lưu để đăng nhập; phần thực thi nhiệm vụ sẽ bổ sung sau. Nếu mở Flash hoặc nhận diện màn hình thất bại, ứng dụng báo lỗi và dừng thao tác.
- Dữ liệu được ghi nguyên tử; nếu ghi thất bại, giữ cấu hình cũ và báo lỗi.
- Chỉ cho phép một phiên ứng dụng sử dụng cùng thư mục dữ liệu.

**“Tạo link” tạo mục lưu từ URL bạn nhập.** Ứng dụng chưa có công thức tự sinh link đăng nhập. Các loại nhiệm vụ do người dùng đặt tên, chưa có bộ thực thi auto. Mở được trình phát cũng chưa xác nhận đăng nhập hoặc tải game thành công.

## Dùng trên Windows

Yêu cầu: Windows 10/11 x64. Flash Player 32-bit bạn cung cấp có thể được chọn trên Windows x64. Không cần cài Python khi dùng bộ cài.

### Chạy thử không cần cài đặt

Tải qua GitHub: mở [Actions của kho vptauto](https://github.com/tphongj4/vptauto/actions), chọn lần chạy **Windows checks and installer** của phiên bản này có trạng thái **Success**. Trong **Artifacts** chọn **VPTAuto-Portable-0.4.1** để tải ZIP. Đăng nhập GitHub để tải artifact. Giải nén toàn bộ rồi mở `ChayThu.bat` hoặc `VPTAuto.exe` trong thư mục đã giải nén.

Nếu nhận tệp đóng gói `VPTAuto-Portable-0.4.1.zip` trực tiếp, giải nén **toàn bộ** rồi mở `VPTAuto-0.4.1/VPTAuto.exe`. Gói đã kèm Python và Qt; không cần cài riêng các thành phần này. Giữ nguyên hai thư mục `app` và `runtime` cạnh tệp `.exe`, không chạy từ bên trong ZIP.

Để thử với cấu hình riêng, mở **ChayThu.bat** trong thư mục đã giải nén. Cách này lưu các link/cài đặt thử tại `DuLieuThu` cạnh chương trình. Chạy `VPTAuto.exe` trực tiếp dùng cấu hình mặc định ở LocalAppData, chung với bản cài đặt. Cả hai cách đều cần chọn Flash Player trong Cài đặt trước khi mở game.

Bản portable không tạo shortcut hay mục gỡ cài đặt. Có thể đóng ứng dụng rồi xóa thư mục đã giải nén để ngừng dùng. Workflow kiểm tra mở bản portable và cài/mở/gỡ bộ cài trên Windows; xem kết quả của đúng lần chạy.

### Dùng bộ cài

1. Chạy `VPTAuto-Setup-0.4.1.exe`, cài đặt cho tài khoản Windows hiện tại. Bản này dùng được dữ liệu cấu hình cũ, mặc định nhân vật 1 nếu chưa có lựa chọn.
2. Mở **VPT Auto Manager** từ Desktop hoặc Start Menu.
3. Vào **Cài đặt → Chọn tệp .exe**, chọn tệp Flash Player của bạn.
4. Vào **Liên kết game → Tạo link**, nhập tên, dán link mở game và chọn nhân vật, rồi bấm **Tạo & lưu link**.
5. Bấm một link để hiển thị cấu hình đã lưu. Có thể sửa trực tiếp tên, URL, vị trí nhân vật và đánh dấu nhiệm vụ trong **Cài đặt auto**, sau đó bấm **Sửa** để lưu tất cả cùng lúc. Các chỉnh sửa chưa bấm Sửa chưa được ghi ra đĩa. **Hoàn tác** khôi phục toàn bộ phần đang chỉnh về bản đã lưu.
6. Bấm **Đăng nhập** để mở link đã lưu bằng Flash Player và chạy quy trình tự đăng nhập bên dưới. Khả năng mở nhiều cửa sổ phụ thuộc trình phát và game. Ứng dụng không tự nhập tài khoản hoặc mật khẩu.
7. Vào **Loại nhiệm vụ → Thêm loại nhiệm vụ** để tạo chức năng dự kiến. Quay lại từng link, chọn nhiệm vụ và bấm **Sửa**. Xóa loại nhiệm vụ ở trang danh mục sẽ xóa lựa chọn đó khỏi tất cả link sau khi xác nhận.
8. **Chạy auto** khởi động Flash Player rồi tự đăng nhập với link và nhân vật đã lưu, kể cả khi chưa lưu nhiệm vụ nào. Sau khi bấm Vào game, trạng thái nhắc rằng bộ thực thi nhiệm vụ chưa tích hợp. Các thay đổi đang chỉnh chưa bấm Sửa không được áp dụng.

### Quy trình tự đăng nhập

Ứng dụng chờ bố cục ổn định rồi bấm **Bắt buộc**, chọn ngẫu nhiên một trong **8 hàng kênh từ trên xuống** (gồm cả bang hội và đấu giá như ảnh mẫu), chọn nhân vật theo vị trí đã lưu, rồi bấm **Vào game**. **Nhân vật 1 đã được game chọn sẵn nên bỏ bước bấm thẻ**, kể cả khi màu thẻ đang chọn thay đổi hoặc một số thẻ khác không hiển thị. Kênh được chọn một lần cho mỗi lượt đăng nhập.

Các điểm bấm được tính từ ảnh hiện tại trong vùng nội dung Flash, có xét thay đổi kích thước/viền đen. Nhận diện nút chuyển sắc dùng chiều rộng/khoảng cách, tránh nhầm chiều cao dải màu sáng với toàn bộ nút. Chỉ thao tác trên cửa sổ thuộc tiến trình Flash vừa mở. Ảnh lấy bằng Windows `PrintWindow`; ảnh, kích thước và tọa độ đều dùng chế độ DPI của chính cửa sổ Flash, kể cả Flash cũ không khai báo DPI. Thao tác được xếp hàng bằng `PostMessageW` tới đúng cửa sổ hoặc cửa sổ con cùng tiến trình, có khoảng nghỉ cho di chuyển/nhấn/nhả nút; `SendMessageTimeoutW` chỉ kiểm tra cửa sổ có phản hồi. Không dùng `SendInput`, không đặt vị trí con trỏ, không giữ chuột/bàn phím. Flash được mở bình thường để khởi tạo trạng thái cửa sổ; trình phát có thể hiện lên lúc mới mở. Phần bấm tự động không gọi API đưa Flash lên trước; bạn có thể chuyển sang ứng dụng khác sau khi mở game.

Sau khi gửi bấm **Bắt buộc**, ứng dụng xác nhận đã thấy màn kênh/nhân vật. Nếu game vẫn ở màn cũ, chỉ thử lại khi nhận diện được đúng nút, tối đa 3 lần cách nhau ít nhất 2 giây. Tương tự cho chọn kênh và **Vào game**. Một lệnh gửi thành công chưa được coi là game đã nhận thao tác. Nhân vật 2/3 chỉ bấm chọn thẻ một lần; nhân vật 1 bỏ bước này.

Bấm **Chạy auto** cho từng link để chạy nhiều tài khoản cùng lúc. Có thể để các cửa sổ Flash chồng lên nhau hoặc sau ứng dụng khác và tiếp tục làm việc. **Không thu nhỏ Flash xuống thanh tác vụ**: Flash có thể ngừng vẽ/cập nhật khi bị thu nhỏ, nên ứng dụng tạm dừng link đó. Chạy nền cần trình phát hỗ trợ ảnh cửa sổ và thông điệp chuột; nếu nhận ảnh đen hoặc game bỏ qua thao tác nền, link đó sẽ dừng vì không nhận diện được bước tiếp theo. Cần thử với bản Flash/game thực tế của bạn.

Mỗi link có tiến trình phụ độc lập. Một cửa sổ không phản hồi sẽ bị dừng riêng sau 12 giây không có phản hồi từ bộ xử lý, không chặn giao diện hoặc các tài khoản khác. **F8** hoặc nút **Dừng đăng nhập** hủy các bộ xử lý, giữ nguyên cửa sổ game. Đóng ứng dụng cũng dừng tự thao tác; tiến trình phụ tự thoát nếu ứng dụng quản lý bị đóng đột ngột.

Nếu không tìm thấy cửa sổ sau 25 giây, chờ một bước quá 45 giây hoặc toàn bộ quy trình quá 180 giây, ứng dụng dừng và báo trạng thái. Nếu Flash dùng lại cửa sổ cũ thuộc tiến trình khác, hãy đóng cửa sổ đó rồi chạy lại. Không nhận diện được bố cục sẽ không tạo thao tác bấm.

Nhận diện dựa trên màu và vị trí tương đối của các nút trong ba màn hình mẫu đã cung cấp. Bộ kiểm tra Windows gồm ba cửa sổ Qt mô phỏng và ba Flash Projector 32 thật mở phim SWF kiểm tra cục bộ, ở các tiến trình riêng, bị cửa sổ soạn thảo che phía trên. Kiểm tra giữ nguyên con trỏ, cửa sổ nhập liệu, chọn đúng nhân vật 1/2/3 và đã rời màn nhân vật. Các kiểm tra chạy cả bằng runtime portable. Trình Flash dùng kiểm thử được khóa checksum, không nằm trong gói tải. **Chưa kiểm thử đăng nhập vào máy chủ Vua Pháp Thuật bằng Flash 25 của bạn**; các điều khiển riêng của game có thể cần điều chỉnh. Trạng thái **Đã bấm Vào game** xác nhận đã gửi thao tác và rời màn nhân vật, chưa xác nhận nhân vật đã tải vào thế giới game.

### Khi game không chuyển màn

Không cần cấp quyền chuột/bàn phím riêng. Nên mở cả VPT Auto và Flash bình thường, cùng mức quyền Windows. Nếu Flash được mở bằng **Run as administrator**, Windows có thể chặn chương trình ở mức quyền thấp hơn gửi thông điệp cho nó.

Nếu thao tác bị bỏ qua 3 lần hoặc không nhận diện được màn hình, ứng dụng báo lỗi thay vì chỉ hiện đang chờ. Khi đã có ảnh chụp, nút **Ảnh lỗi** xuất hiện cạnh trạng thái link: chữ thập đỏ chỉ điểm đã bấm trên đúng ảnh cửa sổ Flash. Ảnh PNG và thông tin bước/điểm bấm JSON được lưu cục bộ trong `ChanDoan` cạnh `settings.json`; không có URL trong báo cáo JSON, không tự gửi ảnh/báo cáo lên mạng. Ảnh có thể chứa thông tin nhân vật trong game. Lượt chạy mới xóa ảnh lỗi cũ của link đó. Có thể xóa thư mục `ChanDoan` sau khi đóng ứng dụng.

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

- `VPTAuto-Setup-0.4.1.exe`: bộ cài kèm môi trường chạy, shortcut và trình gỡ cài đặt.
- `VPTAuto-Setup-0.4.1.exe.sha256`: checksum của bộ cài.
- `VPTAuto-Portable-0.4.1.zip`: bản giải nén chạy ngay, kèm hướng dẫn và chế độ dữ liệu thử riêng.
- `VPTAuto-Portable-0.4.1.zip.sha256`: checksum của bản portable.
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
- `login_flow.py`, `login_session.py`: trình tự đăng nhập và trạng thái riêng cho một tài khoản.
- `login_controller.py`, `login_worker.py`: chạy/giám sát các bộ xử lý đồng thời, dừng và thời gian chờ.
- `login_diagnostics.py`: tạo ảnh lỗi cục bộ có đánh dấu điểm bấm.
- `windows_desktop.py`: tìm đúng cửa sổ theo tiến trình, chụp nền và gửi thông điệp chuột vào đúng cửa sổ.
- `tests/`: kiểm tra lưu/khôi phục, lựa chọn nhân vật, lỗi ghi dữ liệu, thao tác giao diện và quy trình đăng nhập mô phỏng.
- `scripts/smoke_login_windows.py`: kiểm tra ba tài khoản nền bị che, nhân vật 1/2/3 và giữ nguyên chuột/cửa sổ làm việc trên Windows.
- `scripts/smoke_flash_windows.py`: kiểm tra cùng quy trình trên ba Flash Projector thật với phim SWF do dự án cung cấp; có tùy chọn `--player` để kiểm tra một bản Flash sẵn có.
- `scripts/flash_fixture/`: mã Haxe/phim SWF kiểm thử, không chứa game hoặc link tài khoản.

Bộ thực thi nhiệm vụ cần bổ sung sau khi có quy trình game và ảnh/trạng thái cần nhận diện. Không coi tên nhiệm vụ trong cấu hình là mã lệnh; phần thực thi sau này phải ánh xạ ID đến bộ xử lý do ứng dụng cung cấp.
