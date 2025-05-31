import os
from fastapi import FastAPI
import psycopg2
from datetime import datetime

# Параметры подключения к PostgreSQL
DB_HOST = os.getenv('POSTGRES_HOST', 'localhost')
DB_PORT = os.getenv('POSTGRES_PORT', '5432')
DB_NAME = os.getenv('POSTGRES_DB', 'weatherdb')
DB_USER = os.getenv('POSTGRES_USER', 'postgres')
DB_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'password')

app = FastAPI()

@app.post("/split")
def split():
    """
    При POST /split:
    1) Получаем список DISTINCT(station) из таблицы weather_data
    2) Для каждой станции создаём запись в job_metadata со статусом 'queued'
    """
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    cur = conn.cursor()

    # Получаем все уникальные станции
    cur.execute("SELECT DISTINCT station FROM weather_data;")
    stations = [row[0] for row in cur.fetchall()]

    # Вставляем каждую станцию в job_metadata
    for station in stations:
        cur.execute(
            "INSERT INTO job_metadata (station, status) VALUES (%s, 'queued');",
            (station,)
        )
    conn.commit()
    cur.close()
    conn.close()

    return {"message": f"Созданы задачи для станций: {stations}"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8001)))
