import os
from fastapi import FastAPI
import psycopg2
import pickle

# Параметры подключения к PostgreSQL
DB_HOST = os.getenv('POSTGRES_HOST', 'localhost')
DB_PORT = os.getenv('POSTGRES_PORT', '5432')
DB_NAME = os.getenv('POSTGRES_DB', 'weatherdb')
DB_USER = os.getenv('POSTGRES_USER', 'postgres')
DB_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'password')

app = FastAPI()

@app.post("/aggregate")
def aggregate():
    """
    При POST /aggregate:
    1) Считываем из model_checkpoints все model_bytes
    2) Десериализуем каждый pickle → список моделей
    3) Сериализуем весь список models заново и сохраняем в final_models
    """
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    cur = conn.cursor()

    # 1) Получаем все бинарные дампы из model_checkpoints
    cur.execute("SELECT model_bytes FROM model_checkpoints;")
    rows = cur.fetchall()
    if not rows:
        cur.close()
        conn.close()
        return {"message": "В model_checkpoints нет ни одной модели"}

    # 2) Десериализуем каждый дамп
    models = [pickle.loads(row[0]) for row in rows]

    # 3) Сериализуем полный список моделей
    ensemble_bytes = pickle.dumps(models)

    # 4) Сохраняем в final_models
    cur.execute(
        "INSERT INTO final_models (model_bytes) VALUES (%s);",
        (psycopg2.Binary(ensemble_bytes),)
    )
    conn.commit()

    cur.close()
    conn.close()
    return {"message": f"Собрано {len(models)} моделей, сохранено в final_models."}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8003)))
