


###Try a dry‑run (safe)
python3 backup_cleanup.py \
  --source-dirs /var/log /data/reports \
  --backup-dir /backups/daily \
  --extensions .txt .log .csv \
  --retention-days 30 \
  --dry-run \
  --log-path /var/log/backup_cleanup.log \
  --exclude tmp --exclude .git
``


python3 ./backup_cleanup.py --source-dirs /var/log /data/reports --backup-dir /backups/daily --extensions .txt .log .csv --retention-days 30 --dry-run --log-path /var/log/backup_cleanup.log --exclude tmp --exclude .git
