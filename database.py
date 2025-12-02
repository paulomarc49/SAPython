# Este módulo se encarga de gestionar la base de datos SQLite usada por todo el sistema Saphyton.

import sqlite3
import os

PLAN_TABLE = "plan_mantenimiento"                                                                   # Contiene el nombre de la tabla principal del sistema.
ULT_MANT = "ultimo_mantenimiento"
FREC = "frecuencia_meses"


TARGET_COLUMNS = {                                                                                  #
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",                                                      #
    "equipo": "TEXT",                                                                               #
    "marca": "TEXT",                                                                                #
    "modelo": "TEXT",                                                                               #
    "codigo": "TEXT",                                                                               #
    "ubicacion": "TEXT",                                                                            #
    "responsable": "TEXT",          
    "fecha_tentativa": "TEXT",                                                                      #
    "cumplido": "INTEGER DEFAULT 0",                                                                #
    "fecha_cumplimiento": "TEXT",                                                                   #
    "ultimo_mantenimiento": "TEXT",                                                                 #
    "frecuencia_meses": "INTEGER"                                                                   #
}

def ensure_table(db_path: str):                                                                     # Defino la función: ensure_table, que toma como argumento: db_path 
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)                           # Asegura  que exista carpeta para guardar la base de datos. Si no existe, la crea automáticamente.
    conn = sqlite3.connect(db_path)                                                                 # Me conecto a la base de datos mediante el path: db_path
    cur = conn.cursor()                                                                             # Función de sqlite3 que permite ejecutar comandos SQL.
    cur.execute(f"CREATE TABLE IF NOT EXISTS {PLAN_TABLE} (id INTEGER PRIMARY KEY AUTOINCREMENT)")  # Creo la tabla PLAN_TABLE = "plan_mantenimiento"
    cur.execute(f"PRAGMA table_info({PLAN_TABLE})")                                                 # Devuelve una lista con los nombres y tipos de las columnas actuales
    existing = {row[1] for row in cur.fetchall()}                                                   # Lista de columnas que ya existen en la base de datos. 
    for col, decl in TARGET_COLUMNS.items():                                                        # Extra col de TARGET_COLUMNS para realizar comparación
        if col not in existing:                                                                     # Compara col en existing
            cur.execute(f"ALTER TABLE {PLAN_TABLE} ADD COLUMN {col} {decl}")                        # Si alguna columna no está en la tabla, la agrega automáticamente
    conn.commit()                                                                                   # Función de sqlite3
    conn.close()                                                                                    # Cerrar la base de datos
