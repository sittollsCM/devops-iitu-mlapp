-- 1) Таблица с почасовыми метеоданными
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

-- 2) Задачи для Data-Splitter / Worker
CREATE TABLE IF NOT EXISTS job_metadata (
    job_id SERIAL PRIMARY KEY,
    station VARCHAR(10) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'queued',
    start_time TIMESTAMP,
    end_time TIMESTAMP
);

-- 3) Сохранение чекпойнтов (каждый Worker сохраняет свою модель)
CREATE TABLE IF NOT EXISTS model_checkpoints (
    station VARCHAR(10) NOT NULL,
    model_bytes BYTEA,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4) Финальная агрегированная модель (pickle со списком моделей)
CREATE TABLE IF NOT EXISTS final_models (
    id SERIAL PRIMARY KEY,
    model_bytes BYTEA,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
