#!/usr/bin/env bash
# Gửi một link TikTok cho GitHub Actions xử lý rồi chờ kết quả.
#   bash tiktok/submit.sh "<link tiktok>" [lang] [model]
# lang: vi | en | ... (để trống = tự nhận). model: large-v3-turbo (mặc định) | small | medium ...
set -euo pipefail
URL="${1:?Cần link TikTok}"; LANG_IN="${2:-}"; MODEL="${3:-}"
TIMEOUT_MIN="${TIMEOUT_MIN:-45}"
cd "$(git rev-parse --show-toplevel)"
BRANCH="$(git rev-parse --abbrev-ref HEAD)"
NONCE="$(date -u +%Y%m%dT%H%M%SZ)-$RANDOM"

{ echo "url=$URL"; echo "nonce=$NONCE"; [ -n "$LANG_IN" ] && echo "lang=$LANG_IN"; [ -n "$MODEL" ] && echo "model=$MODEL"; } > tiktok/request.txt
git add tiktok/request.txt
git commit -q -m "TikTok: yêu cầu phân tích $NONCE"
for i in 1 2 3 4; do git push -q -u origin "$BRANCH" && break; sleep $((2**i)); done
echo "Đã gửi (nonce=$NONCE). Đang chờ GitHub Actions xử lý..."

deadline=$(( $(date +%s) + TIMEOUT_MIN*60 ))
while [ "$(date +%s)" -lt "$deadline" ]; do
  sleep 30
  git fetch -q origin "$BRANCH" || continue
  st="$(git show FETCH_HEAD:tiktok/results/LAST_RUN.json 2>/dev/null || true)"
  if echo "$st" | grep -q "\"nonce\": \"$NONCE\""; then
    git merge -q --no-edit FETCH_HEAD
    echo "$st"
    if echo "$st" | grep -q '"status": "ok"'; then
      dir="$(python3 -c 'import json;print(json.load(open("tiktok/results/LAST_RUN.json"))["result_dir"])')"
      echo "XONG -> $dir/REPORT.md"; exit 0
    fi
    echo "LỖI khi xử lý (xem error ở trên)"; exit 2
  fi
done
echo "Hết thời gian chờ ${TIMEOUT_MIN} phút"; exit 3
