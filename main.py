import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

from plan_mantenimiento import PlanMantenimientoApp
from cumplimiento import CumplimientoApp
from resumen_insights import ResumenInsightsApp
from informe_latex import InformeLatexApp


class MenuApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SAPhyton - Sistema de Mantenimiento")
        self.root.geometry("500x700")

        # ====== COLOR DE FONDO GLOBAL ======
        BG_COLOR = "#F0F3F4"   # gris claro suave
        self.root.configure(bg=BG_COLOR)

        # ====== ESTILO PERSONALIZADO ======
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("TFrame", background=BG_COLOR)
        style.configure("TLabel", background=BG_COLOR)

        style.configure("Titulo.TLabel", background=BG_COLOR,
                        font=("Arial", 16, "bold"))
        style.configure("Footer.TLabel", background=BG_COLOR,
                        font=("Arial", 9, "italic"))

        style.configure("GreenButton.TButton",
                        font=("Arial", 12),
                        foreground="white",
                        background="#4CAF50",
                        padding=6)
        style.map("GreenButton.TButton",
                  background=[("active", "#66BB6A")],
                  foreground=[("active", "white")])

        # ====== LOGO ======
        try:
            imagen_logo = Image.open(
                r"C:\Users\Luis\Desktop\Transformación Digital\Saphyton\SapythonV4\Logo_SAPython.png"
            )

            nuevo_ancho = 300
            ratio = nuevo_ancho / imagen_logo.width
            nuevo_alto = int(imagen_logo.height * ratio)

            imagen_logo = imagen_logo.resize((nuevo_ancho, nuevo_alto), Image.LANCZOS)
            self.logo_img = ImageTk.PhotoImage(imagen_logo)

            ttk.Label(root, image=self.logo_img, anchor="center").pack(pady=(20, 10))

        except Exception:
            ttk.Label(root, text="(No se pudo cargar el logo)",
                      foreground="red").pack()

        # ====== TÍTULO ======
        ttk.Label(root, text="Seleccione una opción",
                  anchor="center", style="Titulo.TLabel").pack(
            pady=10, ipady=10, fill="x"
        )

        # ====== FRAME BOTONES ======
        botones_frame = ttk.Frame(root)
        botones_frame.pack(pady=10, padx=40, fill="x")

        botones = [
            ("🔧 Plan de Mantenimiento", self.abrir_plan),
            ("📄 Generar Informe LaTeX", self.abrir_informe),
            ("✅ Cumplimiento", self.abrir_cumplimiento),
            ("📊 Resumen e Insights", self.abrir_resumen),
            ("ℹ️ Acerca de", self.abrir_acerca_de),   # <<--- NUEVO BOTÓN
            ("🚪 Salir", root.quit),
        ]

        for texto, comando in botones:
            ttk.Button(botones_frame, text=texto,
                       command=comando,
                       style="GreenButton.TButton").pack(
                pady=6, ipady=10, fill="x"
            )

        # ====== PIE DE PÁGINA ======
        # (Eliminado tu nombre; ahora está en Acerca de)
        ttk.Label(root,
                  text="SAPhyton © 2025",
                  anchor="center",
                  style="Footer.TLabel").pack(side="bottom", pady=10, fill="x")

    # ====== FUNCIONES ======
    def abrir_plan(self):
        self.root.withdraw()
        ventana = tk.Toplevel(self.root)
        PlanMantenimientoApp(ventana, self.root)

    def abrir_informe(self):
        self.root.withdraw()
        ventana = tk.Toplevel(self.root)
        InformeLatexApp(ventana, self.root)

    def abrir_resumen(self):
        self.root.withdraw()
        ventana = tk.Toplevel(self.root)
        ResumenInsightsApp(ventana, self.root)

    def abrir_cumplimiento(self):
        self.root.withdraw()
        ventana = tk.Toplevel(self.root)
        CumplimientoApp(ventana, self.root)

    # ====== 👉 NUEVA VENTANA ACERCA DE ======
    def abrir_acerca_de(self):
        ventana = tk.Toplevel(self.root)
        ventana.title("Acerca de SAPhyton")
        ventana.geometry("400x300")
        ventana.resizable(False, False)

        BG = "#F0F3F4"
        ventana.configure(bg=BG)

        ttk.Label(
            ventana,
            text="Acerca de SAPhyton",
            font=("Arial", 14, "bold"),
            background=BG
        ).pack(pady=10)

        ttk.Label(
            ventana,
            text="Desarrollado por:\n\nLuis Paolo Marcial Sánchez\n\n"
                 "Versión: 1.0\n"
                 "© 2025 - Todos los derechos reservados.",
            anchor="center",
            font=("Arial", 11),
            background=BG,
            justify="center"
        ).pack(pady=20)

        ttk.Button(
            ventana,
            text="Cerrar",
            style="GreenButton.TButton",
            command=ventana.destroy
        ).pack(pady=10)


if __name__ == "__main__":
    root = tk.Tk()
    app = MenuApp(root)
    root.mainloop()
