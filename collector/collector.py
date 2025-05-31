import os
from datetime import datetime
import psycopg2
import pandas as pd
from meteostat import Stations, Hourly

# Параметры подключения к БД (можно переопределить через переменные окружения)
DB_HOST = os.getenv('POSTGRES_HOST', 'localhost')
DB_PORT = os.getenv('POSTGRES_PORT', '5432')
DB_NAME = os.getenv('POSTGRES_DB', 'weatherdb')
DB_USER = os.getenv('POSTGRES_USER', 'postgres')
DB_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'password')

def main():
    # 1. Подключаемся к PostgreSQL
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    cur = conn.cursor()

    # 2. Создаём таблицу weather_data, если её нет
    cur.execute("""
    CREATE TABLE IF NOT EXISTS weather_data (
        station VARCHAR(10),
        ts TIMESTAMP,
        temperature FLOAT,
        dew_point FLOAT,
        humidity FLOAT,
        precipitation FLOAT,
        wind_direction FLOAT,
        wind_speed FLOAT
    );
    """)
    conn.commit()

    # 3. Находим три ближайшие станции к Алматы (координаты примерно 43.2220N, 76.8512E)
    stations = Stations()
    stations = stations.nearby(43.2220, 76.8512)
    stations = stations.fetch(3)
    station_ids = stations.index.tolist()
    print("Найденные станции:", station_ids)

    # 4. Определяем период для выборки: 2000-01-01 по 2024-12-31
    start = datetime(2000, 1, 1)
    end = datetime(2024, 12, 31)

    # 5. Для каждой станции скачиваем почасовые данные и вставляем в БД
    for station_id in station_ids:
        print(f"Скачиваем данные для станции {station_id}...")
        data = Hourly(station_id, start, end)
        data = data.fetch()
        # Оставим только нужные столбцы
        data = data[['temp', 'dwpt', 'rhum', 'prcp', 'wdir', 'wspd']]
        # Уберём строки, где нет температуры (поле temp)
        data = data.dropna(subset=['temp'])
        # Итеративно вставляем
        for ts, row in data.iterrows():
            cur.execute("""
            INSERT INTO weather_data 
                (station, ts, temperature, dew_point, humidity, precipitation, wind_direction, wind_speed)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING;
            """, (
                station_id,
                ts.to_pydatetime(),
                row['temp'],
                row['dwpt'],
                row['rhum'],
                row['prcp'],
                row['wdir'],
                row['wspd']
            ))
        conn.commit()
        print(f"Данные для {station_id} сохранены в БД.")

    # 6. Закрываем соединение
    cur.close()
    conn.close()
    print("Загрузка данных завершена.")

if __name__ == '__main__':
    main()
