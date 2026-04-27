# Звіт до лабораторної роботи №3

## 1. Загальні відомості

Тема: обробка погодних даних, нормалізація схеми БД та міграція між СУБД.

Виконав: `Студент 3 курсу Бурдюг Семен`  
Група: `КМ-33`

---

## 2. Мета роботи

Розробити ETL-процес для набору погодних даних із CSV з подальшою:

1. загрузкою сирих даних у PostgreSQL;
2. нормалізацією структури через Liquibase;
3. обчисленням бізнес-ознаки `should_go_outside`;
4. міграцією фінальних таблиць у MySQL;
5. реалізацією інструментів запиту даних.

---

## 3. Постановка завдання

Потрібно було реалізувати систему, яка:

1. імпортує `GlobalWeatherRepository.csv` у таблицю `weather_raw`;
2. розділяє сиру таблицю на:
   - `weather_record` (метеопараметри);
   - `astronomy_info` (астрономічні параметри);
3. обчислює поле `should_go_outside`;
4. видаляє проміжну таблицю `weather_raw`;
5. переносить фінальні дані з PostgreSQL у MySQL;
6. надає CLI-інтерфейс для фільтрації записів.

У моделі використано обов'язкові типи даних:

- `country` — TEXT  
- `wind_degree` — INT  
- `wind_kph` — FLOAT  
- `wind_direction` — ENUM  
- `last_updated` — DATE  
- `sunrise` — TIME  

Основна категорія згідно варіанту — астрономічні дані (схід/захід небесних тіл), які винесені в окрему таблицю.

---

## 4. Використані засоби

- Мова програмування: Python 3.13  
- ORM/SQL-інструменти: SQLAlchemy 2.x  
- Драйвери:
  - `psycopg[binary]` (PostgreSQL)
  - `PyMySQL` (MySQL)
  - `cryptography`
- Міграції БД: Liquibase  
- СУБД:
  - PostgreSQL
  - MySQL  

---

## 5. Структура проєкту

- `import_weather_raw.py` — імпорт CSV у `weather_raw`
- `run_changes.py` — запуск міграцій
- `migrate_stage3_to_mysql.py` — перенесення у MySQL
- `main.py` — запуск і CLI
- `query_weather.py` — запити
- `models.py` — ORM-моделі
- `db.py` — конфігурація БД
- `clean_db.py` / `clean_mysql.py` — очищення
- `liquibase/changelog/changes/*.sql` — міграції

---

## 6. Опис виконання роботи

### 6.1. Налаштування середовища

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

### 6.2. Імпорт сирих даних

```powershell
python import_weather_raw.py --csv GlobalWeatherRepository.csv --batch-size 5000
```

---

### 6.3. Нормалізація структури (Liquibase)

```powershell
python run_changes.py
```

Перед видаленням всі дані були перенесені у нормалізовані таблиці, втрати даних не відбулося.

Міграції дозволяють створити БД з нуля і мігрувати існуючу.

---

### 6.4. Логіка обчислення `should_go_outside`

Комбінує астрономічні та погодні параметри.

---

### 6.5. Міграція у MySQL

```powershell
python migrate_stage3_to_mysql.py --batch-size 5000
```

---

### 6.6. Запити

```powershell
python main.py
```

---

## 7. Отримані результати

- ETL реалізовано  
- нормалізація виконана  
- міграція працює  

---

