Test cases & expected results

Dry‑run discovery only
Command: use --dry-run with sources /tmp/srcA /tmp/srcB
Expect: “(Dry) Would copy …” lines; no files created in /backups/daily/…

Real copy
Remove --dry-run; expect copied count equals discovered (unless equal files already exist)

Skip identical files
Run twice; second run should increase skipped count

Exclude patterns
Use --exclude link_to_sub1 and confirm paths under that are skipped

Unicode filenames
Create /tmp/srcA/naïve.log; ensure it’s copied and logged correctly

Very large file
Create a 1–2 GB file using dd; ensure copy succeeds (may take time)

Cleanup
Manually create old backup folder named like 20240101_000000 and run with --delete-old --retention-days 30; confirm deletion only for older than 30 days 


###Try a dry‑run (safe)
sudo python3 ./backup_cleanup.py --source-dirs /var/log /data/reports --backup-dir /backups/daily --extensions .txt .log .csv --retention-days 30 --dry-run --log-path /var/log/backup_cleanup.log --exclude tmp --exclude .git


###Real run (no deletion)
sudo python3 backup_cleanup.py --source-dirs /var/log /data/reports --backup-dir /backups/daily --extensions .txt .log .csv --retention-days 30 --log-path /var/log/backup_cleanup.log

###Optional cleanup of old backups
sudo python3 backup_cleanup.py --source-dirs /var/log /data/reports --backup-dir /backups/daily --extensions .txt .log .csv --retention-days 30 --delete-old --log-path /var/log/backup_cleanup.log

###Configuration Examples
sudo python3 backup_cleanup.py --source-dirs /var/log /data/reports --backup-dir /backups/daily --extensions .txt .log .csv --retention-days 14 --log-path /var/log/backup_cleanup.log --exclude tmp --exclude cache --verbose

###Sample dataset generator (for tests)
mkdir -p /tmp/srcA/sub1 /tmp/srcB/sub2 && printf "hello\n" > /tmp/srcA/sub1/a.txt && dd if=/dev/urandom of=/tmp/srcA/sub1/b.log bs=1K count=64 status=none && printf "2025-01-01,ok\n" > /tmp/srcB


### How to read the logs
tail -n 100 /var/log/backup_cleanup.log grep -i "Failed" /var/log/backup_cleanup.log
