


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


dev@al-ThinkPad:~/Desktop/python test folder$ python3 backup_cleanup.py
--source-dirs /var/log /data/reports
--backup-dir /backups/daily
--extensions .txt .log .csv
--retention-days 30
--dry-run
--log-path /var/log/backup_cleanup.log
--exclude tmp --exclude .git
usage: backup_cleanup.py [-h] --source-dirs SOURCE_DIRS [SOURCE_DIRS ...]
                         --backup-dir BACKUP_DIR --extensions EXTENSIONS
                         [EXTENSIONS ...] [--retention-days RETENTION_DAYS]
                         [--dry-run] [--delete-old] [--exclude [EXCLUDE ...]]
                         [--log-path LOG_PATH] [--verbose]
backup_cleanup.py: error: the following arguments are required: --source-dirs, --backup-dir, --extensions
--source-dirs: command not found
--backup-dir: command not found
--extensions: command not found
--retention-days: command not found
--dry-run: command not found
--log-path: command not found
--exclude: command not found
