from tkinter import *
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import sqlite3
import datetime
from database import PLAN_TABLE

class ResumenInsightsApp:
    def __init__(self, root, menu_root):
        self.root = root
        self.menu_root = menu_root
        self.root.title("📊 Resumen e Insights del Mantenimiento")

        ttk.Label(root, text="Selecciona una base de datos:", font=("Arial", 11, "bold")).pack(pady=10)
        ttk.Button(root, text="🗂 Cargar Base de Datos", command=self.cargar_bd).pack(pady=5)
        ttk.Button(root, text="⬅ Volver al menú", command=self.volver).pack(pady=10)

        self.frame_info = None

    def volver(self):
        self.root.destroy()
        self.menu_root.deiconify()

    def cargar_bd(self):
        path = filedialog.askopenfilename(title="Selecciona una BD", filetypes=[("SQLite DB", "*.db")])
        if not path:
            return
        try:
            conn = sqlite3.connect(path)
            df = pd.read_sql_query(f"SELECT * FROM {PLAN_TABLE}", conn)
            conn.close()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo leer la base de datos:\n{e}")
            return

        if df.empty:
            messagebox.showwarning("Aviso", "La base de datos está vacía.")
            return

        self.mostrar_insights(df)

    def mostrar_insights(self, df):
        if self.frame_info:
            self.frame_info.destroy()

        self.frame_info = ttk.Frame(self.root)
        self.frame_info.pack(padx=10, pady=10, fill="both", expand=True)

        df["fecha_tentativa"] = pd.to_datetime(df["fecha_tentativa"], errors="coerce", dayfirst=True)
        hoy = pd.Timestamp.today()

        total = len(df)
        cumplidos = df["cumplido"].sum()
        pendientes = total - cumplidos
        porc = (cumplidos / total * 100) if total > 0 else 0

        atrasados = df[(df["cumplido"] == 0) & (df["fecha_tentativa"] < hoy)]
        proximos = df[
            (df["cumplido"] == 0)
            & (df["fecha_tentativa"].dt.month == hoy.month)
            & (df["fecha_tentativa"].dt.year == hoy.year)
        ]

        resumen = (
            f"🧾 Total de equipos: {total}\n"
            f"✅ Cumplidos: {cumplidos}\n"
            f"⏳ Pendientes: {pendientes}\n"
            f"📈 Porcentaje de cumplimiento: {porc:.1f}%\n\n"
            f"⚠️ Atrasados: {len(atrasados)}\n"
            f"🗓 Próximos este mes: {len(proximos)}"
        )

        ttk.Label(self.frame_info, text="Resumen General", font=("Arial", 12, "bold")).pack(pady=8)
        text = Text(self.frame_info, height=8, wrap="word", bg="#f4f6f8", font=("Arial", 10))
        text.insert("1.0", resumen)
        text.configure(state="disabled")
        text.pack(fill="x", padx=5, pady=5)

        btn_frame = ttk.Frame(self.frame_info)
        btn_frame.pack(pady=8)
        ttk.Button(btn_frame, text="Ver Atrasados", command=lambda: self.mostrar_lista(atrasados, "Equipos Atrasados")).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Ver Próximos", command=lambda: self.mostrar_lista(proximos, "Equipos Próximos")).pack(side="left", padx=5)

    def mostrar_lista(self, df_sub, titulo):
        if df_sub.empty:
            messagebox.showinfo(titulo, "No hay equipos en esta categoría.")
            return
        v = Toplevel(self.root)
        v.title(titulo)
        cols = ["equipo", "marca", "modelo", "codigo", "ubicacion", "fecha_tentativa"]
        tree = ttk.Treeview(v, columns=cols, show="headings")
        for c in cols:
            tree.heading(c, text=c.capitalize())
            tree.column(c, width=140, anchor="w")
        tree.pack(fill="both", expand=True)
        for _, row in df_sub.iterrows():
            tree.insert("", END, values=[row[c] for c in cols])
