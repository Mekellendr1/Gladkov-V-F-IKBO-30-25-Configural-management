#!/bin/bash
echo "=== Этап 5: mkdir/chown в памяти ==="
python3 src/main.py --vfs-path vfs_data/deep.csv \
    --script scripts/stage5_ok.script
echo "--- saved5.csv после chown ---"
grep -E "notes.txt|projects" vfs_data/saved5.csv
echo "--- исходный deep.csv не изменился ---"
grep -c "alice" vfs_data/deep.csv || true