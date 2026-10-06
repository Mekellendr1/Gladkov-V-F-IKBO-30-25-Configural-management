#!/bin/bash
echo "=== Тест: файл не найден ==="
python3 src/main.py --vfs-path vfs_data/nope.csv

echo "=== Тест: неверный формат ==="
python3 src/main.py --vfs-path vfs_data/broken.csv

echo "=== Тест: остановка скрипта на ошибке ==="
python3 src/main.py --vfs-path vfs_data/multi.csv --script scripts/stage3_error.script