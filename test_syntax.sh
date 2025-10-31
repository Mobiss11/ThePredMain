#!/bin/bash

echo "🔍 Проверка синтаксиса всех Python файлов..."
echo ""

errors=0

# Backend
echo "📦 Backend..."
for file in backend/app/**/*.py; do
    if [ -f "$file" ]; then
        python3 -m py_compile "$file" 2>/dev/null
        if [ $? -eq 0 ]; then
            echo "  ✓ $file"
        else
            echo "  ✗ $file"
            errors=$((errors+1))
        fi
    fi
done

# Bot
echo ""
echo "🤖 Bot..."
for file in bot/*.py bot/**/*.py; do
    if [ -f "$file" ]; then
        python3 -m py_compile "$file" 2>/dev/null
        if [ $? -eq 0 ]; then
            echo "  ✓ $file"
        else
            echo "  ✗ $file"
            errors=$((errors+1))
        fi
    fi
done

# Webapp
echo ""
echo "📱 Webapp..."
python3 -m py_compile webapp/main.py 2>/dev/null && echo "  ✓ webapp/main.py" || { echo "  ✗ webapp/main.py"; errors=$((errors+1)); }

# Admin
echo ""
echo "🔧 Admin..."
python3 -m py_compile admin/main.py 2>/dev/null && echo "  ✓ admin/main.py" || { echo "  ✗ admin/main.py"; errors=$((errors+1)); }

# Landing
echo ""
echo "🌐 Landing..."
python3 -m py_compile landing/main.py 2>/dev/null && echo "  ✓ landing/main.py" || { echo "  ✗ landing/main.py"; errors=$((errors+1)); }

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ $errors -eq 0 ]; then
    echo "✅ Все файлы проверены! Ошибок не найдено."
    echo ""
    echo "🚀 Готов к запуску:"
    echo "   make up     - запустить все сервисы"
    echo "   make logs   - посмотреть логи"
    echo "   make health - проверить здоровье"
else
    echo "❌ Найдено ошибок: $errors"
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
