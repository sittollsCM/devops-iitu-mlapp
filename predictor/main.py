import os
from fastapi import FastAPI
from pydantic import BaseModel
import psycopg2
import pickle
import numpy as np

# Параметры подключения к PostgreSQL
DB_HOST = os.getenv('POSTGRES_HOST', 'localhost')
DB_PORT = os.getenv('POSTGRES_PORT', '5432')
DB_NAME = os.getenv('POSTGRES_DB', 'weatherdb')
DB_USER = os.getenv('POSTGRES_USER', 'postgres')
DB_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'password')

# Pydantic-модель для входящего запроса
class PredictRequest(BaseModel):
    dew_point: float
    humidity: float
    precipitation: float
    wind_direction: float
    wind_speed: float

app = FastAPI()
models = []  # сюда загрузим список моделей при старте

def load_models():
    """
    Считывает из final_models последнюю запись model_bytes (pickle-список моделей),
    десериализует и возвращает Python-список моделей XGBRegressor.
    """
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    cur = conn.cursor()
    cur.execute("SELECT model_bytes FROM final_models ORDER BY created_at DESC LIMIT 1;")
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        return []
    models_list = pickle.loads(row[0])
    return models_list

@app.on_event("startup")
def on_startup():
    global models
    models = load_models()

@app.post("/predict")
def predict(req: PredictRequest):
    """
    Принимает JSON вида {dew_point, humidity, precipitation, wind_direction, wind_speed}.
    Возвращает усреднённый прогноз температуры по списку моделей.
    """
    if not models:
        return {"error": "Модели не найдены. Сначала выполните /aggregate"}

    X = np.array([[req.dew_point, req.humidity, req.precipitation, req.wind_direction, req.wind_speed]])
    preds = [m.predict(X)[0] for m in models]
    avg_pred = float(np.mean(preds))
    return {"temperature": avg_pred}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8004)))
