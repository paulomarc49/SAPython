from tkinter import *
from tkinter import ttk, filedialog, messagebox
import datetime
import sqlite3
import os
from database import ensure_table, PLAN_TABLE


class CumplimientoApp:
    def __init__(self, root, menu_root):
        # root aquí debe ser SIEMPRE un Toplevel
        self.root = root
        self.menu_root = menu_root

        self.root.title("Cumplimiento de Mantenimiento")
        self.root.geometry("900x600")

        # 👈 importantísimo: cuando cierras con la X, se llama a volver()
        self.root.protocol("WM_DELETE_WINDOW", self.volver)

        # ===== Fondo global =====
        BG_COLOR = "#F0F3F4"
        self.root.configure(bg=BG_COLOR)

        # ===== Estilos =====
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("TFrame", background=BG_COLOR)
        style.configure("TLabel", background=BG_COLOR)
        style.configure(
            "Titulo.TLabel",
            font=("Arial", 15, "bold"),
            background=BG_COLOR
        )

        style.configure(
            "GreenButton.TButton",
            font=("Arial", 12),
            foreground="white",
            background="#4CAF50",
            padding=8
        )
        style.map(
            "GreenButton.TButton",
            background=[("active", "#66BB6A")],
            foreground=[("active", "white")]
        )

        # ===== Título =====
        ttk.Label(
            self.root,
            text="Cumplimiento de Mantenimiento",
            style="Titulo.TLabel",
            anchor="center"
        ).pack(pady=10, fill="x")

        # ===== Frame superior =====
        top = ttk.Frame(self.root)
        top.pack(fill="x", padx=10, pady=5)

        self.lbl = ttk.Label(top, text="BD: (no seleccionada)", font=("Arial", 10))
        self.lbl.pack(side="left", padx=6)

        ttk.Button(
            top,
            text="🗂 Seleccionar BD",
            command=self.sel_bd,
            style="GreenButton.TButton"
        ).pack(side="right", padx=6)

        # ===== Contenedor con scroll =====
        cont = ttk.Frame(self.root)
        cont.pack(fill="both", expand=True, padx=10, pady=10)

        self.canvas = Canvas(cont, bg=BG_COLOR, highlightthickness=0)
        self.scroll = ttk.Scrollbar(cont, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scroll.set)

        self.scroll.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        # Frame interior donde irán los registros
        self.inner = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.inner, anchor="nw")

        # Ajustar región de scroll cuando cambie el contenido
        self.inner.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        # Opcional: scroll con la rueda del ratón
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        # ===== Footer =====
        bottom = ttk.Frame(self.root)
        bottom.pack(fill="x", padx=10, pady=10)

        ttk.Button(
            bottom,
            text="💾 Guardar Cambios",
            command=self.guardar,
            style="GreenButton.TButton"
        ).pack(side="left", padx=5, fill="x")

        ttk.Button(
            bottom,
            text="⬅ Volver",
            command=self.volver,
            style="GreenButton.TButton"
        ).pack(side="right", padx=5, fill="x")

        self.check_vars = {}
        self.registros = []
        self.plan_db = None

    # ---------- Navegación ----------
    def volver(self):
        """Cerrar esta ventana y volver al menú principal."""
        try:
            self.root.destroy()          # cerrar Toplevel de Cumplimiento
        finally:
            # 👈 si el menú sigue existiendo, lo mostramos
            if self.menu_root is not None:
                self.menu_root.deiconify()

    # ---------- Scroll rueda ratón (opcional) ----------
    def _on_mousewheel(self, event):
        # En Windows el delta suele ser 120/-120
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # ---------- Seleccionar BD ----------
    def sel_bd(self):
        path = filedialog.askopenfilename(
            title="Selecciona la base de datos",
            filetypes=[("SQLite DB", "*.db")]
        )
        if not path:
            return

        self.plan_db = path
        self.lbl.config(text=os.path.basename(path))

        # crea tabla si no existe
        ensure_table(self.plan_db)

        conn = sqlite3.connect(self.plan_db)
        cur = conn.cursor()
        cur.execute(f"""
            SELECT id, equipo, marca, modelo, codigo, ubicacion, fecha_tentativa,
                   cumplido, fecha_cumplimiento 
            FROM {PLAN_TABLE}
        """)
        self.registros = cur.fetchall()
        conn.close()

        self.mostrar()

    # ---------- Mostrar registros ----------
    def mostrar(self):
        # limpiar
        for w in self.inner.winfo_children():
            w.destroy()

        self.check_vars.clear()

        ttk.Label(
            self.inner,
            text="Marque los equipos mantenidos:",
            font=("Arial", 11, "bold")
        ).pack(anchor="w", pady=6)

        for r in self.registros:
            _id, eq, ma, mo, co, ub, ft, cu, fc = r
            texto = (
                f"[{_id}] {eq} | {ma} | {mo} | {co} | {ub} | "
                f"Prog: {ft} | Cumplido: {'Sí' if cu else 'No'}"
            )

            v = IntVar(value=1 if cu else 0)
            cb = Checkbutton(
                self.inner,
                text=texto,
                variable=v,
                bg="#F0F3F4",
                anchor="w",
                padx=8
            )
            cb.pack(fill="x", pady=3)
            self.check_vars[_id] = v

        # 👈 opcional: volver arriba del scroll
        self.canvas.yview_moveto(0)

    # ---------- Guardar ----------
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

        messagebox.showinfo(
            "Éxito",
            f"Se actualizaron {actualizados} registros en:\n{self.plan_db}"
        )
