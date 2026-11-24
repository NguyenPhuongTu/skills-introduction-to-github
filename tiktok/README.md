# Tổng hợp video TikTok tự động

Quy trình chạy trên **GitHub Actions** (máy chủ GitHub có Internet đầy đủ):

1. **Tải video** + caption, hashtag, số liệu: `yt-dlp`, dự phòng qua API `tikwm` (hỗ trợ cả bài đăng dạng ảnh).
2. **Chép lời** có mốc thời gian: `faster-whisper` (mô hình `large-v3-turbo`, tiếng Việt tốt).
3. **Trích khung hình** theo điểm chuyển cảnh + theo nhịp đều (tối đa 48 khung), ghép thành ảnh tổng hợp.
4. **Đọc chữ trên màn hình** (OCR tiếng Việt + Anh) bằng `tesseract`.
5. Commit kết quả vào `tiktok/results/<id video>/` → Claude đọc lời + xem khung hình → viết `TOM_TAT.md`.

## Cách dùng

```bash
bash tiktok/submit.sh "https://www.tiktok.com/@kenh/video/123..."        # tự nhận ngôn ngữ
bash tiktok/submit.sh "https://vt.tiktok.com/xxxx/" vi                   # ép tiếng Việt
```
Hoặc trên GitHub: tab **Actions → TikTok Analyze → Run workflow** (cần workflow có trên nhánh mặc định).

## Kết quả trong `tiktok/results/<id>/`

| File | Nội dung |
|---|---|
| `REPORT.md` | Báo cáo thô: thông tin, caption, lời nói theo thời gian, chữ trên màn hình, ảnh tổng hợp |
| `transcript.txt` / `.srt` | Lời nói có mốc thời gian |
| `frames/`, `sheets/` | Khung hình lẻ và ảnh ghép 4×3 có ghi mốc thời gian |
| `ocr.json`, `info.json` | Chữ OCR từng khung; metadata |
| `TOM_TAT.md` | Bản tổng hợp + giải thích cách làm (Claude viết) |

Video gốc được lưu thành artifact của lượt chạy Actions (giữ 7 ngày).
