# Perplexity API Response

## Prompt
Can you write me a bash script to back up the below directories to a remote rsync server on 192.168.1.43:
- Local: /raid10/  remote: /server_backup
- Local: /oldhome/ remote: /oldhome_backup
Can you also apply compression on the backup side and the data transmisison to increase back up performance.

Could you also provide a script to also to run a restore from the remote back up to the local source system.```

## Response
```To back up the specified directories to a remote rsync server at 192.168.1.43 with compression during transmission and on the backup side, use the following Bash scripts. **rsync's `-z` option compresses data during transfer**, but it does not compress files at rest on the destination; for destination-side compression, you must archive and compress after transfer (e.g., with `tar` and `gzip`)[1][2][4][5].

---

**Backup Script (`backup.sh`):**

```bash
#!/bin/bash
# Backup /raid10/ and /oldhome/ to remote rsync server with compression in transit

REMOTE_HOST="192.168.1.43"
REMOTE_USER="your_remote_user"   # Replace with actual remote user
RSYNC_OPTS="-aHz --delete --progress"  # Archive, preserve hard links, compress in transit, delete removed files

# Backup /raid10/ to /server_backup
rsync $RSYNC_OPTS /raid10/ ${REMOTE_USER}@${REMOTE_HOST}:/server_backup

# Backup /oldhome/ to /oldhome_backup
rsync $RSYNC_OPTS /oldhome/ ${REMOTE_USER}@${REMOTE_HOST}:/oldhome_backup

# Optional: SSH to remote and compress backup directories after transfer
ssh ${REMOTE_USER}@${REMOTE_HOST} "tar -czf /server_backup_$(date +%F).tar.gz -C / server_backup && tar -czf /oldhome_backup_$(date +%F).tar.gz -C / oldhome_backup"
```
- **`-aHz`**: Archive mode, preserve hard links, compress data during transfer[2][4].
- **`--delete`**: Remove files on backup side that no longer exist locally[1].
- **`--progress`**: Show progress.

**Note:** Replace `your_remote_user` with your actual remote username. The SSH command at the end compresses the backup directories on the remote server after transfer using `tar` and `gzip`[5].

---

**Restore Script (`restore.sh`):**

```bash
#!/bin/bash
# Restore /server_backup and /oldhome_backup from remote rsync server with compression in transit

REMOTE_HOST="192.168.1.43"
REMOTE_USER="your_remote_user"
RSYNC_OPTS="-aHz --progress"

# Restore /server_backup to /raid10/
rsync $RSYNC_OPTS ${REMOTE_USER}@${REMOTE_HOST}:/server_backup/ /raid10/

# Restore /oldhome_backup to /oldhome/
rsync $RSYNC_OPTS ${REMOTE_USER}@${REMOTE_HOST}:/oldhome_backup/ /oldhome/
```
- This script restores the directories from the remote server to their original locations, again using compression in transit[2][4].

---

**Key Points:**
- **Compression during transfer** is handled by rsync's `-z` option[2][4].
- **Compression at rest** (on the backup side) requires an additional step, such as archiving with `tar -czf` after the rsync completes[5].
- **Authentication**: SSH keys are recommended for passwordless automation.
- **Permissions**: Ensure the remote user has write permission to the backup directories.

If you need true incremental backups or deduplication, consider using tools like Borg or restic, as rsync does not provide these features[1].

Let me know if you need the scripts tailored for rsync daemon mode or with more advanced backup rotation.```

## Citations
- https://jstaf.github.io/posts/backups-with-borg-rsync/
- https://www.system-rescue.org/manual/Backup_and_transfer_your_data_using_rsync/
- https://opensource.com/article/17/1/rsync-backup-linux
- https://www.nexcess.net/help/using-rsync-for-backups/
- https://bbs.archlinux.org/viewtopic.php?id=212113

