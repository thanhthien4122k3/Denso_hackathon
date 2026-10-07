# Denso D3 — Đặc tả dự án (Project Specification)

Bạn là kỹ sư full-stack và kỹ sư dữ liệu. Hãy mở rộng project **Denso Production Input** hiện có thành ứng dụng **Denso D3 — Liên kết chuỗi sản xuất và phân tích sự cố**.

Ứng dụng phục vụ bài toán:

"Liên kết dữ liệu chuỗi sản xuất qua hai lớp: logic hệ thống và nghiệp vụ sản xuất; phân tích ảnh hưởng lan truyền, đề xuất nguyên nhân có thể xảy ra và gợi ý hành động cho từng bộ phận."

Hãy trực tiếp đọc project, đánh giá những gì đã có và triển khai code hoàn chỉnh. Không chỉ đưa ra kế hoạch hoặc thiết kế giao diện giả.

## 1. Giữ nguyên nền tảng hiện có

- Giữ FastAPI, PostgreSQL, HTML/CSS/JavaScript nếu project đang sử dụng.
- Giữ SQL và thuộc tính query trong YAML.
- Tiếp tục chỉ cần `python run.py` để khởi động.
- Giao diện hoạt động trên Android và máy tính qua trình duyệt nội bộ.
- Frontend gọi API cùng origin bằng URL tương đối.
- Không phụ thuộc Internet hoặc CDN.
- Giữ hoạt động của form nhập sản lượng và các API hiện tại.
- Không xóa hoặc reset dữ liệu đã có.
- Không ghi đè `.env` hoặc để lộ credentials.
- Đọc cấu trúc và quy ước của repository trước khi thay đổi.
- Chưa cần Neo4j, Spark, Kafka hoặc mô hình ML. Dùng PostgreSQL để lưu node/edge và Python để phân tích đồ thị ở quy mô demo.

Mục tiêu là một bản thử nghiệm có thể thao tác xuyên suốt và giải thích kết quả, không tuyên bố là hệ thống dự báo đã được kiểm chứng tại nhà máy.

## 2. Các nhóm chức năng cần có

Tạo menu:

1. Tổng quan.
2. Danh mục sản xuất.
3. Nguồn dữ liệu và liên kết hệ thống.
4. Ghi nhận vận hành.
5. Quản lý sự cố.
6. Bản đồ liên kết.
7. Phân tích tác động và nguyên nhân.
8. Hành động theo bộ phận.
9. Kịch bản mô phỏng.
10. Thông tin khảo sát cần xác nhận.

Mọi nút thao tác phải có chức năng thật hoặc được ghi rõ chưa hỗ trợ. Không tạo nút bấm chỉ để trang trí.

## 3. Danh mục nghiệp vụ sản xuất

Xây dựng danh mục:

- Bộ phận.
- Chuyền sản xuất.
- Công đoạn.
- Máy móc/thiết bị.
- Vật tư/linh kiện.
- Sản phẩm.
- Lệnh sản xuất.
- Lot.
- Ca sản xuất.

Mỗi đối tượng có:

- ID nội bộ.
- Mã nghiệp vụ duy nhất trong phạm vi thích hợp.
- Tên.
- Mô tả.
- Trạng thái hoạt động.
- Thời điểm tạo/cập nhật.
- Cờ dữ liệu mô phỏng nếu có.

Cho phép thêm, xem, sửa và ngừng sử dụng. Đối tượng đang được tham chiếu không được xóa làm mất toàn vẹn dữ liệu.

Thiết lập các quan hệ có ý nghĩa rõ ràng:

- Chuyền có công đoạn.
- Công đoạn trước cung cấp đầu ra cho công đoạn sau.
- Máy phục vụ công đoạn.
- Công đoạn tiêu thụ vật tư.
- Công đoạn tạo ra hoặc xử lý sản phẩm.
- Bộ phận chịu trách nhiệm đối tượng.
- Lệnh sản xuất liên quan đến sản phẩm.
- Lot thuộc lệnh sản xuất.

Không mặc định toàn bộ nhà máy có quy trình tuyến tính. Hỗ trợ phân nhánh, hội tụ và quan hệ có điều kiện.

## 4. Lớp logic hệ thống và nguồn dữ liệu

Quản lý:

- Hệ thống nguồn: MES, ERP, PLC, ứng dụng nhập liệu, Excel, API hoặc nguồn khác.
- Dataset: bảng, file, endpoint hoặc tập dữ liệu.
- Trường dữ liệu trong dataset.
- Luồng xử lý/truyền dữ liệu giữa các dataset.
- Ánh xạ đối tượng nghiệp vụ với dataset và trường định danh tương ứng.

Với mỗi nguồn/dataset, lưu:

- Mã và tên.
- Loại nguồn.
- Nơi phát sinh dữ liệu.
- Phương thức thu thập: cảm biến, PLC, barcode, nhập tay, file, API.
- Bộ phận sở hữu.
- Vị trí lưu trữ dạng metadata, không lưu credentials.
- Các khóa liên kết: machine_code, process_code, lot_code, order_code…
- Trường thời gian sự kiện.
- Múi giờ.
- Tần suất cập nhật.
- Độ trễ dự kiến nếu đã biết.
- Thời điểm nhận dữ liệu gần nhất.
- Trạng thái đã xác nhận hoặc chưa xác nhận.

Tách rõ:

- **Đơn vị phát sinh:** theo sản phẩm/pcs, theo lot, theo sự kiện.
- **Lịch cập nhật:** realtime, theo ca, hằng ngày, batch hoặc thủ công.

Ví dụ "1/lot" không được tự chuyển thành một khoảng thời gian cố định.

Cho phép ghi nhận mã nguồn khác mã chuẩn, ví dụ mã máy trong MES ánh xạ sang mã máy nội bộ. Chỉ liên kết bằng thời gian khi có quy tắc và phạm vi thời gian rõ ràng; không tự suy đoán mọi bản ghi gần nhau đều liên quan.

Lưu metadata của MES/ERP/PLC không có nghĩa đã kết nối trực tiếp với các hệ thống đó. UI phải phân biệt nguồn đã tích hợp và nguồn mới khai báo.

## 5. Liên kết hai lớp

Tạo bản đồ với ba chế độ:

- Nghiệp vụ sản xuất.
- Logic hệ thống.
- Kết hợp hai lớp.

Ví dụ:

- Máy M-01 phục vụ công đoạn ASSY-01.
- Dataset machine_events chứa sự kiện của máy.
- Trường machine_code ánh xạ đến mã máy.
- Dataset production_records chứa sản lượng công đoạn.
- Trường process_code ánh xạ đến mã công đoạn.
- Luồng tổng hợp đọc production_records để tạo báo cáo sản lượng.

Phân biệt rõ loại cạnh:

- Phụ thuộc sản xuất.
- Luồng dữ liệu.
- Ánh xạ dữ liệu–nghiệp vụ.
- Trách nhiệm bộ phận.

Cạnh ánh xạ không mặc nhiên là cạnh gây lan truyền sự cố.

Mỗi quan hệ có chiều, mô tả, nguồn xác nhận và tùy chọn thời gian hiệu lực.

Có thể dùng bảng node/edge kết hợp danh mục có khóa ngoại. Phải bảo đảm endpoint tồn tại, không tạo quan hệ mồ côi, và kiểm tra loại quan hệ hợp lệ.

## 6. Ghi nhận vận hành

Giữ form sản lượng hiện tại và bổ sung các loại dữ liệu:

### Trạng thái thiết bị

- Máy.
- Thời điểm sự kiện.
- Trạng thái RUNNING, STOPPED, MAINTENANCE hoặc UNKNOWN.
- Mã lỗi nếu có.
- Ghi chú.

### Khoảng dừng máy

- Máy.
- Thời gian bắt đầu.
- Thời gian kết thúc, có thể chưa có nếu đang dừng.
- Lý do hoặc mã lỗi.
- Người ghi nhận.

Không nhận thời gian kết thúc trước bắt đầu.

### Kết quả QC

- Lot, sản phẩm và công đoạn.
- Thời điểm kiểm tra.
- Số lượng kiểm tra.
- Số lượng lỗi.
- Loại lỗi.
- Kết quả PASS, FAIL hoặc HOLD.
- Ghi chú.

Số lượng lỗi không vượt số lượng kiểm tra.

### Tình trạng vật tư

- Vật tư.
- Thời điểm ghi nhận.
- Số lượng khả dụng.
- Đơn vị tính.
- Phạm vi kho/chuyền nếu có.

Các form dùng dropdown/tìm kiếm từ danh mục, hạn chế nhập mã tự do gây sai liên kết.

Nếu form cũ đang lưu mã dạng chuỗi, triển khai chuyển đổi tương thích; không gán bừa dữ liệu cũ vào danh mục mới.

Mỗi bản ghi có thời gian sự kiện và thời gian hệ thống tiếp nhận riêng biệt.

## 7. Quản lý sự cố

Tạo sự cố với:

- Mã sự cố.
- Tiêu đề.
- Loại: dừng máy, lỗi chất lượng, thiếu vật tư, chậm dữ liệu hoặc khác.
- Đối tượng phát sinh.
- Thời điểm bắt đầu/kết thúc.
- Mức nghiêm trọng do người dùng chọn.
- Mô tả quan sát.
- Bản ghi vận hành liên quan.
- Trạng thái OPEN, INVESTIGATING, MITIGATING, RESOLVED.
- Bộ phận phụ trách.

Tách riêng:

- Triệu chứng quan sát.
- Nguyên nhân giả thuyết.
- Nguyên nhân đã xác nhận.
- Bằng chứng và người xác nhận.

Không tự ghi kết quả engine thành "nguyên nhân đã xác nhận".

## 8. Engine phân tích tác động

Xây dựng engine Python theo đồ thị và quy tắc.

Đầu vào:

- Sự cố hoặc đối tượng giả định.
- Loại sự cố.
- Thời điểm phân tích.
- Thời lượng dự kiến nếu có.
- Giới hạn số bước lan truyền.
- Các giả định được người dùng nhập.

Cách xử lý:

1. Xác định node khởi phát.
2. Chọn cạnh có thể truyền loại tác động đang xét.
3. Duyệt theo chiều phụ thuộc.
4. Áp dụng điều kiện, phạm vi lot/lệnh và thời gian nếu có.
5. Thu thập đường đi, đối tượng chịu ảnh hưởng và bộ phận liên quan.
6. Lưu kết quả cùng quy tắc và giả định đã sử dụng.

Phải có visited set hoặc cơ chế tương đương để tránh lặp vô hạn khi đồ thị có chu trình.

Phân biệt:

- Ảnh hưởng trực tiếp.
- Ảnh hưởng gián tiếp.
- Rủi ro tiềm năng do chỉ biết quan hệ phụ thuộc.
- Ảnh hưởng quan sát được từ dữ liệu.
- Ảnh hưởng ước tính có đủ tham số.

Không coi mọi node có thể đi tới đều chắc chắn bị dừng.

Nếu thiếu tồn kho đệm, công suất, lịch làm việc hoặc tuyến thay thế, hiển thị "Chưa đủ dữ liệu để định lượng".

Ví dụ công thức demo:

"Sản lượng có nguy cơ mất = thời gian dừng tính bằng phút × tốc độ sản xuất mỗi phút."

Chỉ tính khi có hai đầu vào phù hợp; ghi rõ giả định chưa xét tồn đệm, sản xuất bù và máy thay thế. Không cộng lặp sản lượng qua các công đoạn trên cùng chuỗi.

Chậm dataset là rủi ro thiếu/chậm thông tin; không tự suy thành máy vật lý đã dừng.

Kết quả gồm:

- Đối tượng bị ảnh hưởng.
- Loại tác động.
- Đường lan truyền.
- Bằng chứng.
- Quy tắc đã áp dụng.
- Giả định.
- Thông tin còn thiếu.
- Bộ phận liên quan.

## 9. Gợi ý nguyên nhân

Dùng quy tắc có thể giải thích, chưa dùng ML.

Ví dụ:

- Máy dừng và có mã lỗi thiết bị trong cửa sổ thời gian phù hợp → giả thuyết sự cố thiết bị.
- Vật tư thiếu và công đoạn phụ thuộc vật tư đó giảm sản lượng → giả thuyết thiếu vật tư.
- QC tăng lỗi trong một lot có linh kiện chung → giả thuyết cần kiểm tra lot linh kiện.
- Dataset chậm cập nhật → giả thuyết lỗi thu thập/truyền dữ liệu, không kết luận thiết bị dừng.

Mỗi giả thuyết phải có:

- Nội dung.
- Bằng chứng ủng hộ.
- Thông tin cần kiểm tra thêm.
- Rule ID.
- Mức ưu tiên kiểm tra.

Nếu dùng điểm xếp hạng, giải thích cách tính và ghi rõ đó không phải xác suất nguyên nhân đúng.

Không đủ bằng chứng thì trả "Chưa đủ dữ liệu", không tạo nguyên nhân cho đủ giao diện.

## 10. Quy tắc và hành động theo bộ phận

Lưu quy tắc nghiệp vụ trong YAML riêng, khác YAML chứa SQL.

Quy tắc có:

- ID, tên và phiên bản.
- Loại sự cố.
- Điều kiện.
- Loại quan hệ được phép truyền tác động.
- Bộ phận nhận việc.
- Hành động gợi ý.
- Mức ưu tiên.
- Giả định hoặc giới hạn.

Dùng tập toán tử được hỗ trợ rõ ràng; không dùng eval hoặc thực thi code tùy ý từ YAML.

Ví dụ hành động:

- Bảo trì: kiểm tra máy và mã lỗi.
- QC: kiểm tra bổ sung hoặc đề xuất giữ lot chờ đánh giá.
- Kho: kiểm tra vật tư khả dụng.
- Kế hoạch: đánh giá điều chỉnh lịch.
- IT/Data: kiểm tra nguồn dữ liệu hoặc luồng cập nhật.

Tạo bảng công việc theo bộ phận với trạng thái TODO, IN_PROGRESS, DONE, DISMISSED.

Đây là đề xuất để người dùng xác nhận. Không tự gửi email, điều khiển máy, khóa lot thật hoặc sửa lịch sản xuất ngoài ứng dụng.

## 11. Ba kịch bản mô phỏng

Cung cấp bộ dữ liệu giả nhất quán và có thể tái hiện:

### Kịch bản 1: Máy lắp ráp dừng

- Máy gắn với một công đoạn.
- Có sự kiện STOPPED và mã lỗi.
- Công đoạn sau phụ thuộc đầu ra công đoạn này.
- Gợi ý việc cho bảo trì và kế hoạch.
- Thiếu dữ liệu tồn đệm thì không khẳng định công đoạn sau dừng ngay.

### Kịch bản 2: Lot có tỷ lệ lỗi QC cao

- Có kết quả QC gắn đúng lot, sản phẩm, công đoạn.
- Lot liên quan đến vật tư và công đoạn sau.
- Đánh dấu phạm vi lot có nguy cơ.
- Gợi ý QC kiểm tra và kho truy xuất vật tư.
- Nguyên nhân vật tư chỉ là giả thuyết khi chưa xác minh.

### Kịch bản 3: Thiếu vật tư

- Vật tư có mức khả dụng thấp hơn ngưỡng demo được cấu hình.
- Có công đoạn/lệnh sử dụng vật tư đó.
- Hiển thị rủi ro đối với kế hoạch liên quan.
- Gợi ý kho và kế hoạch xử lý.

Mỗi kịch bản có:

- Dữ liệu đầu vào.
- Quan hệ sử dụng.
- Sự cố ban đầu.
- Quan sát.
- Kết quả dự kiến.
- Quy tắc áp dụng.
- Giới hạn.

Hiển thị nhãn "Dữ liệu mô phỏng — chưa xác nhận bởi Denso".

Có nút nạp demo theo thao tác chủ động, không tự nạp vào dữ liệu thật khi khởi động. Nạp lại không tạo trùng.

Phân tích what-if chỉ lưu trong phạm vi mô phỏng, không sửa trạng thái vận hành thật hoặc tự tạo công việc thật.

## 12. Trang thông tin khảo sát

Tạo màn hình theo dõi thông tin cần xác nhận với nhà máy cho chín nhóm:

1. Quy trình và quan hệ phụ thuộc.
2. Ảnh hưởng khi xảy ra sự cố.
3. Dữ liệu vận hành đang thu thập.
4. Nơi phát sinh và phương thức thu thập.
5. Hệ thống lưu trữ và khóa liên kết.
6. Tần suất phát sinh/cập nhật.
7. Cách xác định nguyên nhân và quy tắc xử lý.
8. Bộ phận nhận việc và hành động.
9. Ba tình huống thực tế.

Mỗi mục có nội dung trả lời, người cung cấp, thời điểm, trạng thái chưa xác nhận/đã xác nhận và ghi chú.

Không biến giả định demo thành câu trả lời chính thức của công ty.

## 13. Giao diện và API

- Dashboard lấy số liệu thật từ database; trạng thái rỗng hiển thị rõ.
- Tách số liệu demo khỏi dữ liệu thực.
- Desktop ưu tiên bảng và bản đồ.
- Android ưu tiên nhập liệu, xem sự cố và công việc.
- Đồ thị có lọc loại node, chọn node xem chi tiết và tô đường ảnh hưởng.
- Có danh sách đường lan truyền dạng chữ để đọc được trên màn hình nhỏ.
- Thư viện vẽ đồ thị nếu dùng phải được đóng gói local.
- Có loading, lỗi API, empty state và xác nhận trước thao tác ảnh hưởng dữ liệu.
- Không hardcode địa chỉ API.
- Giữ bảo vệ chống gửi trùng cho các thao tác tạo bản ghi quan trọng.
- API có validation, phân trang, filter và mã lỗi phù hợp.

## 14. Lưu vết kết quả phân tích

Lưu mỗi lần phân tích:

- Sự cố hoặc kịch bản nguồn.
- Thời điểm chạy.
- Đầu vào.
- Phiên bản quy tắc.
- Các cạnh và dữ liệu bằng chứng đã dùng.
- Kết quả ảnh hưởng.
- Giả thuyết nguyên nhân.
- Hành động đề xuất.
- Giả định và giới hạn.

Giữ snapshot đủ để xem lại kết quả cũ khi danh mục hoặc quy tắc đã thay đổi.

## 15. Migration và kiểm thử

- Tạo migration có phiên bản, chạy có kiểm soát trong quá trình khởi động.
- Không chỉ dùng CREATE TABLE IF NOT EXISTS để xử lý thay đổi schema.
- Giữ tương thích dữ liệu sản lượng cũ.
- Migration lỗi phải báo rõ và không tiếp tục với schema dở dang.
- Không sửa dữ liệu không thể ánh xạ một cách chắc chắn.

Kiểm thử có ý nghĩa cho:

- Luồng nhập vận hành → tạo sự cố → phân tích → đề xuất hành động.
- Lan truyền đúng chiều và đúng loại cạnh.
- Đồ thị có chu trình.
- Thiếu dữ liệu định lượng.
- Không cộng lặp ảnh hưởng.
- Phạm vi lot/lệnh.
- Không lẫn demo với dữ liệu thật.
- Ba kịch bản có kết quả giải thích được.
- Chức năng nhập sản lượng cũ vẫn chạy.

Nếu không có PostgreSQL trong môi trường, nói rõ phần chưa chạy được. Không tuyên bố đã kiểm thử tích hợp khi chỉ dùng mock.

## 16. Trình tự và bàn giao

Triển khai theo thứ tự:

1. Đọc và đánh giá project.
2. Schema/migration/danh mục.
3. Nguồn dữ liệu và liên kết hai lớp.
4. Form vận hành và sự cố.
5. Engine quy tắc.
6. Bản đồ, kết quả và công việc.
7. Ba kịch bản demo.
8. Kiểm thử và README.

Thực hiện tới khi hoàn thành phạm vi, không dừng ở phần đề xuất.

README cần hướng dẫn:

- Cập nhật dependencies.
- Cấu hình cần bổ sung.
- Chạy `python run.py`.
- Truy cập từ máy tính và Android.
- Nạp dữ liệu demo.
- Thao tác từng kịch bản từ đầu đến kết quả.
- Đọc đường lan truyền và bằng chứng.
- Phân biệt giả thuyết với nguyên nhân đã xác nhận.
- Những thông tin phải khảo sát thêm tại Denso.

Khi bàn giao, báo cáo các chức năng đã làm, các kiểm thử đã chạy và giới hạn còn lại. Tách rõ tính năng hoạt động thật, dữ liệu mô phỏng và tích hợp hệ thống ngoài chưa triển khai.
