import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
import sqlite3
import pandas as pd
import re
from datetime import date


PLACEHOLDER = "% TABLAS_PLAN_MANTENIMIENTO"


def fecha_actual_espanol() -> str:
    """
    Devuelve la fecha actual en español, por ejemplo:
    'Jueves, 27 de noviembre del 2025'
    """
    dias = [
        "Lunes", "Martes", "Miércoles", "Jueves",
        "Viernes", "Sábado", "Domingo"
    ]
    meses = [
        "enero", "febrero", "marzo", "abril", "mayo", "junio",
        "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
    ]
    hoy = date.today()
    nombre_dia = dias[hoy.weekday()]      # lunes = 0
    nombre_mes = meses[hoy.month - 1]     # enero = 0
    return f"{nombre_dia}, {hoy.day} de {nombre_mes} del {hoy.year}"


def latex_escape(text: str) -> str:
    """
    Escapa caracteres especiales de LaTeX en un texto.
    """
    replacements = {
        "&": r"\&",
        "%": r"\%",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "$": r"\$",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
        "\\": r"\textbackslash{}",
    }
    return "".join(replacements.get(c, c) for c in text)


def latex_label_from_ubicacion(ubicacion: str) -> str:
    """
    Genera una etiqueta LaTeX segura (para \\label) a partir de la ubicación.
    """
    base = ubicacion.lower()
    base = re.sub(r"[^a-z0-9]+", "_", base)
    base = re.sub(r"_+", "_", base).strip("_")
    if not base:
        base = "lab"
    return f"tab:plan_mant_{base}"


def generar_tablas_latex(df: pd.DataFrame) -> str:
    """
    Genera tablas LaTeX por ubicación.

    Agrupa por (equipo, responsable), de modo que si un mismo equipo
    tiene responsables distintos, se separan en filas distintas con su propia cantidad.
    """
    lineas = []

    df = df.copy()
    # Aseguramos tipo string para las fechas
    df["fecha_tentativa"] = df["fecha_tentativa"].astype(str)

    # Asegurar columna 'responsable'; si no existe, usar valor por defecto
    if "responsable" not in df.columns:
        df["responsable"] = "Téc. de Laboratorio"
    else:
        df["responsable"] = df["responsable"].fillna("Téc. de Laboratorio")

    # Recorremos por ubicación
    for ubicacion, df_ubic in df.groupby("ubicacion"):
        ubic_esc = latex_escape(str(ubicacion))
        label = latex_label_from_ubicacion(str(ubicacion))

        lineas.append(r"\begin{table}[htbp]")
        lineas.append(r"    \centering")
        lineas.append(
            f"    \\caption{{Plan de mantenimiento preventivo de equipos / {ubic_esc}}}"
        )
        lineas.append(f"    \\label{{{label}}}")
        lineas.append(r"    {\footnotesize")
        lineas.append(r"    \begin{tabular}{p{3.9cm}p{1.3cm}p{3.0cm}p{4.0cm}p{1.5cm}}")
        lineas.append(r"        \toprule")
        lineas.append(
            r"        \textbf{Equipo} & \textbf{Cantidad} & \textbf{Ubicación} & "
            r"\textbf{Responsable} & \textbf{Fecha} \\"
        )
        lineas.append(r"        \midrule")

        # Agrupamos por (equipo, responsable) para contar cuántos equipos hay por responsable
        counts = (
            df_ubic.groupby(["equipo", "responsable"])
            .size()
            .to_dict()
        )

        # Fechas únicas por (equipo, responsable)
        fechas_por_grupo = (
            df_ubic.groupby(["equipo", "responsable"])["fecha_tentativa"]
            .apply(lambda s: sorted({f for f in s if isinstance(f, str) and f.strip()}))
            .to_dict()
        )

        # Ordenamos por equipo y responsable para que la salida sea consistente
        for (equipo, responsable) in sorted(
            fechas_por_grupo.keys(),
            key=lambda x: (str(x[0]), str(x[1])),
        ):
            equipo_esc = latex_escape(str(equipo))
            resp_esc = latex_escape(str(responsable))
            cantidad = counts.get((equipo, responsable), 0)

            fechas = fechas_por_grupo[(equipo, responsable)]
            if not fechas:
                fechas = [""]

            n_fechas = len(fechas)

            equipo_cell = rf"\multirow{{{n_fechas}}}{{*}}{{{equipo_esc}}}"
            cantidad_cell = rf"\multirow{{{n_fechas}}}{{*}}{{{cantidad}}}"
            ubic_cell = rf"\multirow{{{n_fechas}}}{{*}}{{{ubic_esc}}}"
            resp_cell = rf"\multirow{{{n_fechas}}}{{*}}{{{resp_esc}}}"

            for i, fecha in enumerate(fechas):
                fecha_esc = latex_escape(str(fecha))
                if i == 0:
                    lineas.append(
                        f"        {equipo_cell} & {cantidad_cell} & {ubic_cell} "
                        f"& {resp_cell} & {fecha_esc} \\\\"
                    )
                else:
                    lineas.append(
                        f"        & & & & {fecha_esc} \\\\"
                    )

        lineas.append(r"        \bottomrule")
        lineas.append(r"    \end{tabular}")
        lineas.append(r"    }")
        lineas.append(r"\end{table}")
        lineas.append("")

    return "\n".join(lineas)


def generar_informe_desde_archivos(
    db_path: Path,
    template_path: Path,
    output_path: Path,
    periodo_academico: str,
    fecha_presentacion: str,
) -> None:
    """
    Lógica de generación del informe: lee la BD, arma las tablas y escribe el .tex final.
    También reemplaza el período académico y la fecha de presentación en la plantilla.
    """
    if not db_path.exists():
        raise FileNotFoundError(f"No se encontró la base de datos: {db_path}")

    if not template_path.exists():
        raise FileNotFoundError(f"No se encontró la plantilla LaTeX: {template_path}")

    con = sqlite3.connect(db_path)
    try:
        df = pd.read_sql_query(
            "SELECT equipo, ubicacion, fecha_tentativa, responsable "
            "FROM plan_mantenimiento",
            con,
        )
    finally:
        con.close()

    if df.empty:
        raise ValueError("La tabla plan_mantenimiento está vacía.")

    tablas_latex = generar_tablas_latex(df)

    template_text = template_path.read_text(encoding="utf-8")

    # Reemplazar período académico y fecha de presentación
    template_text = template_text.replace(
        "<<PERIODO_ACADEMICO>>",
        latex_escape(periodo_academico),
    )
    template_text = template_text.replace(
        "<<FECHA_PRESENTACION>>",
        latex_escape(fecha_presentacion),
    )

    if PLACEHOLDER not in template_text:
        raise RuntimeError(
            f"No se encontró el marcador '{PLACEHOLDER}' en la plantilla LaTeX."
        )

    salida = template_text.replace(PLACEHOLDER, tablas_latex)
    output_path.write_text(salida, encoding="utf-8")


class InformeLatexApp:
    def __init__(self, ventana, main_root):
        self.ventana = ventana
        self.main_root = main_root

        self.ventana.title("Generador de Informe LaTeX")
        self.ventana.geometry("760x350")

        # Rutas por defecto (ajústalas a tu estructura real)
        base_dir = Path(__file__).parent
        self.db_var = tk.StringVar(
            value=str(base_dir / "Mantenimieto2026_v2.db")
        )
        self.template_var = tk.StringVar(
            value=str(base_dir / "plantilla_mantenimiento.tex")
        )
        self.output_var = tk.StringVar(
            value=str(base_dir / "informe_mantenimiento.tex")
        )

        # Nuevos campos: período académico y fecha de presentación
        self.periodo_var = tk.StringVar(
            value="agosto 2025 -- enero 2026"
        )
        # Fecha actual por defecto (en español)
        self.fecha_presentacion_var = tk.StringVar(
            value=fecha_actual_espanol()
        )

        self._construir_ui()

    def _construir_ui(self):
        frame = ttk.Frame(self.ventana, padding=20)
        frame.pack(fill="both", expand=True)

        ttk.Label(
            frame,
            text="Generación de Informe LaTeX de Mantenimiento",
            font=("Arial", 14, "bold"),
        ).grid(row=0, column=0, columnspan=3, pady=(0, 15), sticky="w")

        # Período académico
        ttk.Label(frame, text="Período académico:").grid(
            row=1, column=0, sticky="e", pady=5
        )
        ttk.Entry(frame, textvariable=self.periodo_var, width=70).grid(
            row=1, column=1, pady=5, sticky="w"
        )

        # Fecha de presentación
        ttk.Label(frame, text="Fecha de presentación:").grid(
            row=2, column=0, sticky="e", pady=5
        )
        ttk.Entry(frame, textvariable=self.fecha_presentacion_var, width=70).grid(
            row=2, column=1, pady=5, sticky="w"
        )

        # Config común de ancho para los botones superiores
        top_btn_width = 16

        # BD
        ttk.Label(frame, text="Base de datos (.db):").grid(
            row=3, column=0, sticky="e", pady=5
        )
        ttk.Entry(frame, textvariable=self.db_var, width=70).grid(
            row=3, column=1, pady=5, sticky="w"
        )
        ttk.Button(
            frame,
            text="Buscar...",
            command=self.buscar_db,
            width=top_btn_width,
            style="GreenButton.TButton",
        ).grid(row=3, column=2, padx=5)

        # Plantilla
        ttk.Label(frame, text="Plantilla LaTeX (.tex):").grid(
            row=4, column=0, sticky="e", pady=5
        )
        ttk.Entry(frame, textvariable=self.template_var, width=70).grid(
            row=4, column=1, pady=5, sticky="w"
        )
        ttk.Button(
            frame,
            text="Buscar...",
            command=self.buscar_plantilla,
            width=top_btn_width,
            style="GreenButton.TButton",
        ).grid(row=4, column=2, padx=5)

        # Salida
        ttk.Label(frame, text="Archivo de salida (.tex):").grid(
            row=5, column=0, sticky="e", pady=5
        )
        ttk.Entry(frame, textvariable=self.output_var, width=70).grid(
            row=5, column=1, pady=5, sticky="w"
        )
        ttk.Button(
            frame,
            text="Guardar como...",
            command=self.buscar_salida,
            width=top_btn_width,
            style="GreenButton.TButton",
        ).grid(row=5, column=2, padx=5)

        # Info marcador
        ttk.Label(
            frame,
            text="Nota: la plantilla debe contener el marcador: " + PLACEHOLDER,
            foreground="gray",
        ).grid(row=6, column=0, columnspan=3, pady=10, sticky="w")

        # Botones acción (mismo ancho y estilo del main)
        botones = ttk.Frame(frame)
        botones.grid(row=7, column=0, columnspan=3, pady=20)

        bottom_btn_width = 22
        ttk.Button(
            botones,
            text="Generar Informe",
            command=self.on_generar,
            width=bottom_btn_width,
            style="GreenButton.TButton",
        ).pack(side="left", padx=10)
        ttk.Button(
            botones,
            text="Volver al menú",
            command=self.cerrar,
            width=bottom_btn_width,
            style="GreenButton.TButton",
        ).pack(side="left", padx=10)

    def buscar_db(self):
        ruta = filedialog.askopenfilename(
            title="Seleccionar base de datos",
            filetypes=[("SQLite DB", "*.db"), ("Todos los archivos", "*.*")],
        )
        if ruta:
            self.db_var.set(ruta)

    def buscar_plantilla(self):
        ruta = filedialog.askopenfilename(
            title="Seleccionar plantilla LaTeX",
            filetypes=[("LaTeX", "*.tex"), ("Todos los archivos", "*.*")],
        )
        if ruta:
            self.template_var.set(ruta)

    def buscar_salida(self):
        ruta = filedialog.asksaveasfilename(
            title="Guardar informe LaTeX como...",
            defaultextension=".tex",
            filetypes=[("LaTeX", "*.tex"), ("Todos los archivos", "*.*")],
        )
        if ruta:
            self.output_var.set(ruta)

    def on_generar(self):
        try:
            db_path = Path(self.db_var.get())
            template_path = Path(self.template_var.get())
            output_path = Path(self.output_var.get())

            periodo = self.periodo_var.get().strip()
            fecha_pres = self.fecha_presentacion_var.get().strip()

            if not periodo or not fecha_pres:
                raise ValueError(
                    "Debe ingresar el período académico y la fecha de presentación."
                )

            generar_informe_desde_archivos(
                db_path,
                template_path,
                output_path,
                periodo,
                fecha_pres,
            )

            messagebox.showinfo(
                "Éxito",
                f"Informe generado correctamente: {output_path}",
            )
        except Exception as e:
            messagebox.showerror("Error al generar informe", str(e))

    def cerrar(self):
        # Mostrar el menú principal de nuevo
        if self.main_root is not None:
            self.main_root.deiconify()
        self.ventana.destroy()
