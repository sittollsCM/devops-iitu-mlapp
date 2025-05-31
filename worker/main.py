import os
from fastapi import FastAPI
from datetime import datetime
import psycopg2
import pandas as pd
import xgboost as xgb
import pickle

# Параметры подключения к PostgreSQL
DB_HOST = os.getenv('POSTGRES_HOST', 'localhost')
DB_PORT = os.getenv('POSTGRES_PORT', '5432')
DB_NAME = os.getenv('POSTGRES_DB', 'weatherdb')
DB_USER = os.getenv('POSTGRES_USER', 'postgres')
DB_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'password')

app = FastAPI()

@app.post("/train")
def train():
    """
    При POST /train:
    1) Извлекаем из job_metadata первую задачу со статусом 'queued'
    2) Меняем статус на 'running', записываем время старта
    3) Считываем все записи weather_data по этой станции
    4) Обучаем XGBoostRegressor
    5) Сохраняем сериализованную модель в model_checkpoints
    6) Меняем статус задачи на 'done' с указанием end_time
    """
    # 1. Подключаемся к БД
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    cur = conn.cursor()

    # 2. Достаём первую очередь из job_metadata
    cur.execute("SELECT job_id, station FROM job_metadata WHERE status='queued' LIMIT 1;")
    job = cur.fetchone()
    if not job:
        cur.close()
        conn.close()
        return {"message": "Нет задач в статусе 'queued'"}

    job_id, station = job

    # Обновляем статус на 'running' и ставим start_time
    cur.execute(
        "UPDATE job_metadata SET status='running', start_time=%s WHERE job_id=%s;",
        (datetime.utcnow(), job_id)
    )
    conn.commit()

    # 3. Считываем данные для указанной станции
    query = """
        SELECT temperature, dew_point, humidity, precipitation, wind_direction, wind_speed
        FROM weather_data
        WHERE station = %s;
    """
    df = pd.read_sql(query, conn, params=(station,))

    # 4. Формируем X и y
    X = df[['dew_point', 'humidity', 'precipitation', 'wind_direction', 'wind_speed']]
    y = df['temperature']

    # 5. Обучаем модель XGBoostRegressor
    model = xgb.XGBRegressor(objective='reg:squarederror')
    model.fit(X, y)

    # 6. Сериализуем модель
    model_bytes = pickle.dumps(model)

    # 7. Вставляем в model_checkpoints
    cur.execute(
        "INSERT INTO model_checkpoints (station, model_bytes) VALUES (%s, %s);",
        (station, psycopg2.Binary(model_bytes))
    )

    # 8. Обновляем статус job_metadata → 'done'
    cur.execute(
        "UPDATE job_metadata SET status='done', end_time=%s WHERE job_id=%s;",
        (datetime.utcnow(), job_id)
    )
    conn.commit()

    cur.close()
    conn.close()

    return {"message": f"Модель обучена для станции {station}, job_id={job_id}"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8002)))
