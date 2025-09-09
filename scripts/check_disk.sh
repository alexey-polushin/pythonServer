#!/bin/bash

echo "📊 Мониторинг диска:"
echo "Дата: $(date)"
echo

echo "💾 Использование диска:"
df -h /
echo

echo "🐳 Docker:"
docker system df
echo

echo "📦 Топ директории:"
du -sh /var/* 2>/dev/null | sort -hr | head -5
echo

echo "🧠 Память:"
free -h
echo

echo "📈 Нагрузка:"
uptime
