#!/usr/bin/env python3
"""
Xử lý một video TikTok thành bộ dữ liệu để tổng hợp:
  1. Tải video + thông tin (yt-dlp, dự phòng qua API tikwm) - hỗ trợ cả bài dạng ảnh (slideshow)
  2. Tách âm thanh và chép lời có mốc thời gian (faster-whisper)
  3. Trích khung hình theo cảnh + theo nhịp đều, ghép thành ảnh tổng hợp (contact sheet)
  4. Đọc chữ hiện trên màn hình bằng OCR (tesseract, tiếng Việt + Anh)
  5. Ghi REPORT.md + LAST_RUN.json để biết lượt chạy đã xong

Dùng:  python tiktok/process.py --request tiktok/request.txt --out tiktok/results
"""
import argparse
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import traceback
import urllib.parse
import urllib.request

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
MAX_FRAMES = 48


def log(*a):
    print(*a, flush=True)


def run(cmd, check=True, capture=False):
    log("+", " ".join(str(c) for c in cmd))
    return subprocess.run(cmd, check=check, capture_output=capture, text=True)


def read_request(path):
    """request.txt: các dòng key=value (url=..., nonce=..., lang=..., model=...)."""
    req = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                req[k.strip().lower()] = v.strip()
            elif line.startswith("http"):
                req["url"] = line
    if not req.get("url"):
        raise SystemExit("request.txt không có url=")
    return req


def http_get(url, timeout=60):
    r = urllib.request.Request(url, headers={"User-Agent": UA, "Referer": "https://www.tiktok.com/"})
    with urllib.request.urlopen(r, timeout=timeout) as resp:
        return resp.read()


def save(url, path):
    with open(path, "wb") as f:
        f.write(http_get(url, timeout=180))
    return path


# ---------------------------------------------------------------- tải video
def download_ytdlp(url, work):
    errors = []
    for extra in (["--impersonate", "chrome"], []):
        for f in os.listdir(work):
            if f.startswith("video."):
                os.remove(os.path.join(work, f))
        cmd = ["yt-dlp", "--no-playlist", "--no-progress", "-f", "bv*+ba/b",
               "--merge-output-format", "mp4", "--write-info-json",
               "-o", os.path.join(work, "video.%(ext)s"), *extra, url]
        p = run(cmd, check=False, capture=True)
        log(p.stdout[-3000:], p.stderr[-3000:])
        vids = [f for f in os.listdir(work) if f.startswith("video.") and f.endswith((".mp4", ".mkv", ".webm", ".mov"))]
        if p.returncode == 0 and vids:
            info = json.load(open(os.path.join(work, "video.info.json"), encoding="utf-8"))
            # phụ đề (nếu TikTok có) - tải riêng, lỗi cũng không sao
            run(["yt-dlp", "--no-playlist", "--skip-download", "--write-subs", "--write-auto-subs",
                 "--sub-langs", "all", "-o", os.path.join(work, "sub.%(ext)s"), *extra, url], check=False)
            return {"source": "yt-dlp", "video": os.path.join(work, vids[0]), "images": [], "audio": None, "info": info}
        errors.append(p.stderr[-800:])
    raise RuntimeError("yt-dlp thất bại:\n" + "\n---\n".join(errors))


def download_tikwm(url, work):
    api = "https://www.tikwm.com/api/?" + urllib.parse.urlencode({"url": url, "hd": 1})
    data = json.loads(http_get(api))
    if data.get("code") != 0:
        raise RuntimeError(f"tikwm lỗi: {data.get('msg')}")
    d = data["data"]

    def absu(u):
        return u if not u or u.startswith("http") else "https://www.tikwm.com" + u

    author = d.get("author") or {}
    info = {
        "id": d.get("id"), "title": d.get("title"), "description": d.get("title"),
        "uploader": author.get("unique_id"), "channel": author.get("nickname"),
        "duration": d.get("duration"), "view_count": d.get("play_count"),
        "like_count": d.get("digg_count"), "comment_count": d.get("comment_count"),
        "timestamp": d.get("create_time"), "webpage_url": url,
        "track": (d.get("music_info") or {}).get("title"),
    }
    res = {"source": "tikwm", "video": None, "images": [], "audio": None, "info": info}
    if d.get("images"):  # bài đăng dạng ảnh
        for i, im in enumerate(d["images"], 1):
            res["images"].append(save(absu(im), os.path.join(work, f"image_{i:02d}.jpg")))
        if d.get("music"):
            res["audio"] = save(absu(d["music"]), os.path.join(work, "music.mp3"))
    else:
        play = absu(d.get("hdplay") or d.get("play"))
        res["video"] = save(play, os.path.join(work, "video.mp4"))
    return res


def download(url, work):
    errs = []
    if "/photo/" not in url:
        try:
            return download_ytdlp(url, work)
        except Exception as e:  # noqa
            errs.append(str(e))
            log("yt-dlp không được, chuyển sang tikwm...", e)
    try:
        return download_tikwm(url, work)
    except Exception as e:  # noqa
        errs.append(str(e))
    raise RuntimeError("Không tải được video.\n" + "\n====\n".join(errs))


# ---------------------------------------------------------------- media
def probe(path):
    p = run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type",
             "-of", "json", path], capture=True)
    j = json.loads(p.stdout)
    dur = float(j.get("format", {}).get("duration") or 0)
    types = {s.get("codec_type") for s in j.get("streams", [])}
    return dur, "audio" in types, "video" in types


def extract_wav(src, work):
    wav = os.path.join(work, "audio.wav")
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", src, "-vn", "-ac", "1", "-ar", "16000", wav])
    return wav


def fmt_ts(t, srt=False):
    t = max(0.0, t)
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    if srt:
        return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int((s % 1) * 1000):03d}"
    return f"{int(h)}:{int(m):02d}:{int(s):02d}" if h else f"{int(m):02d}:{int(s):02d}"


def transcribe(wav, model_name, lang):
    from faster_whisper import WhisperModel
    log(f"Nạp mô hình {model_name} ...")
    model = WhisperModel(model_name, device="cpu", compute_type="int8", cpu_threads=os.cpu_count() or 4)
    prompt = "Xin chào các bạn, hôm nay mình sẽ hướng dẫn các bạn cách làm." if lang in (None, "", "vi") else None
    segs, info = model.transcribe(wav, language=lang or None, beam_size=5, vad_filter=True,
                                  initial_prompt=prompt, condition_on_previous_text=False)
    out = [{"start": s.start, "end": s.end, "text": s.text.strip()} for s in segs if s.text.strip()]
    return out, info.language, info.language_probability


# ---------------------------------------------------------------- khung hình
def pick_times(video, dur):
    p = run(["ffmpeg", "-hide_banner", "-i", video, "-vf", "select='gt(scene,0.30)',showinfo",
             "-an", "-f", "null", "-"], check=False, capture=True)
    scenes = sorted(float(x) for x in re.findall(r"pts_time:([0-9.]+)", p.stderr))
    step = min(10.0, max(1.5, dur / 30.0))
    chosen = []
    for t in [0.3] + scenes:
        if t < dur and all(abs(t - c) >= 1.0 for c in chosen):
            chosen.append(t)
    t = step
    while t < dur - 0.3:
        if all(abs(t - c) >= step * 0.6 for c in chosen):
            chosen.append(t)
        t += step
    chosen.sort()
    if len(chosen) > MAX_FRAMES:
        k = len(chosen) / MAX_FRAMES
        chosen = [chosen[int(i * k)] for i in range(MAX_FRAMES)]
    return chosen


def extract_frames(video, dur, frames_dir):
    os.makedirs(frames_dir, exist_ok=True)
    frames = []
    for t in pick_times(video, dur):
        name = f"f_{int(t * 10):05d}.jpg"
        path = os.path.join(frames_dir, name)
        run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-ss", f"{t:.2f}", "-i", video,
             "-frames:v", "1", "-vf", "scale=720:-2", "-q:v", "4", path], check=False)
        if os.path.exists(path):
            frames.append({"t": t, "path": path})
    return frames


def copy_images(images, frames_dir):
    from PIL import Image
    os.makedirs(frames_dir, exist_ok=True)
    frames = []
    for i, src in enumerate(images, 1):
        im = Image.open(src).convert("RGB")
        if im.width > 720:
            im = im.resize((720, int(im.height * 720 / im.width)))
        path = os.path.join(frames_dir, f"anh_{i:02d}.jpg")
        im.save(path, quality=82)
        frames.append({"t": None, "idx": i, "path": path})
    return frames


def contact_sheets(frames, sheets_dir, cols=4, rows=3, cell_w=320):
    from PIL import Image, ImageDraw, ImageFont
    os.makedirs(sheets_dir, exist_ok=True)
    try:
        font = ImageFont.load_default(size=26)
    except TypeError:
        font = ImageFont.load_default()
    per = cols * rows
    out = []
    for n in range(0, len(frames), per):
        chunk = frames[n:n + per]
        thumbs = []
        for fr in chunk:
            im = Image.open(fr["path"]).convert("RGB")
            im = im.resize((cell_w, int(im.height * cell_w / im.width)))
            thumbs.append((fr, im))
        cell_h = max(im.height for _, im in thumbs)
        sheet = Image.new("RGB", (cols * cell_w, rows * cell_h), "black")
        draw = ImageDraw.Draw(sheet)
        for i, (fr, im) in enumerate(thumbs):
            x, y = (i % cols) * cell_w, (i // cols) * cell_h
            sheet.paste(im, (x, y))
            label = fmt_ts(fr["t"]) if fr.get("t") is not None else f"Ảnh {fr['idx']}"
            draw.rectangle([x, y, x + 110, y + 34], fill="black")
            draw.text((x + 6, y + 3), label, fill="yellow", font=font)
        path = os.path.join(sheets_dir, f"sheet_{n // per + 1:02d}.jpg")
        sheet.save(path, quality=80)
        out.append(path)
    return out


def ocr(frames):
    if not shutil.which("tesseract"):
        log("Không có tesseract, bỏ qua OCR")
        return
    p = run(["tesseract", "--list-langs"], check=False, capture=True)
    langs = "vie+eng" if "vie" in (p.stdout + p.stderr) else "eng"
    for fr in frames:
        p = run(["tesseract", fr["path"], "stdout", "-l", langs, "--psm", "11"], check=False, capture=True)
        lines = []
        for ln in p.stdout.splitlines():
            ln = ln.strip()
            letters = sum(ch.isalnum() for ch in ln)
            if letters >= 3 and letters / max(1, len(ln)) > 0.6:
                lines.append(ln)
        fr["ocr"] = " | ".join(lines)


# ---------------------------------------------------------------- báo cáo
def slug(s):
    return re.sub(r"[^A-Za-z0-9_-]+", "_", str(s or "video"))[:60].strip("_") or "video"


def write_report(rd, req, dl, info, dur, segs, lang_info, frames, sheets, subs):
    rel = lambda p: os.path.relpath(p, rd)  # noqa: E731
    desc = info.get("description") or info.get("title") or ""
    tags = sorted(set(re.findall(r"#(\w+)", desc)) | set(info.get("tags") or []))
    L = [f"# Báo cáo video TikTok `{info.get('id')}`", "",
         f"- **Link:** {req['url']}",
         f"- **Kênh:** @{info.get('uploader') or info.get('uploader_id') or '?'} ({info.get('channel') or info.get('creator') or ''})",
         f"- **Thời lượng:** {fmt_ts(dur) if dur else '?'}",
         f"- **Lượt xem / thích / bình luận:** {info.get('view_count')} / {info.get('like_count')} / {info.get('comment_count')}",
         f"- **Nhạc:** {info.get('track') or ''}",
         f"- **Nguồn tải:** {dl['source']}  ·  **Xử lý lúc:** {datetime.datetime.utcnow():%Y-%m-%d %H:%M} UTC",
         "", "## Mô tả (caption)", "", desc or "_(trống)_", ""]
    if tags:
        L += ["**Hashtag:** " + " ".join("#" + t for t in tags), ""]
    L += ["## Lời nói (chép tự động)", ""]
    if lang_info:
        L += [f"_Ngôn ngữ nhận dạng: {lang_info[0]} ({lang_info[1]:.0%})_", ""]
    if segs:
        L += [f"- `[{fmt_ts(s['start'])}]` {s['text']}" for s in segs]
    else:
        L += ["_(Không có lời nói - có thể chỉ có nhạc nền)_"]
    if subs:
        L += ["", "Phụ đề gốc của TikTok: " + ", ".join(f"[{os.path.basename(s)}]({rel(s)})" for s in subs)]
    L += ["", "## Chữ trên màn hình (OCR theo khung hình)", ""]
    last = None
    for fr in frames:
        txt = fr.get("ocr")
        if txt and txt != last:
            lab = fmt_ts(fr["t"]) if fr.get("t") is not None else f"Ảnh {fr['idx']}"
            L.append(f"- `[{lab}]` {txt}")
            last = txt
    if last is None:
        L.append("_(Không đọc được chữ)_")
    L += ["", "## Ảnh tổng hợp khung hình", ""] + [f"![{os.path.basename(s)}]({rel(s)})" for s in sheets]
    L += ["", f"Tổng {len(frames)} khung hình trong thư mục `frames/`."]
    with open(os.path.join(rd, "REPORT.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")


def process(req, out_root):
    work = tempfile.mkdtemp(prefix="tt_")
    dl = download(req["url"], work)
    info = dl["info"]
    rd = os.path.join(out_root, slug(info.get("id")))
    if os.path.isdir(rd):
        shutil.rmtree(rd)
    os.makedirs(rd)
    keep = ["id", "title", "description", "uploader", "uploader_id", "channel", "creator", "duration",
            "view_count", "like_count", "comment_count", "repost_count", "timestamp", "upload_date",
            "webpage_url", "track", "artist", "tags"]
    with open(os.path.join(rd, "info.json"), "w", encoding="utf-8") as f:
        json.dump({k: info.get(k) for k in keep if info.get(k) is not None}, f, ensure_ascii=False, indent=2)

    subs = []
    for fn in os.listdir(work):
        if fn.startswith("sub.") and fn.endswith((".vtt", ".srt")):
            shutil.copy(os.path.join(work, fn), os.path.join(rd, fn))
            subs.append(os.path.join(rd, fn))

    frames_dir = os.path.join(rd, "frames")
    dur, segs, lang_info = 0.0, [], None
    if dl["video"]:
        dur, has_audio, _ = probe(dl["video"])
        frames = extract_frames(dl["video"], dur, frames_dir)
        audio_src = dl["video"] if has_audio else None
    else:
        frames = copy_images(dl["images"], frames_dir)
        audio_src = dl["audio"]
        if audio_src:
            dur = probe(audio_src)[0]
    if audio_src:
        wav = extract_wav(audio_src, work)
        try:
            segs, lg, lp = transcribe(wav, req.get("model") or "large-v3-turbo", req.get("lang"))
        except Exception as e:  # noqa - mô hình lớn lỗi thì thử mô hình nhỏ
            log("Mô hình chính lỗi, dùng 'small':", e)
            segs, lg, lp = transcribe(wav, "small", req.get("lang"))
        lang_info = (lg, lp)
    with open(os.path.join(rd, "transcript.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(f"[{fmt_ts(s['start'])}] {s['text']}" for s in segs) + "\n")
    with open(os.path.join(rd, "transcript.srt"), "w", encoding="utf-8") as f:
        for i, s in enumerate(segs, 1):
            f.write(f"{i}\n{fmt_ts(s['start'], True)} --> {fmt_ts(s['end'], True)}\n{s['text']}\n\n")

    ocr(frames)
    sheets = contact_sheets(frames, os.path.join(rd, "sheets")) if frames else []
    with open(os.path.join(rd, "ocr.json"), "w", encoding="utf-8") as f:
        json.dump([{"t": fr.get("t"), "file": os.path.basename(fr["path"]), "text": fr.get("ocr", "")}
                   for fr in frames], f, ensure_ascii=False, indent=2)
    write_report(rd, req, dl, info, dur, segs, lang_info, frames, sheets, subs)
    # để lại file video gốc cho bước upload artifact
    media = dl["video"] or dl["audio"]
    if media and os.environ.get("MEDIA_OUT"):
        os.makedirs(os.environ["MEDIA_OUT"], exist_ok=True)
        shutil.copy(media, os.path.join(os.environ["MEDIA_OUT"], os.path.basename(media)))
    return rd


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--request", default="tiktok/request.txt")
    ap.add_argument("--url")
    ap.add_argument("--out", default="tiktok/results")
    a = ap.parse_args()
    req = {"url": a.url} if a.url else read_request(a.request)
    os.makedirs(a.out, exist_ok=True)
    status = {"nonce": req.get("nonce"), "url": req["url"],
              "started_at": datetime.datetime.utcnow().isoformat() + "Z"}
    code = 0
    try:
        rd = process(req, a.out)
        status.update(status="ok", result_dir=rd)
    except Exception as e:  # noqa
        traceback.print_exc()
        status.update(status="error", error=f"{type(e).__name__}: {e}"[-4000:])
        code = 1
    status["finished_at"] = datetime.datetime.utcnow().isoformat() + "Z"
    with open(os.path.join(a.out, "LAST_RUN.json"), "w", encoding="utf-8") as f:
        json.dump(status, f, ensure_ascii=False, indent=2)
    log(json.dumps(status, ensure_ascii=False, indent=2))
    sys.exit(code)


if __name__ == "__main__":
    main()
