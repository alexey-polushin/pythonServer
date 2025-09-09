#!/bin/bash

echo "🧹 Начинаем очистку диска..."
echo "Дата: $(date)"
echo

echo "📊 Состояние диска ДО очистки:"
df -h /
echo

echo "🐳 Очищаем Docker..."
docker system prune -a --volumes -f
echo

echo "📦 Очищаем APT кэш..."
apt clean
apt autoremove -y
echo

echo "📝 Очищаем логи (старше 1 дня)..."
journalctl --vacuum-time=1d
echo

echo "🗑️ Очищаем временные файлы..."
rm -rf /tmp/*
rm -rf /var/tmp/*
echo

echo "📊 Состояние диска ПОСЛЕ очистки:"
df -h /
echo

echo "✅ Очистка завершена!"
