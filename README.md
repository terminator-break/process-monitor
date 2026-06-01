[README (1).md](https://github.com/user-attachments/files/28466453/README.1.md)
# ⬡ Process Monitor

> Менеджер процессов Windows с тёмным GUI на Python — удобная альтернатива диспетчеру задач.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=flat-square&logo=python)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey?style=flat-square&logo=windows)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

---

## ✨ Возможности

- 📊 Мониторинг всех процессов в реальном времени (CPU, RAM, статус, потоки, пользователь)
- ⛔ Завершение процессов одной кнопкой или клавишей `Delete`
- ⏸ Приостановка и возобновление процессов
- 🔍 Поиск процесса по имени или PID
- 🔃 Сортировка по любому столбцу
- 🖱 Двойной клик — детальная информация о процессе (путь, время запуска и др.)
- ⚡ Авто-обновление каждые 2 секунды (можно отключить)
- 🎨 Тёмный интерфейс с цветовой индикацией нагрузки

---

## 🖥 Требования

- Windows 7 / 10 / 11
- Python 3.8 или новее
- Библиотека `psutil`

---

## 🚀 Установка и запуск

### 1. Установи Python

Скачай с официального сайта: [python.org/downloads](https://www.python.org/downloads/)

> ⚠️ При установке поставь галочку **"Add Python to PATH"**

### 2. Скачай проект

```bash
git clone https://github.com/terminator-break/process-monitor.git
cd process-monitor
```

Или просто скачай ZIP: **Code → Download ZIP** и распакуй.

### 3. Установи зависимости

```bash
pip install psutil
```

### 4. Запусти программу

```bash
python process_monitor.py
```

> 🔐 Для завершения системных процессов запускай от имени администратора:
> правой кнопкой на `process_monitor.py` → **Запустить от имени администратора**

---

## ⌨️ Горячие клавиши

| Клавиша | Действие |
|---------|----------|
| `Delete` | Завершить выбранный процесс |
| `Double Click` | Открыть детали процесса |

---

## 📁 Структура проекта

```
process-monitor/
└── process_monitor.py   # Основной файл программы
└── README.md            # Документация
```

---

## 📄 Лицензия

MIT © [terminator-break](https://github.com/terminator-break)
