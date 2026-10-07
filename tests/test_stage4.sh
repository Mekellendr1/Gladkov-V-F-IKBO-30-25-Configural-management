#!/bin/bash
echo "=== Этап 4: ls, cd, rev, date ==="
python3 src/main.py --vfs-path vfs_data/deep.csv \
    --script tests/stage4_ok.script
echo "=== Этап 4: остановка на ошибке ==="
python3 src/main.py --vfs-path vfs_data/deep.csv \
    --script tests/stage4_err.script