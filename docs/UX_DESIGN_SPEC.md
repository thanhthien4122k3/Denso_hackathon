# Denso D3 — Đặc tả cải tiến giao diện & trải nghiệm (UX/Design Specification)

Bạn là Product Designer, UX Engineer và Full-stack Engineer. Hãy trực tiếp cải tiến project Denso D3 hiện có thành ứng dụng nội bộ rõ ràng, dễ thao tác trên máy tính và Android, hỗ trợ hiệu quả bài toán liên kết dữ liệu sản xuất và phân tích sự cố.

Không chỉ thay màu hoặc làm đẹp dashboard. Phải cải thiện cấu trúc thông tin, luồng thao tác, khả năng giải thích kết quả và trạng thái dữ liệu.

## 1. Đọc project trước khi chỉnh sửa

Đầu tiên:

- Đọc cấu trúc frontend, backend, API, database và YAML.
- Xác định tính năng nào hoạt động thật, tính năng nào mới có giao diện.
- Kiểm tra các luồng đang có trước khi refactor.
- Giữ stack hiện tại nếu đáp ứng được; không tự chuyển sang React hoặc thêm framework lớn.
- Giữ một lệnh khởi động `python run.py`.
- Giữ SQL trong YAML và thông tin kết nối trong `.env`.
- Không xóa dữ liệu, reset database hoặc ghi đè credentials.
- Nếu thay schema, dùng migration có phiên bản.
- Giữ tương thích các API đang được sử dụng; nếu cần thay đổi thì cập nhật đồng bộ và kiểm tra hồi quy.

Ảnh hiện tại chỉ thể hiện trang tổng quan, không chứng minh các màn hình khác có lỗi. Hãy kiểm tra code và giao diện thực tế trước khi kết luận.

## 2. Các vấn đề cần sửa từ giao diện hiện tại

Trang hiện tại có:

- Header đỏ khá lớn.
- Sidebar 10 mục đánh số liên tục.
- Nhiều thẻ thống kê nhỏ ngang hàng.
- Nhãn kỹ thuật như department, line, process, dataset, cạnh đồ thị.
- Số dạng 0/0 không có diễn giải.
- Nội dung bị giới hạn chiều rộng và để trống lớn bên phải.
- Các khối rỗng cao nhưng chỉ hiện "Không có dữ liệu".

Hãy xử lý những vấn đề này bằng cách:

- Ưu tiên thông tin giúp người dùng ra quyết định.
- Gom chức năng theo công việc.
- Việt hóa nhãn.
- Phân biệt số 0, chưa có dữ liệu, đang tải và tải lỗi.
- Tận dụng không gian màn hình hợp lý.
- Mọi empty state phải giải thích và có hành động phù hợp.

## 3. Tổ chức điều hướng

Bỏ số thứ tự 1–10 trong menu. Nhóm lại:

**Tổng quan**
- Trung tâm vận hành.

**Vận hành**
- Ghi nhận dữ liệu.
- Sự cố.
- Công việc theo bộ phận.

**Phân tích**
- Bản đồ liên kết.
- Phân tích tác động.
- Kịch bản mô phỏng.

**Thiết lập dữ liệu**
- Danh mục sản xuất.
- Nguồn dữ liệu và ánh xạ.
- Khảo sát và xác nhận.

Giữ chức năng hiện có nhưng cải thiện tên và vị trí.

Desktop:
- Sidebar có icon và chữ, có thể thu gọn.
- Header gọn: tên trang, bộ lọc phạm vi nếu phù hợp, chế độ dữ liệu và hành động chính.
- Active menu rõ ràng, không chỉ dựa vào màu.

Android:
- Menu drawer.
- Đặt lối vào Tổng quan, Ghi nhận, Sự cố và Công việc dễ tìm.
- Không thu nhỏ nguyên giao diện desktop xuống màn hình điện thoại.

Dùng đường dẫn hoặc trạng thái điều hướng có thể bookmark. Reload không đưa người dùng về trang đầu một cách bất ngờ.

## 4. Hệ thống thiết kế

Phong cách ứng dụng vận hành công nghiệp: sạch, dễ đọc, ít trang trí.

- Nền xám rất nhạt, bề mặt trắng.
- Đỏ là màu thương hiệu và hành động chính; không dùng đỏ cho tất cả chỉ số.
- Trạng thái có màu ngữ nghĩa: xanh thành công, cam cần chú ý, đỏ nghiêm trọng, xám chưa xác định.
- Luôn đi kèm chữ/icon, không truyền đạt bằng màu đơn thuần.
- Font hệ thống hoặc font đóng gói local, hỗ trợ tiếng Việt.
- Body text khoảng 14–16px, line-height dễ đọc.
- Hệ khoảng cách nhất quán: 4, 8, 12, 16, 24, 32px.
- Border nhẹ, bo góc vừa phải, hạn chế shadow.
- Dùng icon SVG nhất quán, không dùng emoji làm icon điều hướng.
- Nút cảm ứng khoảng 44px trở lên.
- Có focus rõ, label đầy đủ, thao tác bàn phím và thông báo lỗi dễ tiếp cận.
- Bảng dữ liệu rộng được cuộn trong vùng riêng; không gây cuộn ngang toàn trang.

Tạo design tokens cho màu, khoảng cách, font, radius và trạng thái. Tái sử dụng component thay vì mỗi trang một kiểu.

Không phụ thuộc CDN hoặc Internet.

## 5. Thiết kế lại trang tổng quan

Trang này phải trả lời nhanh:

1. Có vấn đề gì đang cần xử lý?
2. Phạm vi nào bị ảnh hưởng?
3. Bộ phận nào cần hành động?
4. Dữ liệu có đủ và còn cập nhật không?

### Hàng đầu: phạm vi và hành động

- Bộ lọc thời gian, chuyền và ca khi dữ liệu hỗ trợ.
- Hiển thị rõ bộ lọc áp dụng cho những khối nào.
- Chế độ dữ liệu "Vận hành" hoặc "Mô phỏng".
- Thời điểm cập nhật gần nhất.
- Nút "Ghi nhận dữ liệu".
- Nút "Báo cáo sự cố".

Không dùng tên "Dữ liệu thực" cho dữ liệu chưa được xác minh nguồn.

### Chỉ số chính

Chỉ hiển thị khoảng 4–5 chỉ số thực sự hữu ích, chẳng hạn:

- Sự cố chưa đóng.
- Công việc cần xử lý.
- Máy đang dừng nếu có dữ liệu trạng thái đủ mới.
- Sản lượng đạt trong phạm vi.
- Tỷ lệ lỗi trong phạm vi.

Mỗi chỉ số có tên rõ, đơn vị, phạm vi và có thể bấm để xem danh sách đã lọc.

Quy tắc:

- Không hiện trend giả.
- Không có kỳ so sánh thì không hiện phần trăm tăng/giảm.
- Không có dữ liệu trạng thái máy thì hiện "Chưa có dữ liệu", không hiện 0 máy dừng.
- Tỷ lệ lỗi tổng hợp = tổng số lỗi / tổng số kiểm tra hoặc tổng sản lượng, tùy chỉ số được định nghĩa rõ; không lấy trung bình đơn giản các tỷ lệ.
- Không trộn tỷ lệ lỗi QC với tỷ lệ lỗi từ báo cáo sản lượng.
- Không cộng sản lượng của nhiều công đoạn thành sản lượng thành phẩm nếu gây đếm lặp.
- Không cộng các đơn vị đo không tương thích.

### Nội dung ưu tiên

- Danh sách sự cố cần chú ý, sắp theo mức nghiêm trọng rồi thời gian.
- Công việc cần xử lý, có bộ lọc bộ phận.
- Chất lượng/độ mới dữ liệu dạng khối nhỏ.
- Các hoạt động gần đây nếu có lịch sử thật.

Số lượng danh mục, dataset, cạnh đồ thị chuyển sang phần "Tình trạng thiết lập", không chiếm vị trí chỉ số vận hành chính.

Không thêm biểu đồ khi chưa có câu hỏi và dữ liệu phù hợp để biểu đồ trả lời.

## 6. Trạng thái lần đầu sử dụng

Khi hệ thống chưa được thiết lập, hiển thị checklist dựa trên dữ liệu thực:

1. Tạo bộ phận và chuyền.
2. Khai báo công đoạn và máy.
3. Thiết lập quan hệ.
4. Ghi nhận dữ liệu đầu tiên.
5. Tạo sự cố hoặc thử kịch bản mô phỏng.

Mỗi bước có:
- Trạng thái hoàn thành.
- Mô tả ngắn.
- Nút mở đúng màn hình.

Có lựa chọn "Khám phá bằng dữ liệu mô phỏng", tách biệt khỏi dữ liệu vận hành. Không tự nạp demo khi vào trang.

Empty state cần phân biệt:
- Chưa có bản ghi.
- Không có kết quả phù hợp bộ lọc.
- Chưa thiết lập nguồn.
- Không tải được dữ liệu.

Lỗi API không được hiển thị thành danh sách rỗng hoặc số 0.

## 7. Cải thiện ghi nhận dữ liệu

Chia theo loại nghiệp vụ:

- Sản lượng.
- Trạng thái máy.
- Dừng máy.
- QC.
- Vật tư.

Form:
- Nhóm trường theo bối cảnh, số liệu và ghi chú.
- Dropdown có tìm kiếm, hiển thị cả mã và tên.
- Chọn chuyền thì lọc công đoạn phù hợp.
- Chọn công đoạn thì lọc máy phù hợp.
- Quan hệ chưa có thì giải thích, không tự chọn ngẫu nhiên.
- Giữ lựa chọn chuyền/ca cho lần nhập tiếp theo khi phù hợp, nhưng luôn hiển thị để người dùng kiểm tra.
- Phân biệt thời gian sự kiện và thời gian ghi nhận.
- Hiển thị đơn vị ngay cạnh ô số.
- Tính tổng/tỷ lệ chỉ khi dữ liệu đầu vào hợp lệ.
- Báo lỗi sát trường, giữ nguyên dữ liệu khi API lỗi.
- Chống double-submit và retry tạo trùng theo cơ chế hiện tại.
- Sau thành công hiển thị ID và nút "Xem bản ghi", "Nhập tiếp".

Trên Android, ưu tiên thao tác một cột và bàn phím số. Thanh hành động cố định không che trường nhập hoặc thông báo lỗi.

Nếu rời trang có thay đổi chưa lưu, cảnh báo phù hợp.

## 8. Quản lý sự cố theo một luồng liền mạch

Danh sách sự cố có:
- Mã, tiêu đề, đối tượng, mức độ, trạng thái.
- Thời gian bắt đầu và thời lượng.
- Bộ phận phụ trách.
- Trạng thái phân tích.
- Tìm kiếm, lọc và phân trang.

Trang chi tiết là nơi xử lý chính, gồm:
- Tóm tắt.
- Quan sát và bằng chứng.
- Phạm vi ảnh hưởng.
- Giả thuyết nguyên nhân.
- Công việc.
- Lịch sử thay đổi.

Luồng:
Tạo sự cố → bổ sung bằng chứng → chạy phân tích → xem đường ảnh hưởng → xác nhận công việc cần tạo → theo dõi → giải quyết.

Không bắt người dùng chuyển qua nhiều trang rồi tự nhập lại incident ID.

Khi mở phân tích từ sự cố, truyền sẵn ngữ cảnh. Khi quay lại, giữ bộ lọc và vị trí danh sách nếu khả thi.

Chỉ cho chuyển trạng thái hợp lệ. Khi đóng sự cố, yêu cầu thông tin kết quả xử lý; không bắt buộc bịa nguyên nhân nếu chưa xác định được.

Không hiện "người xác nhận" như danh tính đã xác thực nếu hệ thống chưa có đăng nhập.

## 9. Bản đồ liên kết phục vụ truy vết

Có ba chế độ:
- Nghiệp vụ.
- Logic hệ thống.
- Hai lớp kết hợp.

Không mở đầu bằng toàn bộ đồ thị dày đặc. Cho người dùng chọn đối tượng và xem lân cận 1–2 bước trước.

Cần:
- Tìm node theo mã/tên.
- Lọc loại node và cạnh.
- Chọn upstream/downstream.
- Chọn độ sâu.
- Zoom, fit view, reset.
- Legend rõ.
- Panel chi tiết node.
- Highlight đường ảnh hưởng.
- Hiển thị mũi tên và ý nghĩa quan hệ.

Phân biệt cạnh phụ thuộc sản xuất, luồng dữ liệu, ánh xạ và trách nhiệm.

Kèm bảng/danh sách quan hệ để đọc trên điện thoại và kiểm tra khi đồ thị phức tạp.

Cạnh ánh xạ dữ liệu không tự động được dùng để lan truyền sự cố vật lý.

Nếu đồ thị bị giới hạn số node vì hiệu năng, thông báo rõ phần đang được hiển thị.

## 10. Màn hình phân tích dễ kiểm chứng

Tách ba phần:

**Đầu vào**
- Sự cố/đối tượng.
- Thời điểm.
- Phạm vi.
- Giả định.
- Quy tắc/phiên bản.

**Kết quả**
- Ảnh hưởng đã quan sát.
- Rủi ro suy ra từ quan hệ.
- Ước tính định lượng khi đủ tham số.
- Giả thuyết nguyên nhân được ưu tiên kiểm tra.

**Giải thích**
- Đường lan truyền.
- Bằng chứng.
- Quy tắc áp dụng.
- Công thức và đơn vị.
- Dữ liệu còn thiếu.

Mỗi kết luận có hành động "Vì sao?" để mở giải thích.

Không trình bày điểm quy tắc thành xác suất.
Không biến tương quan thành nguyên nhân đã xác nhận.
Không hiển thị số ước tính chính xác giả tạo khi thiếu tham số.
Không cộng lặp ảnh hưởng trên cùng lot/lệnh qua nhiều công đoạn.

Lưu snapshot kết quả. Nếu dữ liệu đầu vào hoặc quan hệ đã thay đổi sau lần chạy, hiển thị thời điểm phân tích và gợi ý chạy lại; chỉ kết luận "đã thay đổi" khi hệ thống có bằng chứng phiên bản/thời điểm.

## 11. Công việc theo bộ phận

Mỗi công việc thể hiện:
- Việc cần làm.
- Lý do đề xuất.
- Sự cố liên quan.
- Đối tượng cần kiểm tra.
- Bộ phận phụ trách.
- Mức ưu tiên.
- Trạng thái.
- Hạn xử lý nếu đã được đặt.

Cho phép xác nhận, bắt đầu, hoàn thành hoặc từ chối kèm lý do phù hợp.

Không tự tạo nhiều công việc giống nhau khi phân tích lại. Có cơ chế nhận diện đề xuất đã được chuyển thành công việc.

"Quá hạn" chỉ xuất hiện khi có deadline thật.
Không tự gửi thông báo ra hệ thống ngoài nếu chưa tích hợp.

## 12. Thiết lập dữ liệu thuận tiện

Danh mục:
- Dùng tab hoặc nhóm theo nghiệp vụ.
- Nhãn tiếng Việt, mã kỹ thuật đặt ở chi tiết.
- Tìm kiếm, lọc trạng thái, thêm/sửa nhanh.
- Cho xem đối tượng đang được tham chiếu trước khi ngừng sử dụng.

Nguồn dữ liệu:
- Phân biệt "Đã khai báo", "Đã tích hợp", "Chưa có dữ liệu", "Dữ liệu chậm".
- Đánh giá chậm dựa trên lịch cập nhật được cấu hình.
- Không đánh dấu nguồn theo lot là chậm chỉ vì không có dữ liệu mỗi phút.
- Hiển thị khóa ánh xạ thiếu hoặc chưa xác nhận.
- Không tuyên bố đã kết nối MES/ERP khi chỉ mới khai báo metadata.

Khảo sát:
- Cho xem thông tin đã xác nhận và còn thiếu.
- Liên kết câu trả lời với danh mục/quan hệ liên quan khi có.
- Giữ giả định mô phỏng tách biệt với thông tin nhà máy xác nhận.

## 13. Mô phỏng

Giữ ba kịch bản:
- Máy dừng.
- QC có tỷ lệ lỗi cao.
- Thiếu vật tư.

Luồng màn hình:
Chọn kịch bản → xem dữ liệu và giả định → chỉnh tham số hợp lệ → chạy → đọc ảnh hưởng → xem hành động.

Cho phép so sánh cơ sở và giả định khi engine hỗ trợ, với cùng phạm vi và đơn vị.

Luôn có nhãn "Mô phỏng".
Không sửa dữ liệu vận hành hoặc tạo công việc thật khi chạy what-if.
Không nạp demo trùng.
Không bổ sung ML hoặc gọi kết quả là dự báo AI nếu chỉ dùng quy tắc.

## 14. Trạng thái UI và hiệu năng

Chuẩn hóa:
- Loading.
- Thành công.
- Validation error.
- API/network error.
- Empty state.
- Retry.
- Dữ liệu cũ/chưa cập nhật khi có căn cứ.

Tìm kiếm có debounce và xử lý response đến sai thứ tự.
Danh sách lớn có phân trang server.
Không tải toàn bộ database để lọc bằng JavaScript.
Không gọi lại tất cả API khi chỉ cập nhật một bản ghi.
Tự làm mới, nếu có, không xóa form đang nhập và dừng hoặc giảm tần suất khi tab ẩn.

Nội dung người dùng phải render an toàn.
Không mở CORS wildcard hoặc thay đổi firewall để giải quyết lỗi UI.

## 15. Kiểm tra và nghiệm thu

Kiểm tra các kích thước tối thiểu:
- Mobile 360–390px.
- Tablet khoảng 768px.
- Desktop 1366px và 1920px.

Kiểm thử thực tế:
1. Hệ thống chưa có dữ liệu.
2. Có danh mục nhưng chưa có vận hành.
3. Nhập sản lượng thành công.
4. Nhập sai và API lỗi.
5. Tạo sự cố từ ngữ cảnh đối tượng.
6. Phân tích và mở giải thích.
7. Chuyển đề xuất thành công việc.
8. Chạy lại không tạo trùng.
9. Chuyển giữa mô phỏng và vận hành.
10. Lọc, phân trang và reload.
11. Tên dài, tiếng Việt và dữ liệu nhiều.
12. Chức năng cũ vẫn hoạt động.

Nếu có công cụ trình duyệt, chạy app, chụp ảnh, kiểm tra trực quan và sửa lỗi layout trước khi bàn giao. Nếu không có, nói rõ chưa xác minh trực quan.

Không tuyên bố đã test database hoặc mobile thật khi chưa làm.

## 16. Kết quả cần bàn giao

Thực hiện sửa code hoàn chỉnh, không dừng ở tư vấn.

Sau khi hoàn tất, cung cấp:
- Những vấn đề đã sửa và tác dụng với người dùng.
- Các màn hình/luồng đã cải tiến.
- Thay đổi API hoặc database nếu có.
- Hướng dẫn chạy.
- Kết quả kiểm thử.
- Ảnh màn hình nếu đã chụp.
- Giới hạn còn lại.

Ưu tiên hoàn thiện luồng:
**Ghi nhận → Sự cố → Phân tích → Giải thích → Hành động → Theo dõi.**

Không mở rộng sang tính năng ngoài phạm vi chỉ để ứng dụng trông phức tạp hơn.
