# GENIUS
Новости приколы

## Скачать канал целиком

```bash
scripts/download_channel.sh @kupelbach
```

Качает shorts, видео и стримы с метаданными, превью и субтитрами в `downloads/<канал>/`
(папка в `.gitignore`), плюс сводку `index.csv`. Повторный запуск докачивает только новое.
Нужны `python3` и `ffmpeg`.
