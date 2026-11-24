# Tổng hợp: "Văn phòng nhân viên AI" tự động làm nội dung & bán hàng

- **Video:** https://vt.tiktok.com/ZSsF5bkrg/ · kênh **@nganthomvlog** (Ngân Thơm Shop) · 8 phút 10 giây · ~102 nghìn lượt xem
- **Người trình bày:** anh Tuấn (Lê Tuấn AI Studio)
- **Dạng video:** trình diễn hệ thống có thật và quảng cáo khóa học. Video **cho xem kết quả**, **không hướng dẫn cài đặt** từng bước.
- **Nguồn dữ liệu:** lời nói chép tự động, phụ đề gốc của TikTok, 48 khung hình đã xem kỹ. Chi tiết thô nằm ở [REPORT.md](REPORT.md).

---

## 1. Video nói gì (tóm tắt 30 giây)

Anh Tuấn dựng một **"văn phòng ảo 3D"**. Mỗi nhân vật ngồi bàn trong đó là một **AI agent** (nhân viên AI) phụ trách một việc. Các agent được chia thành **đội**, mỗi đội lo một kênh hoặc một mảng: chăm sóc khách trên Zalo, từng fanpage Facebook, làm ảnh, làm video quảng cáo...

Có hai cách làm việc:
1. **Tự động theo lịch.** Ví dụ 7h và 17h mỗi ngày, cả dây chuyền tự chạy: tìm tin → viết kịch bản → dựng video → kiểm duyệt → đăng fanpage. Chủ không phải làm gì.
2. **Ra lệnh qua Telegram trên điện thoại.** Nhắn cho "trợ lý ảnh" hoặc "trợ lý video", AI tự làm rồi gửi kết quả về điện thoại sau vài phút.

Ý chính anh muốn truyền tải: *không cần ngồi máy tính gõ câu lệnh, chỉ thiết lập ban đầu, sau đó AI tự vận hành.*

---

## 2. Cấu trúc hệ thống thấy trong video

### 2.1. Văn phòng 3D (bảng điều khiển trực quan)
- Là một **web app chạy trên máy tính**. Màn hình MacBook ghi rõ: `Le Tuan AI Studio.command`, mở tại `http://127.0.0.1:7790/index.html`, và một cổng `7788` "dành cho học viên".
- Mỗi khu có biển tên đội và số nhân sự, ví dụ: **"KÊNH KIẾN TRÚC BIỂN – 4 nhân sự · 1 đang làm"**, "KÊNH BÁO DN&HN", "GIÁM ĐỐC AI", "KÊNH MÔI GIỚI", "KÊNH GIA ĐÌNH BÉ...". Có khu báo "2 lỗi".
- Mỗi bàn có **2 màn hình**:
  - màn trái là **thống kê** (việc chờ, đang làm, đã xong);
  - màn phải là **nhật ký việc đang chạy**.
- Agent rảnh thì nhân vật "ngồi lướt điện thoại". Agent có việc thì "gõ máy". Trạng thái hiện chữ *Sẵn sàng / Đang làm / Đang nghỉ*.
- Trên MacBook, anh Tuấn dùng **Claude** (cửa sổ "Trợ lý trên máy MacBook") để vận hành và sửa app này.

### 2.2. Dây chuyền "Kênh Kiến Trúc Biển" (fanpage tin tức, 4 nhân viên)

| # | Nhân viên AI | Vai trò | Thấy trên màn hình |
|---|---|---|---|
| 1 | **Quang Vinh** | Tìm tin hot và viết kịch bản | "Viết 3 kịch bản KTB19–21 (hổ Pakistan, kế toán 738 triệu, Huy bến xe) từ **VnExpress/Tuổi Trẻ** 15–16/11" |
| 2 | **Thế Anh** | Dựng video | Bảng "DỰNG VIDEO": kịch bản chờ dựng 11, đang dựng KTB14–16, video chờ kiểm, bị trả về sửa |
| 3 | **Hà Vy** | Kiểm duyệt (QC) | Chấm điểm: "**ĐẠT ĐĂNG 9.7/10**". Kiểm nội dung, hình ảnh, "mặt mũi" nhân vật |
| 4 | **Gia Khánh** | Đăng bài | Đăng Reels lên fanpage qua **Meta Business Suite**, có lịch hẹn giờ đăng |

Kết quả là trang Facebook có hàng loạt **Reels dạng "MC đọc tin"** dùng người dẫn do AI tạo. Theo lời anh Tuấn, "nhiều người nhìn vào sẽ không biết đấy là AI".

### 2.3. Trợ lý làm ảnh: "Kim Oanh – Họa sĩ ảnh"
- Lệnh gửi qua **Telegram bot "Trợ Lý Ảnh Kim Oanh"**. Ví dụ: *"Làm cho tao một bức ảnh đang đi du lịch bên Pháp cùng vợ."*
- Nhật ký trên màn hình agent ghi các bước:
  1. Nhận lệnh làm ảnh từ sếp Tuấn
  2. Lấy câu lệnh (prompt) lần trước làm khuôn
  3. Đọc tệp `tuan-thom-di-choi-my.txt` (mô tả và ảnh gốc khuôn mặt hai vợ chồng)
  4. Tạo câu lệnh ảnh "Pháp" từ khuôn cũ
  5. **Vẽ bằng ChatGPT web (gói trả phí)** hoặc Gemini, rồi gửi lại qua Telegram
- Vài phút sau, điện thoại nhận được ảnh hai vợ chồng ở tháp Eiffel. Lời nhắn của bot: *"Dạ sếp, ảnh xong rồi ạ! Em làm sếp với chị Thơm..."*.
- Điểm mấu chốt: agent đã có **"hàng trăm skill"** (mẫu câu lệnh ảnh đẹp) sẵn trong đầu, nên người không biết viết prompt vẫn ra ảnh đẹp.

### 2.4. Trợ lý video quảng cáo
- Telegram bot "Trợ Lý Video Quảng Cáo". Lệnh: *"Làm cho tao video giới thiệu về khóa học AI chuyên sâu tại Vinh bằng omni 1.2, 10s."*
- Bot trả lời: *"Em đang viết lời rồi quay... Em đang quay trên **Google Flow** (Omni 1.2 · 10 giây), khoảng 2–4 phút."*
- Kết quả: một video MC (AI) giới thiệu khóa học, gửi thẳng về Telegram.

### 2.5. Các đội khác (chỉ nhắc qua)
- Đội **chăm sóc, tư vấn khách hàng tự động trên Zalo**
- Mỗi fanpage Facebook có một đội riêng

---

## 3. Giải thích cách làm: dựng lại hệ thống như vậy

> ⚠️ Video **không** chỉ cách cài đặt; phần này thuộc khóa học có phí. Dưới đây là cách dựng hệ thống **tương tự**. Tôi suy ra từ những gì thấy trên màn hình kết hợp với cách làm phổ biến hiện nay, **không phải** nguyên văn quy trình của anh Tuấn.

### Bước 1 – Chọn "bộ não" cho các agent
- Dùng một AI agent chạy được trên máy tính: điều khiển trình duyệt, đọc/ghi file, chạy lệnh. Anh Tuấn dùng **Claude** trên Mac. Các lựa chọn tương tự: Claude Code / Claude Desktop, hoặc các framework agent khác.
- Mỗi "nhân viên" thực chất là **một agent + một bản mô tả vai trò** (system prompt hoặc "skill"): làm gì, nhận việc từ đâu, giao cho ai, tiêu chuẩn chất lượng ra sao.

### Bước 2 – Viết "skill" cho từng vai trò
Mỗi skill là một file hướng dẫn. Ví dụ:
- *Biên kịch:* nguồn tin (VnExpress, Tuổi Trẻ...), cách chọn tin hot, khung kịch bản 30–60 giây, đặt mã kịch bản (KTB19, KTB20...).
- *Dựng video:* cách đưa kịch bản vào công cụ tạo video (Google Flow / Veo...), giọng đọc, nhạc, phụ đề, tỉ lệ 9:16.
- *Kiểm duyệt:* thang chấm điểm, ngưỡng đạt (ví dụ ≥ 9/10 mới đăng, thấp hơn thì trả về sửa).
- *Họa sĩ ảnh:* thư viện mẫu câu lệnh ảnh đẹp, cộng file mô tả khuôn mặt hoặc nhân vật cố định để ảnh luôn giống người thật.

### Bước 3 – Nối các agent thành dây chuyền
- Dùng **thư mục / hàng đợi chung**. Agent A làm xong thì ghi file vào "hộp thư" của agent B (ví dụ `kich-ban-cho-dung/`, `video-cho-kiem/`, `bi-tra-ve-sua/`). Đúng như các ô đếm "Kịch bản chờ dựng / Video chờ kiểm / Bị trả về sửa" trên màn hình.
- Mỗi agent tự kiểm hộp thư của mình. Có việc thì làm, không có thì "ngồi chơi điện thoại".

### Bước 4 – Kết nối công cụ tạo nội dung
- **Ảnh:** ChatGPT (gói trả phí) hoặc Gemini. Agent điều khiển trình duyệt đã đăng nhập sẵn, hoặc dùng API.
- **Video:** Google Flow (Omni/Veo) cho video MC AI 8–10 giây; muốn dài hơn thì ghép nhiều đoạn.
- **Đăng bài:** Meta Business Suite (hẹn giờ đăng Reels) hoặc Facebook Graph API.

### Bước 5 – Ra lệnh từ điện thoại qua Telegram
- Tạo bot bằng **@BotFather** trên Telegram, mỗi trợ lý một bot (Trợ lý ảnh, Trợ lý video...).
- Một chương trình nhỏ trên máy tính nhận tin nhắn từ bot, chuyển thành "việc" cho đúng agent, rồi gửi kết quả (ảnh, video) ngược lại qua bot.
- Máy tính phải **luôn bật** và luôn đăng nhập ChatGPT / Google Flow / Facebook.

### Bước 6 – Lịch tự động
- Đặt lịch (cron / Task Scheduler) cho từng đội, ví dụ **7h và 17h**: biên kịch tìm tin → chuyển dựng → chuyển kiểm → chuyển đăng. Chuỗi tự chạy mỗi ngày.

### Bước 7 – Làm "văn phòng 3D" để theo dõi (tùy chọn)
- Một trang web nội bộ (`127.0.0.1:7790`) đọc trạng thái các hàng đợi và nhật ký, rồi vẽ mỗi agent thành nhân vật 3D, kèm bảng số liệu.
- Phần này **chỉ để quan sát và trình diễn**, không bắt buộc để hệ thống chạy. Một bảng tính hoặc dashboard đơn giản cũng làm được việc tương tự.

---

## 4. Mẹo rút ra từ video
1. **Chia nhỏ vai trò** (tìm tin, dựng, kiểm, đăng) thay vì một AI làm hết. Dễ kiểm soát lỗi, dễ thay một khâu.
2. **Luôn có khâu kiểm duyệt (QC) có điểm số** trước khi đăng, và cho phép "trả về sửa".
3. **Lưu khuôn prompt tốt** để dùng lại ("lấy câu lệnh lần trước làm khuôn"), kèm file mô tả nhân vật cố định cho ảnh luôn đồng nhất.
4. **Điều khiển qua Telegram** giúp ra lệnh mọi lúc mà không cần mở máy tính.
5. **Bắt đầu từ một kênh** (ví dụ một fanpage), chạy ổn rồi mới nhân thêm đội.

## 5. Lưu ý và rủi ro (video không nhắc)
- **Gắn nhãn nội dung AI:** Facebook và TikTok yêu cầu ghi rõ video có người hoặc giọng nói giống thật do AI tạo. Video nhấn mạnh "người xem không biết là AI", điều này dễ bị **giảm tương tác, gỡ bài hoặc khóa trang** nếu không gắn nhãn.
- **Bản quyền tin tức:** viết lại tin từ VnExpress/Tuổi Trẻ thì nên ghi nguồn và tóm tắt bằng lời mình, tránh sao chép.
- **Điều khiển ChatGPT/Gemini bằng tự động hóa trình duyệt** có thể vi phạm điều khoản dịch vụ và dễ hỏng khi giao diện thay đổi. Dùng API chính thức thì ổn định hơn.
- **Dùng ảnh khuôn mặt người thật** (vợ, khách hàng) cần có sự đồng ý.
- **Chi phí:** cần gói trả phí ChatGPT, Google Flow, máy tính chạy 24/7, cộng công sức thiết lập ban đầu và bảo trì khi có lỗi (văn phòng đang báo "2 lỗi").
- Cuối video là **lời mời đăng ký khóa học** ("học thật làm thật, cầm tay chỉ việc... nhắn Tuấn đăng ký"). Phần cài đặt cụ thể nằm trong khóa học.

---

## 6. Tóm tắt ngắn
**Ý tưởng:** biến AI thành một "công ty ảo". Mỗi AI agent là một nhân viên có vai trò riêng, xếp thành dây chuyền **Tìm tin → Viết kịch bản → Dựng video (Google Flow) → Kiểm duyệt chấm điểm → Đăng Facebook**, chạy tự động theo lịch. Ngoài ra có các trợ lý **làm ảnh (ChatGPT/Gemini)** và **làm video quảng cáo** nhận lệnh qua **Telegram** và gửi kết quả về điện thoại. Mọi thứ hiển thị trên một **văn phòng 3D** để theo dõi.

**Công cụ thấy trong video:** Claude (vận hành agent trên Mac), ChatGPT web gói trả phí, Gemini, Google Flow (Omni 1.2), Telegram bot, Meta Business Suite, Zalo, nguồn tin VnExpress/Tuổi Trẻ.

**Thực chất:** video là bản demo kết quả để bán khóa học; cách cài đặt chi tiết không được công bố. Có thể tự dựng hệ thống tương tự theo 7 bước ở mục 3, nhưng cần lưu ý gắn nhãn nội dung AI và điều khoản của các nền tảng.
