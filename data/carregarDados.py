import pandas as pd
from sqlalchemy import create_engine, text
import os
import sys

def verificar_csv():
    csv_paths = [
        "docs/IOT-temp.csv",
        "IOT-temp.csv",
        "data/IOT-temp.csv"
    ]
    for path in csv_paths:
        if os.path.exists(path):
            return path
    print("❌ Arquivo CSV não encontrado! Coloque o IOT-temp.csv em uma destas pastas: docs/, data/ ou raiz.")
    return None

def conectar_banco():
    try:
        engine = create_engine('postgresql://postgres:senha123@localhost:5432/iotdb')
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return engine
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
        return None

def carregar_csv(csv_path):
    try:
        df = pd.read_csv(csv_path, sep=",")
        if 'noted_date' in df.columns:
            try:
                df['noted_date'] = pd.to_datetime(df['noted_date'], dayfirst=True)
            except:
                df['noted_date'] = pd.to_datetime(df['noted_date'])
        return df
    except Exception as e:
        print(f"❌ Erro ao carregar CSV: {e}")
        return None

def criar_tabela_e_views(engine, df):
    try:
        with engine.begin() as conn:
            conn.execute(text("DROP VIEW IF EXISTS avg_temp_por_dispositivo CASCADE;"))
            conn.execute(text("DROP VIEW IF EXISTS leituras_por_hora CASCADE;"))
            conn.execute(text("DROP VIEW IF EXISTS temp_max_min_por_dia CASCADE;"))
        df.to_sql("iot_temperaturas", engine, if_exists="replace", index=False)
        with engine.begin() as conn:
            conn.execute(text("""
                CREATE OR REPLACE VIEW avg_temp_por_dispositivo AS
                SELECT id AS device_id, ROUND(AVG(temp), 2) AS avg_temp, COUNT(*) AS total_leituras
                FROM iot_temperaturas
                GROUP BY id
                ORDER BY avg_temp DESC;
            """))
            conn.execute(text("""
                CREATE OR REPLACE VIEW leituras_por_hora AS
                SELECT EXTRACT(HOUR FROM noted_date) AS hora, COUNT(*) AS contagem
                FROM iot_temperaturas
                GROUP BY hora
                ORDER BY hora;
            """))
            conn.execute(text("""
                CREATE OR REPLACE VIEW temp_max_min_por_dia AS
                SELECT DATE(noted_date) AS data, ROUND(MAX(temp), 2) AS temp_max, 
                       ROUND(MIN(temp), 2) AS temp_min, COUNT(*) AS leituras_dia
                FROM iot_temperaturas
                GROUP BY DATE(noted_date)
                ORDER BY data;
            """))
        return True
    except:
        return False

def validar_views(engine):
    try:
        views = ['avg_temp_por_dispositivo', 'leituras_por_hora', 'temp_max_min_por_dia']
        for view in views:
            df = pd.read_sql(f"SELECT COUNT(*) as total FROM {view}", engine)
        return True
    except:
        return False

def main():
    csv_path = verificar_csv()
    if not csv_path:
        sys.exit(1)
    engine = conectar_banco()
    if not engine:
        sys.exit(1)
    df = carregar_csv(csv_path)
    if df is None:
        sys.exit(1)
    if not criar_tabela_e_views(engine, df):
        print("❌ Erro ao criar tabela/views")
        sys.exit(1)
    if not validar_views(engine):
        print("❌ Erro na validação das views")
        sys.exit(1)
    print("✅ Dados carregados e views criadas com sucesso!")

if __name__ == "__main__":
    main()
