from tkinter import *
from tkinter import ttk, filedialog, messagebox, Checkbutton, IntVar
import datetime
import sqlite3
import os
from database import ensure_table, PLAN_TABLE


class CumplimientoApp:
    def __init__(self, root, menu_root):
        self.root = root
        self.menu_root = menu_root
        self.root.title("Cumplimiento de Mantenimiento")
        self.root.geometry("900x600")

        # Título
        ttk.Label(root, text="Cumplimiento de Mantenimiento", font=("Arial", 12, "bold")).pack(pady=10)

        # Contenedor superior con botones
        top = ttk.Frame(root)
        top.pack(fill="x", padx=8)
        self.plan_db = None
        self.lbl = ttk.Label(top, text="BD: (no seleccionada)")
        self.lbl.pack(side="left", padx=4)
        ttk.Button(top, text="🗂 Seleccionar BD", command=self.sel_bd).pack(side="right", padx=4)

        # Contenedor principal con scrollbar
        cont = ttk.Frame(root)
        cont.pack(fill="both", expand=True, padx=8, pady=8)
        self.canvas = Canvas(cont, highlightthickness=0)
        self.scroll = ttk.Scrollbar(cont, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scroll.set)
        self.scroll.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.inner = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.inner.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        # Pie de ventana
        bottom = ttk.Frame(root)
        bottom.pack(fill="x", padx=8, pady=6)
        ttk.Button(bottom, text="💾 Guardar Cambios", command=self.guardar).pack(side="left", padx=4)
        ttk.Button(bottom, text="⬅ Volver", command=self.volver).pack(side="right", padx=4)

        self.check_vars = {}
        self.registros = []

    # ---------------- Navegación ----------------
    def volver(self):
        self.root.destroy()
        self.menu_root.deiconify()

    # ---------------- Seleccionar BD ----------------
    def sel_bd(self):
        path = filedialog.askopenfilename(
            title="Selecciona la base de datos",
            filetypes=[("SQLite DB", "*.db")]
        )
        if not path:
            return

        self.plan_db = path
        self.lbl.config(text=os.path.basename(path))
        ensure_table(self.plan_db)

        conn = sqlite3.connect(self.plan_db)
        cur = conn.cursor()
        cur.execute(f"""
            SELECT id, equipo, marca, modelo, codigo, ubicacion, fecha_tentativa, cumplido, fecha_cumplimiento 
            FROM {PLAN_TABLE}
        """)
        self.registros = cur.fetchall()
        conn.close()
        self.mostrar()

    # ---------------- Mostrar registros ----------------
    def mostrar(self):
        for w in self.inner.winfo_children():
            w.destroy()

        self.check_vars.clear()
        ttk.Label(
            self.inner,
            text="Marque los equipos que ya fueron mantenidos (los cambios se guardan en la misma base de datos):",
            font=("Arial", 10, "bold")
        ).pack(anchor="w", pady=4)

        for r in self.registros:
            _id, eq, ma, mo, co, ub, ft, cu, fc = r
            txt = f"[{_id}] {eq} | {ma} | {mo} | {co} | {ub} | Prog: {ft} | Cumplido: {'Sí' if cu else 'No'}"
            v = IntVar(value=1 if cu else 0)
            Checkbutton(self.inner, text=txt, variable=v).pack(anchor="w", padx=8, pady=2)
            self.check_vars[_id] = v

    # ---------------- Guardar ----------------
    def guardar(self):
        if not self.plan_db:
            messagebox.showwarning("Atención", "Primero selecciona una base de datos.")
            return

        hoy = datetime.date.today().strftime("%d/%m/%Y")
        conn = sqlite3.connect(self.plan_db)
        cur = conn.cursor()
        actualizados = 0

        for _id, var in self.check_vars.items():
            if var.get() == 1:
                cur.execute(f"""
                    UPDATE {PLAN_TABLE}
                    SET cumplido = 1, fecha_cumplimiento = ?
                    WHERE id = ?
                """, (hoy, _id))
            else:
                cur.execute(f"""
                    UPDATE {PLAN_TABLE}
                    SET cumplido = 0, fecha_cumplimiento = NULL
                    WHERE id = ?
                """, (_id,))
            actualizados += cur.rowcount

        conn.commit()
        conn.close()

        messagebox.showinfo("Éxito", f"Se actualizaron {actualizados} registros en:\n{self.plan_db}")
