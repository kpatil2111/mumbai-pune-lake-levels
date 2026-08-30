# Lake levels cron sync

Run `sync-lake-levels.sh` from cron to fetch the latest MWRD report and upsert it into the PostgreSQL database.

Example: sync every day at 10:00 AM IST.

```cron
0 10 * * * /home/kartikp-home-ubuntu/workspace/lake-levels/sync-lake-levels.sh
```

Logs are written to:

```text
/home/kartikp-home-ubuntu/workspace/lake-levels/sync.log
```

The script uses a lock file at `/tmp/lake-levels-sync.lock`, so overlapping cron runs exit safely.
