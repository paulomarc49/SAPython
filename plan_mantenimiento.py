from tkinter import *
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import datetime as dt
import sqlite3
from database import ensure_table, PLAN_TABLE  # ensure_table(path), PLAN_TABLE nombre de la tabla
from utils import load_config, save_config


EXCEL_COLUMN_MAP = {
    "Equipo": "equipo",
    "Marca": "marca",
    "Modelo": "modelo",
    "Codigo": "codigo",
    "Código": "codigo",
    "Ubicacion": "ubicacion",
    "Ubicación": "ubicacion",
    "Frecuencia (meses)": "frecuencia",
    "Fecha último mantenimiento": "fecha"
}


class PlanMantenimientoApp:
    def __init__(self, root, menu_root):
        self.root = root
        self.menu_root = menu_root
        self.root.geometry("1424x700")
        self.root.title("Plan de Mantenimiento Preventivo")

        # ========= TEMA SAPHYTON (solo estilos, no cambia lógica) =========
        BG_COLOR  = "#F0F3F4"      # Gris claro suave
        BTN_COLOR = "#4CAF50"      # Verde principal
        BTN_HOVER = "#66BB6A"      # Verde claro para hover

        self.root.configure(bg=BG_COLOR)

        style = ttk.Style()
        style.theme_use("clam")

        # Fondo para contenedores y labels
        style.configure("TFrame", background=BG_COLOR)
        style.configure("TLabel", background=BG_COLOR)
        style.configure("TLabelframe", background=BG_COLOR)
        style.configure("TLabelframe.Label", background=BG_COLOR)

        # Botón verde reutilizable
        style.configure(
            "GreenButton.TButton",
            font=("Arial", 10),
            foreground="white",
            background=BTN_COLOR,
            padding=6
        )
        style.map(
            "GreenButton.TButton",
            background=[("active", BTN_HOVER)],
            foreground=[("active", "white")]
        )

        # Treeview con cabeceras verdes
        style.configure(
            "Treeview",
            background="white",
            fieldbackground="white",
            foreground="#333",
            rowheight=22,
        )
        style.configure(
            "Treeview.Heading",
            background=BTN_COLOR,
            foreground="white",
            font=("Arial", 10, "bold")
        )
        style.map(
            "Treeview.Heading",
            background=[("active", BTN_HOVER)]
        )

        # Listbox con selección verde
        self.root.option_add("*Listbox.background", "white")
        self.root.option_add("*Listbox.foreground", "#333")
        self.root.option_add("*Listbox.font", "Arial 10")
        self.root.option_add("*Listbox.highlightThickness", 0)
        self.root.option_add("*Listbox.selectBackground", BTN_COLOR)
        self.root.option_add("*Listbox.selectForeground", "white")

        # ===============================================================

        self.df = None
        self.df_filtrada = None
        self.equipos_seleccionados = []
        self.item_rows = {}

        cfg = load_config()
        self.plan_db = cfg.get("plan_db", "mantenimiento.db")
        ensure_table(self.plan_db)

        ttk.Label(root, text="Plan de Mantenimiento", font=("Arial", 12, "bold")).pack(pady=8)
        self._crear_controles_bd()
        self._crear_controles_excel()
        self._crear_listas()

    # ---------------- BD ----------------
    def _crear_controles_bd(self):
        frame = ttk.Frame(self.root)
        frame.pack(fill="x", padx=8, pady=4)
        ttk.Label(frame, text="BD actual:").pack(side="left", padx=(0, 6))
        self.lbl_plan_db = ttk.Label(
            frame, text=self.plan_db, foreground="#1f6feb", wraplength=420, justify="left"
        )
        self.lbl_plan_db.pack(side="left", fill="x", expand=True)

        btns = ttk.Frame(self.root)
        btns.pack(fill="x", padx=8, pady=(0, 6))
        ttk.Button(
            btns,
            text="Abrir Base de Datos",
            command=self.sel_bd,
            style="GreenButton.TButton",
        ).pack(side="left", padx=4)
        ttk.Button(
            btns,
            text="Crear Base de Datos",
            command=self.new_bd,
            style="GreenButton.TButton",
        ).pack(side="left", padx=4)

    def sel_bd(self):
        path = filedialog.askopenfilename(
            title="Selecciona una BD", filetypes=[("SQLite DB", "*.db")]
        )
        if path:
            self.plan_db = path
            ensure_table(self.plan_db)
            self.lbl_plan_db.config(text=self.plan_db)
            cfg = load_config()
            cfg["plan_db"] = self.plan_db
            save_config(cfg)
            messagebox.showinfo("BD seleccionada", f"Usando:\n{self.plan_db}")

    def new_bd(self):
        path = filedialog.asksaveasfilename(
            title="Crear nueva BD",
            defaultextension=".db",
            filetypes=[("SQLite DB", "*.db")],
        )
        if path:
            self.plan_db = path
            ensure_table(self.plan_db)
            self.lbl_plan_db.config(text=self.plan_db)
            cfg = load_config()
            cfg["plan_db"] = self.plan_db
            save_config(cfg)
            messagebox.showinfo("BD creada", f"Creada:\n{self.plan_db}")

    # ---------------- Excel ----------------
    def _crear_controles_excel(self):
        # Frame para que el botón tenga ancho completo uniforme
        btn_excel_frame = ttk.Frame(self.root)
        btn_excel_frame.pack(fill="x", padx=10)

        ttk.Button(
            btn_excel_frame,
            text="Cargar Base de Datos (Excel)",
            command=self.cargar_excel,
            style="GreenButton.TButton",
        ).pack(pady=5, fill="x")

        ttk.Label(self.root, text="Filtrar por ubicación:").pack()
        self.filtro_combo = ttk.Combobox(self.root, state="readonly")
        self.filtro_combo.bind("<<ComboboxSelected>>", self.filtrar)
        self.filtro_combo.pack(pady=5)

    def cargar_excel(self):
        filepath = filedialog.askopenfilename(filetypes=[("Archivos Excel", "*.xlsx")])
        if not filepath:
            return
        try:
            df = pd.read_excel(filepath)  # Excel tipo "equipos_mantenimiento_2026_limpio_desde_csv.xlsx"
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo leer el Excel:\n{e}")
            return

        # Mapeo de cabeceras a nombres internos
        column_map = {
            "Equipo": "equipo",
            "Marca": "marca",
            "Modelo": "modelo",
            "Codigo": "codigo",
            "Código": "codigo",
            "Ubicacion": "ubicacion",
            "Ubicación": "ubicacion",
            "Responsable": "responsable",
            "Frecuencia (meses)": "frecuencia_meses",
            "Fecha último mantenimiento": "ultimo_mantenimiento",  # texto dd/mm/yyyy
        }

        for orig, new in column_map.items():
            if orig in df.columns:
                df.rename(columns={orig: new}, inplace=True)

        # Columnas requeridas
        requeridas = [
            "equipo",
            "marca",
            "modelo",
            "codigo",
            "ubicacion",
            "responsable",
            "frecuencia_meses",
            "ultimo_mantenimiento",
        ]
        faltantes = [c for c in requeridas if c not in df.columns]
        if faltantes:
            messagebox.showerror("Error", f"Faltan columnas en el Excel: {', '.join(faltantes)}")
            return

        # Nos quedamos solo con lo que vamos a usar
        self.df = df[requeridas].copy()

        # Tipos de datos
        self.df["equipo"] = self.df["equipo"].astype(str)
        self.df["marca"] = self.df["marca"].astype(str)
        self.df["modelo"] = self.df["modelo"].astype(str)
        self.df["codigo"] = self.df["codigo"].astype(str)
        self.df["ubicacion"] = self.df["ubicacion"].astype(str)
        self.df["responsable"] = self.df["responsable"].astype(str)

        # Frecuencia a número
        self.df["frecuencia_meses"] = pd.to_numeric(self.df["frecuencia_meses"], errors="coerce")

        # -------- Parseo de fecha para futuras bases tipo "limpio_desde_csv" --------
        # La columna viene como texto dd/mm/yyyy o vacío
        self.df["ultimo_mantenimiento"] = pd.to_datetime(
            self.df["ultimo_mantenimiento"].astype(str).str.strip(),
            format="%d/%m/%Y",
            errors="coerce",       # valores inválidos -> NaT
        )

        # Calcular estado (Pendiente / Próximo / Al día)
        def calcular_estado(row):
            hoy = pd.Timestamp.today().normalize()

            if pd.isna(row["ultimo_mantenimiento"]) or pd.isna(row["frecuencia_meses"]):
                return "Pendiente"

            try:
                meses = int(row["frecuencia_meses"])
            except Exception:
                return "Pendiente"

            fecha_next = row["ultimo_mantenimiento"] + pd.DateOffset(months=meses)

            if fecha_next < hoy:
                return "Pendiente"
            elif (fecha_next - hoy).days <= 180:
                return "Próximo"
            else:
                return "Al día"

        self.df["estado"] = self.df.apply(calcular_estado, axis=1)

        # Columna SOLO para mostrar en listas (siempre dd/mm/yyyy)
        self.df["ultimo_mantenimiento_str"] = (
            self.df["ultimo_mantenimiento"]
                .dt.strftime("%d/%m/%Y")
                .fillna("")
        )

        # Llenar combo de ubicaciones
        ubicaciones = sorted(self.df["ubicacion"].dropna().astype(str).unique())
        self.filtro_combo["values"] = ubicaciones
        self.filtro_combo.set("Selecciona una ubicación")

        messagebox.showinfo("Éxito", "Base cargada correctamente.")

    # Helper para texto en Listbox
    def _format_disp(self, row):
        return (
            f"{row['equipo']} | {row['marca']} | {row['modelo']} | "
            f"{row['codigo']} | {row['ubicacion']} | "
            f"{row['ultimo_mantenimiento_str']} | {row['estado']}"
        )

    def filtrar(self, event=None):
        ubic = self.filtro_combo.get()
        self.df_filtrada = self.df[self.df["ubicacion"].astype(str) == str(ubic)]
        self.lista_equipos.delete(0, END)
        for _, row in self.df_filtrada.iterrows():
            disp = self._format_disp(row)
            self.lista_equipos.insert(END, disp)

    # ---------------- Listas ----------------
    def _crear_listas(self):
        frame = ttk.Frame(self.root)
        frame.pack(pady=10, fill="both", expand=True)

        # Lista izquierda
        frame_izq = ttk.Frame(frame)
        frame_izq.grid(row=0, column=0, padx=10)
        scroll_izq = ttk.Scrollbar(frame_izq, orient="vertical")
        self.lista_equipos = Listbox(
            frame_izq, selectmode="multiple", width=90, height=15, yscrollcommand=scroll_izq.set
        )
        scroll_izq.config(command=self.lista_equipos.yview)
        self.lista_equipos.pack(side="left", fill="both")
        scroll_izq.pack(side="right", fill="y")

        # Botones centro
        mid = ttk.Frame(frame)
        mid.grid(row=0, column=1)
        ttk.Button(
            mid,
            text="→ Agregar",
            command=self.agregar,
            style="GreenButton.TButton",
        ).pack(pady=5)
        ttk.Button(
            mid,
            text="← Eliminar",
            command=self.eliminar,
            style="GreenButton.TButton",
        ).pack(pady=5)

        # Lista derecha
        frame_der = ttk.Frame(frame)
        frame_der.grid(row=0, column=2, padx=10)
        scroll_der = ttk.Scrollbar(frame_der, orient="vertical")
        self.lista_sel = Listbox(
            frame_der, selectmode="multiple", width=90, height=15, yscrollcommand=scroll_der.set
        )
        scroll_der.config(command=self.lista_sel.yview)
        self.lista_sel.pack(side="left", fill="both")
        scroll_der.pack(side="right", fill="y")

        # Frame inferior para botones de ancho igual
        btns_bottom = ttk.Frame(self.root)
        btns_bottom.pack(fill="x", padx=10)

        ttk.Button(
            btns_bottom,
            text="Asignar Fechas Tentativas",
            command=self.asignar_fechas,
            style="GreenButton.TButton",
        ).pack(pady=5, fill="x")

        ttk.Button(
            btns_bottom,
            text="Ver Plan Guardado",
            command=self.ver_plan,
            style="GreenButton.TButton",
        ).pack(pady=5, fill="x")

        ttk.Button(
            self.root,
            text="⬅ Volver al menú",
            command=self.volver,
            style="GreenButton.TButton",
        ).pack(pady=5)

    def agregar(self):
        seleccion_indices = self.lista_equipos.curselection()
        if not hasattr(self, "df_filtrada") or self.df_filtrada is None:
            messagebox.showwarning("Atención", "Primero filtra por ubicación y selecciona equipos.")
            return

        mapa_disp_row = {}
        for _, row in self.df_filtrada.iterrows():
            disp = self._format_disp(row)
            mapa_disp_row[disp] = row

        for i in seleccion_indices:
            val = self.lista_equipos.get(i)
            if val not in self.equipos_seleccionados:
                self.equipos_seleccionados.append(val)
                self.lista_sel.insert(END, val)
            if val not in self.item_rows and val in mapa_disp_row:
                self.item_rows[val] = mapa_disp_row[val]

    def eliminar(self):
        for i in reversed(self.lista_sel.curselection()):
            val = self.lista_sel.get(i)
            if val in self.equipos_seleccionados:
                self.equipos_seleccionados.remove(val)
            self.lista_sel.delete(i)

    def volver(self):
        self.root.destroy()
        self.menu_root.deiconify()

    # ---------------- Fechas ----------------
    def asignar_fechas(self):
        if not self.equipos_seleccionados:
            messagebox.showwarning("Atención", "Selecciona al menos un equipo.")
            return
        self.abrir_fechas()

    def abrir_fechas(self):
        v = Toplevel(self.root)
        v.title("Asignar fechas tentativas")
        v.geometry("900x520")

        cont = ttk.Frame(v)
        cont.pack(fill="both", expand=True)
        canvas = Canvas(cont, highlightthickness=0)
        scroll = ttk.Scrollbar(cont, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        inner = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        ttk.Label(inner, text="Equipo", font=("Arial", 10, "bold")).grid(
            row=0, column=0, padx=8, pady=6, sticky="w"
        )
        ttk.Label(inner, text="Fecha (dd/mm/yyyy)", font=("Arial", 10, "bold")).grid(
            row=0, column=1, padx=8, pady=6, sticky="w"
        )

        self.entries = {}
        def_fecha = dt.date.today().strftime("%d/%m/%Y")
        for i, disp in enumerate(self.equipos_seleccionados, start=1):
            ttk.Label(inner, text=disp, wraplength=520, justify="left").grid(
                row=i, column=0, sticky="w", padx=8, pady=4
            )
            e = ttk.Entry(inner, width=18)
            e.grid(row=i, column=1, sticky="w", padx=8, pady=4)
            e.insert(0, def_fecha)
            self.entries[disp] = e

        ttk.Button(
            v,
            text="Guardar en BD",
            command=self.guardar,
            style="GreenButton.TButton",
        ).pack(pady=10)

    # ---------------- Guardar ----------------
    def guardar(self):
        ensure_table(self.plan_db)
        conn = sqlite3.connect(self.plan_db)
        cur = conn.cursor()

        for disp, ent in self.entries.items():
            fecha = ent.get().strip()

            row = self.item_rows.get(disp, None)

            if row is None and hasattr(self, "df") and self.df is not None:
                partes = [p.strip() for p in disp.split("|")]
                if len(partes) >= 5:
                    eq, ma, mo, co, ub = partes[:5]
                    filtro = (
                        (self.df["equipo"].astype(str).str.strip() == eq)
                        & (self.df["marca"].astype(str).str.strip() == ma)
                        & (self.df["modelo"].astype(str).str.strip() == mo)
                        & (self.df["codigo"].astype(str).str.strip() == co)
                        & (self.df["ubicacion"].astype(str).str.strip() == ub)
                    )
                    encontrados = self.df[filtro]
                    if not encontrados.empty:
                        row = encontrados.iloc[0]

            if row is None:
                print(f"[AVISO] No se encontró información para: {disp}. Se omite este equipo.")
                continue

            vals = {
                "equipo": str(row["equipo"]),
                "marca": str(row["marca"]),
                "modelo": str(row["modelo"]),
                "codigo": str(row["codigo"]),
                "ubicacion": str(row["ubicacion"]),
                "responsable": str(row.get("responsable", "")),
                "fecha_tentativa": str(fecha),
                "cumplido": 0,
                "fecha_cumplimiento": None,
            }

            cur.execute(
                f"""
                INSERT INTO {PLAN_TABLE}
                (equipo, marca, modelo, codigo, ubicacion, responsable, fecha_tentativa, cumplido, fecha_cumplimiento)
                VALUES (:equipo, :marca, :modelo, :codigo, :ubicacion, :responsable, :fecha_tentativa, :cumplido, :fecha_cumplimiento)
                """,
                vals,
            )

        conn.commit()
        conn.close()
        messagebox.showinfo("Éxito", f"Plan guardado en:\n{self.plan_db}")

    # ---------------- Ver plan ----------------
    # Programamción cuando se da click en ver plan
    def ver_plan(self):
        v = Toplevel(self.root)
        v.title("Plan Guardado")
        v.geometry("1200x500")

        cols = (
            "id",
            "equipo",
            "marca",
            "modelo",
            "codigo",
            "ubicacion",
            "responsable",
            "fecha_tentativa",
            "cumplido",
            "fecha_cumplimiento",
        )
        tree = ttk.Treeview(v, columns=cols, show="headings", selectmode="extended")
        tree.pack(fill="both", expand=True)

        labels = [
            "ID",
            "Equipo",
            "Marca",
            "Modelo",
            "Código",
            "Ubicación",
            "Responsable",
            "Fecha Tentativa",
            "Cumplido",
            "Fecha Cumpl.",
        ]
        for c, l in zip(cols, labels):
            tree.heading(c, text=l)
            tree.column(c, width=120 if c != "id" else 60, anchor="w")

        conn = sqlite3.connect(self.plan_db)
        cur = conn.cursor()
        cur.execute(
            f"""
            SELECT id, equipo, marca, modelo, codigo, ubicacion, responsable, fecha_tentativa, cumplido, fecha_cumplimiento
            FROM {PLAN_TABLE}
            """
        )
        rows = cur.fetchall()
        conn.close()

        for r in rows:
            tree.insert("", END, values=r)

        frame_btn = ttk.Frame(v)
        frame_btn.pack(pady=10)

        def eliminar_seleccionados():
            seleccion = tree.selection()
            if not seleccion:
                messagebox.showwarning("Atención", "No has seleccionado ningún equipo para eliminar.")
                return

            confirm = messagebox.askyesno(
                "Confirmar eliminación",
                f"¿Deseas eliminar {len(seleccion)} registro(s)?"
            )
            if not confirm:
                return

            conn = sqlite3.connect(self.plan_db)
            cur = conn.cursor()
            eliminados = 0
            for item in seleccion:
                data = tree.item(item, "values")
                record_id = data[0]
                cur.execute(f"DELETE FROM {PLAN_TABLE} WHERE id = ?", (record_id,))
                eliminados += 1
                tree.delete(item)
            conn.commit()
            conn.close()

            messagebox.showinfo("Éxito", f"Se eliminaron {eliminados} registro(s) correctamente.")

        ttk.Button(
            frame_btn,
            text="🗑 Eliminar Seleccionados",
            command=eliminar_seleccionados,
            style="GreenButton.TButton",
        ).pack(side="left", padx=5)
        ttk.Button(
            frame_btn,
            text="⬅ Cerrar",
            command=v.destroy,
            style="GreenButton.TButton",
        ).pack(side="left", padx=5)
