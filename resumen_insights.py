from tkinter import *
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import sqlite3
from database import PLAN_TABLE


class ResumenInsightsApp:
    def __init__(self, root, menu_root):
        self.root = root
        self.menu_root = menu_root
        self.root.title("📊 Resumen e Insights del Mantenimiento")
        self.root.geometry("900x600")

        # 👇 Capturar el cierre con la X de esta ventana
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
            background=BG_COLOR,
            font=("Arial", 16, "bold")
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
            root,
            text="Resumen e Insights del Mantenimiento",
            style="Titulo.TLabel",
            anchor="center"
        ).pack(pady=10, fill="x")

        # ===== Frame superior (selección de BD) =====
        top = ttk.Frame(root)
        top.pack(fill="x", padx=10, pady=5)

        self.lbl_bd = ttk.Label(
            top,
            text="BD: (no seleccionada)",
            font=("Arial", 10)
        )
        self.lbl_bd.pack(side="left", padx=6)

        ttk.Button(
            top,
            text="   Cargar Base de Datos   ",
            command=self.cargar_bd,
            style="GreenButton.TButton"
        ).pack(side="right", padx=6, fill="x")

        # ===== Frame central para info / resumen =====
        self.frame_info = ttk.Frame(root)
        self.frame_info.pack(padx=10, pady=10, fill="both", expand=True)

        ttk.Label(
            self.frame_info,
            text="Carga una base de datos para ver el resumen.",
            font=("Arial", 11)
        ).pack(pady=10)

        # ===== Footer / Volver =====
        bottom = ttk.Frame(root)
        bottom.pack(fill="x", padx=10, pady=10)

        ttk.Button(
            bottom,
            text="⬅ Volver al menú principal",
            command=self.volver,
            style="GreenButton.TButton"
        ).pack(side="bottom", padx=6, fill="x")

        self.db_path = None

    # ---------- Navegación ----------
    def volver(self):
        self.root.destroy()
        self.menu_root.deiconify()

    # ---------- Cargar BD ----------
    def cargar_bd(self):
        path = filedialog.askopenfilename(
            title="Selecciona una BD",
            filetypes=[("SQLite DB", "*.db")]
        )
        if not path:
            return

        self.db_path = path
        # Mostrar solo el nombre del archivo
        self.lbl_bd.config(text=f"BD: {path.split('/')[-1]}")

        try:
            conn = sqlite3.connect(path)
            df = pd.read_sql_query(f"SELECT * FROM {PLAN_TABLE}", conn)
            conn.close()
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"No se pudo leer la base de datos:\n{e}"
            )
            return

        if df.empty:
            messagebox.showwarning("Aviso", "La base de datos está vacía.")
            return

        self.mostrar_insights(df)

    # ---------- Mostrar insights ----------
    def mostrar_insights(self, df):
        # Limpiar frame central
        for w in self.frame_info.winfo_children():
            w.destroy()

        # Asegurar tipo fecha
        df["fecha_tentativa"] = pd.to_datetime(
            df["fecha_tentativa"],
            errors="coerce",
            dayfirst=True
        )
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
            f"📈 Porcentaje de cumplimiento: {porc:.1f}%\n"
            f"⚠️ Atrasados: {len(atrasados)}\n"
            f"🗓 Próximos este mes: {len(proximos)}"
        )

        # Título "Resumen General" centrado
        ttk.Label(
            self.frame_info,
            text="Resumen General",
            font=("Arial", 13, "bold"),
            anchor="center"
        ).pack(pady=5, fill="x")

        # Texto centrado y con fuente que muestra emojis a color (en Windows)
        text = Text(
            self.frame_info,
            height=8,
            wrap="word",
            bg="#FFFFFF",
            font=("Segoe UI Emoji", 15),
            relief="flat"
        )
        text.insert("1.0", resumen)

        # Centrar todo el contenido
        text.tag_configure("center", justify="center")
        text.tag_add("center", "1.0", "end")

        text.configure(state="disabled")
        text.pack(fill="x", padx=5, pady=5)

        # Botones inferiores (mismo ancho)
        btn_frame = ttk.Frame(self.frame_info)
        btn_frame.pack(pady=10, fill="x")

        ttk.Button(
            btn_frame,
            text="Ver Atrasados",
            command=lambda: self.mostrar_lista(atrasados, "Equipos Atrasados"),
            style="GreenButton.TButton"
        ).pack(side="left", padx=5, fill="x", expand=True)

        ttk.Button(
            btn_frame,
            text="Ver Próximos",
            command=lambda: self.mostrar_lista(proximos, "Equipos Próximos"),
            style="GreenButton.TButton"
        ).pack(side="left", padx=5, fill="x", expand=True)

    # ---------- Ventana con listado ----------
    def mostrar_lista(self, df_sub, titulo):
        if df_sub.empty:
            messagebox.showinfo(titulo, "No hay equipos en esta categoría.")
            return

        BG_COLOR = "#F0F3F4"

        v = Toplevel(self.root)
        v.title(titulo)
        v.geometry("800x400")
        v.configure(bg=BG_COLOR)

        # Frame principal
        frame_main = ttk.Frame(v)
        frame_main.pack(fill="both", expand=True, padx=10, pady=10)

        # Título de la ventana secundaria
        ttk.Label(
            frame_main,
            text=titulo,
            font=("Arial", 13, "bold"),
            anchor="center"
        ).pack(pady=5, fill="x")

        # Frame para la tabla
        frame_tabla = ttk.Frame(frame_main)
        frame_tabla.pack(fill="both", expand=True)

        cols = ["equipo", "marca", "modelo", "codigo", "ubicacion", "fecha_tentativa"]
        tree = ttk.Treeview(frame_tabla, columns=cols, show="headings")

        # Scroll vertical
        scroll_y = ttk.Scrollbar(frame_tabla, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scroll_y.set)

        scroll_y.pack(side="right", fill="y")
        tree.pack(side="left", fill="both", expand=True)

        for c in cols:
            tree.heading(c, text=c.capitalize())
            tree.column(c, width=120, anchor="w")

        for _, row in df_sub.iterrows():
            tree.insert("", END, values=[row.get(c, "") for c in cols])

        # Botón de cierre con el mismo estilo
        bottom = ttk.Frame(frame_main)
        bottom.pack(fill="x", pady=8)

        ttk.Button(
            bottom,
            text="Cerrar",
            command=v.destroy,
            style="GreenButton.TButton"
        ).pack(side="right", padx=5, fill="x")
