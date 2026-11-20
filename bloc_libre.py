import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog

import pymupdf
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import simpleSplit


class BlocLibre:

    def __init__(self, root):
        self.root = root
        self.root.title("Bloc Libre 0.3")
        self.root.geometry("1000x700")
        self.root.minsize(600, 400)

        self.tema_oscuro = False
        self.documentos = {}
        self.autoguardado_activo = True

        self.crear_interfaz()
        self.crear_menu()
        self.nuevo_documento()

        self.root.protocol("WM_DELETE_WINDOW", self.cerrar_aplicacion)
        self.programar_autoguardado()

    # INTERFAZ

    def crear_interfaz(self):
        self.contenedor = ttk.Frame(self.root)
        self.contenedor.pack(fill="both", expand=True)

        self.notebook = ttk.Notebook(self.contenedor)
        self.notebook.pack(fill="both", expand=True)

        self.notebook.bind("<<NotebookTabChanged>>", self.actualizar_estado)

        self.estado = ttk.Label(
            self.root,
            text="Bloc Libre 0.3",
            anchor="w"
        )
        self.estado.pack(fill="x", side="bottom")

    def crear_menu(self):
        menu = tk.Menu(self.root)

        archivo_menu = tk.Menu(menu, tearoff=0)
        archivo_menu.add_command(label="Nuevo", command=self.nuevo_documento, accelerator="Ctrl+N")
        archivo_menu.add_command(label="Abrir", command=self.abrir_documento, accelerator="Ctrl+O")
        archivo_menu.add_command(label="Guardar", command=self.guardar_documento, accelerator="Ctrl+S")
        archivo_menu.add_command(label="Guardar como", command=self.guardar_como, accelerator="Ctrl+Shift+S")
        archivo_menu.add_separator()
        archivo_menu.add_command(label="Exportar a PDF", command=self.exportar_pdf)
        archivo_menu.add_separator()
        archivo_menu.add_command(label="Cerrar pestaña", command=self.cerrar_pestana)
        archivo_menu.add_command(label="Salir", command=self.cerrar_aplicacion)

        menu.add_cascade(label="Archivo", menu=archivo_menu)

        editar_menu = tk.Menu(menu, tearoff=0)
        editar_menu.add_command(label="Buscar", command=self.buscar, accelerator="Ctrl+F")
        editar_menu.add_command(label="Buscar y reemplazar", command=self.reemplazar, accelerator="Ctrl+H")
        editar_menu.add_separator()
        editar_menu.add_command(label="Seleccionar todo", command=self.seleccionar_todo)

        menu.add_cascade(label="Editar", menu=editar_menu)

        vista_menu = tk.Menu(menu, tearoff=0)
        vista_menu.add_command(label="Aumentar letra", command=lambda: self.cambiar_tamano_letra(2))
        vista_menu.add_command(label="Reducir letra", command=lambda: self.cambiar_tamano_letra(-2))
        vista_menu.add_separator()
        vista_menu.add_command(label="Cambiar tema", command=self.cambiar_tema)

        menu.add_cascade(label="Vista", menu=vista_menu)

        pdf_menu = tk.Menu(menu, tearoff=0)
        pdf_menu.add_command(label="Unir PDF", command=self.unir_pdf)
        pdf_menu.add_command(label="Dividir PDF", command=self.dividir_pdf)
        pdf_menu.add_separator()
        pdf_menu.add_command(label="Eliminar páginas", command=self.eliminar_paginas)
        pdf_menu.add_command(label="Rotar páginas", command=self.rotar_paginas)
        pdf_menu.add_command(label="Reordenar páginas", command=self.reordenar_paginas)
        pdf_menu.add_command(label="Insertar páginas", command=self.insertar_paginas)

        menu.add_cascade(label="Herramientas PDF", menu=pdf_menu)

        self.root.config(menu=menu)

        self.root.bind("<Control-n>", lambda e: self.nuevo_documento())
        self.root.bind("<Control-o>", lambda e: self.abrir_documento())
        self.root.bind("<Control-s>", lambda e: self.guardar_documento())
        self.root.bind("<Control-Shift-S>", lambda e: self.guardar_como())
        self.root.bind("<Control-f>", lambda e: self.buscar())
        self.root.bind("<Control-h>", lambda e: self.reemplazar())

    # DOCUMENTOS Y PESTAÑAS

    def nuevo_documento(self):
        marco = ttk.Frame(self.notebook)

        texto = tk.Text(
            marco,
            wrap="word",
            undo=True,
            font=("Arial", 12),
            padx=10,
            pady=10
        )

        scroll = ttk.Scrollbar(marco, orient="vertical", command=texto.yview)
        texto.configure(yscrollcommand=scroll.set)

        texto.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        self.notebook.add(marco, text="Nuevo")
        self.notebook.select(marco)

        self.documentos[marco] = {
            "texto": texto,
            "ruta": None,
            "modificado": False,
            "tamano": 12
        }

        texto.bind("<<Modified>>", self.marcar_modificado)
        texto.bind("<KeyRelease>", self.actualizar_estado)
        texto.edit_modified(False)
        texto.focus_set()

        self.actualizar_estado()

    def documento_actual(self):
        seleccion = self.notebook.select()
        if not seleccion:
            return None

        marco = self.root.nametowidget(seleccion)
        return self.documentos.get(marco)

    def marco_actual(self):
        seleccion = self.notebook.select()
        if not seleccion:
            return None

        return self.root.nametowidget(seleccion)

    def marcar_modificado(self, event=None):
        marco = self.marco_actual()

        if marco not in self.documentos:
            return

        datos = self.documentos[marco]
        texto = datos["texto"]

        if texto.edit_modified():
            datos["modificado"] = True
            texto.edit_modified(False)
            self.actualizar_titulo(marco)
            self.actualizar_estado()

    def actualizar_titulo(self, marco):
        if marco not in self.documentos:
            return

        datos = self.documentos[marco]
        ruta = datos["ruta"]

        nombre = os.path.basename(ruta) if ruta else "Nuevo"

        if datos["modificado"]:
            nombre += " *"

        self.notebook.tab(marco, text=nombre)

    def actualizar_estado(self, event=None):
        datos = self.documento_actual()

        if not datos:
            self.estado.config(text="Bloc Libre 0.3")
            return

        contenido = datos["texto"].get("1.0", "end-1c")
        palabras = len(contenido.split())
        caracteres = len(contenido)

        self.estado.config(
            text=f"Palabras: {palabras} | Caracteres: {caracteres}"
        )

    # ABRIR Y GUARDAR

    def abrir_documento(self):
        ruta = filedialog.askopenfilename(
            filetypes=[
                ("Documentos de texto", "*.txt"),
                ("Documentos PDF", "*.pdf"),
                ("Todos los archivos", "*.*")
            ]
        )

        if not ruta:
            return

        try:
            extension = os.path.splitext(ruta)[1].lower()

            if extension == ".pdf":
                with pymupdf.open(ruta) as pdf:
                    contenido = "\n\n".join(pagina.get_text() for pagina in pdf)

                self.nuevo_documento()
                datos = self.documento_actual()
                datos["texto"].insert("1.0", contenido)
                datos["ruta"] = None
                datos["modificado"] = False

                marco = self.marco_actual()
                self.notebook.tab(marco, text=os.path.basename(ruta) + " (PDF)")

            else:
                with open(ruta, "r", encoding="utf-8") as archivo:
                    contenido = archivo.read()

                self.nuevo_documento()
                datos = self.documento_actual()
                datos["texto"].insert("1.0", contenido)
                datos["ruta"] = ruta
                datos["modificado"] = False

                marco = self.marco_actual()
                self.actualizar_titulo(marco)

            datos["texto"].edit_modified(False)
            self.actualizar_estado()

        except Exception as error:
            messagebox.showerror("Error", f"No se pudo abrir el archivo:\n{error}")

    def guardar_documento(self):
        datos = self.documento_actual()

        if not datos:
            return False

        if not datos["ruta"]:
            return self.guardar_como()

        try:
            contenido = datos["texto"].get("1.0", "end-1c")

            with open(datos["ruta"], "w", encoding="utf-8") as archivo:
                archivo.write(contenido)

            datos["modificado"] = False
            self.actualizar_titulo(self.marco_actual())
            self.actualizar_estado()
            return True

        except Exception as error:
            messagebox.showerror("Error", f"No se pudo guardar:\n{error}")
            return False

    def guardar_como(self):
        datos = self.documento_actual()

        if not datos:
            return False

        ruta = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[
                ("Archivo de texto", "*.txt"),
                ("Todos los archivos", "*.*")
            ]
        )

        if not ruta:
            return False

        datos["ruta"] = ruta
        return self.guardar_documento()

    # AUTOGUARDADO

    def programar_autoguardado(self):
        self.root.after(60000, self.autoguardado)

    def autoguardado(self):
        if self.autoguardado_activo:
            for marco, datos in list(self.documentos.items()):
                if datos["modificado"] and datos["ruta"]:
                    try:
                        contenido = datos["texto"].get("1.0", "end-1c")

                        with open(datos["ruta"], "w", encoding="utf-8") as archivo:
                            archivo.write(contenido)

                        datos["modificado"] = False
                        self.actualizar_titulo(marco)

                    except Exception:
                        pass

        self.programar_autoguardado()

    # BUSCAR Y REEMPLAZAR

    def buscar(self):
        datos = self.documento_actual()
        if not datos:
            return

        palabra = simpledialog.askstring("Buscar", "Palabra o texto que quieres buscar:")

        if not palabra:
            return

        texto = datos["texto"]
        texto.tag_remove("busqueda", "1.0", "end")

        inicio = "1.0"
        encontrados = 0

        while True:
            posicion = texto.search(palabra, inicio, stopindex="end", nocase=True)

            if not posicion:
                break

            final = f"{posicion}+{len(palabra)}c"
            texto.tag_add("busqueda", posicion, final)
            inicio = final
            encontrados += 1

        texto.tag_config("busqueda", background="yellow", foreground="black")

        messagebox.showinfo("Buscar", f"Coincidencias encontradas: {encontrados}")

    def reemplazar(self):
        datos = self.documento_actual()
        if not datos:
            return

        ventana = tk.Toplevel(self.root)
        ventana.title("Buscar y reemplazar")
        ventana.geometry("350x180")
        ventana.resizable(False, False)

        ttk.Label(ventana, text="Texto que quieres buscar:").pack(pady=(10, 0))
        entrada_buscar = ttk.Entry(ventana, width=40)
        entrada_buscar.pack(pady=5)

        ttk.Label(ventana, text="Reemplazar por:").pack()
        entrada_reemplazar = ttk.Entry(ventana, width=40)
        entrada_reemplazar.pack(pady=5)

        def ejecutar():
            buscar_texto = entrada_buscar.get()
            reemplazo = entrada_reemplazar.get()

            if not buscar_texto:
                return

            texto = datos["texto"]
            contenido = texto.get("1.0", "end-1c")
            nuevo = contenido.replace(buscar_texto, reemplazo)

            if nuevo != contenido:
                texto.delete("1.0", "end")
                texto.insert("1.0", nuevo)

            ventana.destroy()

        ttk.Button(ventana, text="Reemplazar todos", command=ejecutar).pack(pady=10)

    def seleccionar_todo(self):
        datos = self.documento_actual()

        if datos:
            texto = datos["texto"]
            texto.tag_add("sel", "1.0", "end-1c")
            texto.mark_set("insert", "1.0")
            texto.see("insert")

    # TAMAÑO DE LETRA Y TEMAS

    def cambiar_tamano_letra(self, cambio):
        datos = self.documento_actual()
        if not datos:
            return

        datos["tamano"] = max(6, min(48, datos["tamano"] + cambio))
        datos["texto"].config(font=("Arial", datos["tamano"]))

    def cambiar_tema(self):
        self.tema_oscuro = not self.tema_oscuro

        if self.tema_oscuro:
            fondo = "#202020"
            letra = "#ffffff"
            cursor = "#ffffff"
        else:
            fondo = "#ffffff"
            letra = "#000000"
            cursor = "#000000"

        for datos in self.documentos.values():
            datos["texto"].config(
                bg=fondo,
                fg=letra,
                insertbackground=cursor
            )

    # EXPORTAR TEXTO A PDF

    def exportar_pdf(self):
        datos = self.documento_actual()
        if not datos:
            return

        ruta = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("Documento PDF", "*.pdf")]
        )

        if not ruta:
            return

        try:
            contenido = datos["texto"].get("1.0", "end-1c")
            pdf = canvas.Canvas(ruta, pagesize=A4)

            ancho, alto = A4
            margen = 50
            tamano = datos["tamano"]
            y = alto - margen

            pdf.setFont("Helvetica", tamano)

            for linea in contenido.split("\n"):
                partes = simpleSplit(
                    linea,
                    "Helvetica",
                    tamano,
                    ancho - 2 * margen
                )

                if not partes:
                    partes = [""]

                for parte in partes:
                    if y < margen:
                        pdf.showPage()
                        pdf.setFont("Helvetica", tamano)
                        y = alto - margen

                    pdf.drawString(margen, y, parte)
                    y -= tamano + 4

            pdf.save()
            messagebox.showinfo("PDF creado", "El documento PDF se ha creado correctamente.")

        except Exception as error:
            messagebox.showerror("Error", f"No se pudo crear el PDF:\n{error}")

    # FUNCIONES AUXILIARES PDF

    def guardar_pdf_nuevo(self, documento, titulo):
        ruta = filedialog.asksaveasfilename(
            title=titulo,
            defaultextension=".pdf",
            filetypes=[("Documento PDF", "*.pdf")]
        )

        if not ruta:
            documento.close()
            return

        try:
            documento.save(ruta, garbage=4, deflate=True)
            messagebox.showinfo("Operación completada", f"PDF guardado correctamente:\n{ruta}")

        except Exception as error:
            messagebox.showerror("Error", f"No se pudo guardar el PDF:\n{error}")

        finally:
            documento.close()

    def seleccionar_paginas(self, cantidad):
        entrada = simpledialog.askstring(
            "Seleccionar páginas",
            "Escribe las páginas que quieres seleccionar.\nEjemplo: 1,3,5-8"
        )

        if entrada is None:
            return None

        try:
            paginas = set()

            for parte in entrada.replace(" ", "").split(","):
                if not parte:
                    raise ValueError()

                if "-" in parte:
                    extremos = parte.split("-")
                    if len(extremos) != 2:
                        raise ValueError()

                    inicio = int(extremos[0])
                    final = int(extremos[1])

                    if inicio > final:
                        raise ValueError()

                    numeros = range(inicio, final + 1)
                else:
                    numeros = [int(parte)]

                for numero in numeros:
                    if numero < 1 or numero > cantidad:
                        raise ValueError()

                    paginas.add(numero - 1)

            if not paginas:
                raise ValueError()

            return sorted(paginas)

        except Exception:
            messagebox.showerror(
                "Selección incorrecta",
                f"Introduce páginas entre 1 y {cantidad}.\nEjemplo: 1,3,5-8"
            )
            return None
 # UNIR PDF

    def unir_pdf(self):
        rutas = filedialog.askopenfilenames(
            title="Seleccionar PDF para unir",
            filetypes=[("Documentos PDF", "*.pdf")]
        )

        if not rutas:
            return

        resultado = pymupdf.open()

        try:
            for ruta in rutas:
                with pymupdf.open(ruta) as documento:
                    resultado.insert_pdf(documento)

            self.guardar_pdf_nuevo(resultado, "Guardar PDF unido")

        except Exception as error:
            resultado.close()
            messagebox.showerror("Error", f"No se pudieron unir los PDF:\n{error}")

    # DIVIDIR PDF

    def dividir_pdf(self):
        ruta = filedialog.askopenfilename(
            title="Seleccionar PDF",
            filetypes=[("Documentos PDF", "*.pdf")]
        )

        if not ruta:
            return

        carpeta = filedialog.askdirectory(title="Seleccionar carpeta de destino")

        if not carpeta:
            return

        try:
            with pymupdf.open(ruta) as original:
                cantidad = original.page_count

                for numero in range(cantidad):
                    resultado = pymupdf.open()

                    resultado.insert_pdf(
                        original,
                        from_page=numero,
                        to_page=numero
                    )

                    destino = os.path.join(carpeta, f"pagina_{numero + 1}.pdf")

                    resultado.save(destino, garbage=4, deflate=True)
                    resultado.close()

            messagebox.showinfo(
                "PDF dividido",
                f"Se han creado {cantidad} archivos PDF."
            )

        except Exception as error:
            messagebox.showerror("Error", f"No se pudo dividir el PDF:\n{error}")

    # ELIMINAR PÁGINAS

    def eliminar_paginas(self):
        ruta = filedialog.askopenfilename(
            title="Seleccionar PDF",
            filetypes=[("Documentos PDF", "*.pdf")]
        )

        if not ruta:
            return

        try:
            with pymupdf.open(ruta) as original:
                cantidad = original.page_count

                if cantidad == 0:
                    messagebox.showerror("Error", "El PDF no contiene páginas.")
                    return

                paginas = self.seleccionar_paginas(cantidad)

                if paginas is None:
                    return

                if len(paginas) >= cantidad:
                    messagebox.showerror("Error", "No puedes eliminar todas las páginas.")
                    return

                resultado = pymupdf.open()
                resultado.insert_pdf(original)

            for numero in sorted(paginas, reverse=True):
                resultado.delete_page(numero)

            self.guardar_pdf_nuevo(resultado, "Guardar PDF modificado")

        except Exception as error:
            messagebox.showerror("Error", f"No se pudieron eliminar las páginas:\n{error}")

    # ROTAR PÁGINAS

    def rotar_paginas(self):
        ruta = filedialog.askopenfilename(
            title="Seleccionar PDF",
            filetypes=[("Documentos PDF", "*.pdf")]
        )

        if not ruta:
            return

        try:
            with pymupdf.open(ruta) as original:
                cantidad = original.page_count
                paginas = self.seleccionar_paginas(cantidad)

                if paginas is None:
                    return

                grados = simpledialog.askinteger(
                    "Rotar páginas",
                    "Grados de rotación: 90, 180 o 270",
                    minvalue=90,
                    maxvalue=270
                )

                if grados not in (90, 180, 270):
                    if grados is not None:
                        messagebox.showerror(
                            "Error",
                            "Solo se permiten 90, 180 o 270 grados."
                        )
                    return

                resultado = pymupdf.open()
                resultado.insert_pdf(original)

            for numero in paginas:
                pagina = resultado[numero]
                pagina.set_rotation((pagina.rotation + grados) % 360)

            self.guardar_pdf_nuevo(resultado, "Guardar PDF rotado")

        except Exception as error:
            messagebox.showerror("Error", f"No se pudieron rotar las páginas:\n{error}")

    # REORDENAR PÁGINAS

    def reordenar_paginas(self):
        ruta = filedialog.askopenfilename(
            title="Seleccionar PDF",
            filetypes=[("Documentos PDF", "*.pdf")]
        )

        if not ruta:
            return

        try:
            with pymupdf.open(ruta) as original:
                cantidad = original.page_count

                entrada = simpledialog.askstring(
                    "Reordenar páginas",
                    "Escribe el nuevo orden de todas las páginas.\nEjemplo: 3,1,2"
                )

                if entrada is None:
                    return

                try:
                    orden = [
                        int(numero.strip()) - 1
                        for numero in entrada.split(",")
                    ]

                    if (
                        len(orden) != cantidad
                        or set(orden) != set(range(cantidad))
                    ):
                        raise ValueError()

                except Exception:
                    messagebox.showerror(
                        "Orden incorrecto",
                        f"Debes introducir todas las páginas una vez.\n"
                        f"Ejemplo para {cantidad} páginas: "
                        + ",".join(str(n) for n in range(1, cantidad + 1))
                    )
                    return

                resultado = pymupdf.open()
                resultado.insert_pdf(original)

            resultado.select(orden)
            self.guardar_pdf_nuevo(resultado, "Guardar PDF reordenado")

        except Exception as error:
            messagebox.showerror("Error", f"No se pudieron reordenar las páginas:\n{error}")

    # INSERTAR PÁGINAS

    def insertar_paginas(self):
        ruta_principal = filedialog.askopenfilename(
            title="Seleccionar PDF principal",
            filetypes=[("Documentos PDF", "*.pdf")]
        )

        if not ruta_principal:
            return

        ruta_extra = filedialog.askopenfilename(
            title="Seleccionar PDF del que insertar páginas",
            filetypes=[("Documentos PDF", "*.pdf")]
        )

        if not ruta_extra:
            return

        try:
            with pymupdf.open(ruta_principal) as principal:
                cantidad = principal.page_count

                posicion = simpledialog.askinteger(
                    "Insertar páginas",
                    f"¿Después de qué página quieres insertar?\n"
                    f"Escribe 0 para insertarlas al principio.\n"
                    f"Máximo: {cantidad}",
                    minvalue=0,
                    maxvalue=cantidad
                )

                if posicion is None:
                    return

                resultado = pymupdf.open()
                resultado.insert_pdf(principal)

            with pymupdf.open(ruta_extra) as extra:
                resultado.insert_pdf(extra, start_at=posicion)

            self.guardar_pdf_nuevo(resultado, "Guardar PDF con páginas insertadas")

        except Exception as error:
            messagebox.showerror("Error", f"No se pudieron insertar las páginas:\n{error}")

    # CERRAR PESTAÑAS Y APLICACIÓN

    def cerrar_pestana(self):
        marco = self.marco_actual()

        if marco is None:
            return

        datos = self.documentos[marco]

        if datos["modificado"]:
            respuesta = messagebox.askyesnocancel(
                "Cambios sin guardar",
                "¿Quieres guardar los cambios antes de cerrar?"
            )

            if respuesta is None:
                return

            if respuesta:
                if not self.guardar_documento():
                    return

        self.notebook.forget(marco)
        del self.documentos[marco]
        marco.destroy()

        if not self.documentos:
            self.nuevo_documento()

        self.actualizar_estado()

    def cerrar_aplicacion(self):
        for marco, datos in list(self.documentos.items()):
            if datos["modificado"]:
                self.notebook.select(marco)

                respuesta = messagebox.askyesnocancel(
                    "Cambios sin guardar",
                    "Hay cambios sin guardar.\n¿Quieres guardarlos antes de salir?"
                )

                if respuesta is None:
                    return

                if respuesta:
                    if not self.guardar_documento():
                        return

        self.autoguardado_activo = False
        self.root.destroy()


# INICIAR PROGRAMA

if __name__ == "__main__":
    ventana = tk.Tk()
    aplicacion = BlocLibre(ventana)
    ventana.mainloop()


