#!/usr/bin/env bash
# Скачивает ВСЁ с YouTube-канала: shorts, обычные видео и стримы,
# вместе с метаданными (.info.json), превью и субтитрами.
#
# Использование:
#   scripts/download_channel.sh                 # по умолчанию @kupelbach
#   scripts/download_channel.sh @другой_канал
#
# Повторный запуск докачивает только новое (учёт в downloads/<канал>/archive.txt).
set -euo pipefail

CHANNEL="${1:-@kupelbach}"
CHANNEL="${CHANNEL#https://www.youtube.com/}"
CHANNEL="${CHANNEL%%/*}"
OUT="downloads/${CHANNEL#@}"

if ! command -v yt-dlp >/dev/null 2>&1; then
  echo "yt-dlp не найден, ставлю..." >&2
  python3 -m pip install -q -U "yt-dlp[default]"
fi
command -v ffmpeg >/dev/null 2>&1 || { echo "Нужен ffmpeg (склейка видео+аудио)" >&2; exit 1; }

mkdir -p "$OUT"

for TAB in shorts videos streams; do
  echo "=== $CHANNEL / $TAB ==="
  yt-dlp \
    "https://www.youtube.com/${CHANNEL}/${TAB}" \
    --download-archive "$OUT/archive.txt" \
    --format "bv*+ba/b" --merge-output-format mp4 \
    --output "$OUT/${TAB}/%(upload_date)s_%(id)s_%(title).80B.%(ext)s" \
    --write-info-json --write-thumbnail --convert-thumbnails jpg \
    --write-subs --write-auto-subs --sub-langs "ru.*,en.*" --sub-format "srt/best" \
    --ignore-errors --no-overwrites --retries 10 --fragment-retries 10 \
    --sleep-requests 1 --min-sleep-interval 2 --max-sleep-interval 5 \
    || echo "Вкладка $TAB: есть ошибки или вкладки нет — продолжаю" >&2
done

# Сводная таблица: дата, id, длительность, просмотры, название
python3 - "$OUT" <<'PY'
import csv, json, pathlib, sys
out = pathlib.Path(sys.argv[1])
rows = []
for f in sorted(out.rglob("*.info.json")):
    d = json.loads(f.read_text(encoding="utf-8"))
    if d.get("_type") == "playlist":
        continue
    rows.append([d.get("upload_date"), f.parent.name, d.get("id"), d.get("duration"),
                 d.get("view_count"), d.get("like_count"), d.get("title"), d.get("webpage_url")])
with open(out / "index.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["upload_date", "tab", "id", "duration_s", "views", "likes", "title", "url"])
    w.writerows(rows)
print(f"Готово: {len(rows)} роликов, список в {out/'index.csv'}")
PY
