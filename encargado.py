# encargado.py

import tkinter as tk
from tkinter import messagebox
from ttkbootstrap import Style
from ttkbootstrap.widgets import Treeview, Entry, Button, Label
from factura import Factura
from productos import agregar_producto_db, actualizar_producto_db
from database import conectar


class EncargadoVentana:
    def __init__(self, master, user_id):
        self.master = master
        self.master.title("Sistema de Facturación")
        self.user_id = user_id 
         # Convertir a entero al inicio
        self.factura = Factura(self.user_id) # ✅ Guardamos el user_id como atributo
         # Ahora usamos self.user_id
        style = Style("flatly")  # Puedes cambiar el tema aquí si deseas

        self.frame = tk.Frame(master, padx=10, pady=10)
        self.frame.pack(fill="both", expand=True)

        btn_frame = tk.Frame(self.frame)
        btn_frame.pack(pady=10)

        self.total_label = Label(self.frame, text="Total: 0.00", font=("Arial", 12, "bold"))
        self.total_label.pack(pady=10)
        self.btn_salir = tk.Button(self.frame, text="Cerrar Sesión", command=self.volver_al_login)
        self.btn_salir.pack(pady=10)

        Button(btn_frame, text="Crear Factura", command=self.guardar_factura).grid(row=0, column=0, padx=5)
        Button(btn_frame, text="Agregar Producto a Factura", command=self.agregar_producto_a_factura).grid(row=0, column=1, padx=5)
        Button(btn_frame, text="Agregar Nuevo Producto al Sistema", command=self.ventana_nuevo_producto).grid(row=0, column=2, padx=5)
        Button(btn_frame, text="Actualizar Producto", command=self.ventana_actualizar_producto).grid(row=0, column=3, padx=5)

        self.tree = Treeview(self.frame, columns=("codigo", "nombre", "precio", "cantidad", "subtotal"), show='headings')
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col.capitalize())
        self.tree.pack(fill="both", expand=True)

    def agregar_producto_a_factura(self):
        win = tk.Toplevel(self.master)
        win.title("Buscar y Agregar Producto a Factura")

        Label(win, text="Buscar código o nombre:").grid(row=0, column=0, padx=5, pady=5)
        search_entry = Entry(win)
        search_entry.grid(row=0, column=1, padx=5, pady=5)

        result_list = tk.Listbox(win, height=6, width=50)
        result_list.grid(row=1, column=0, columnspan=3, padx=5, pady=5)

        Label(win, text="Cantidad:").grid(row=2, column=0, padx=5, pady=5)
        cantidad_entry = Entry(win)
        cantidad_entry.grid(row=2, column=1, padx=5, pady=5)

        def buscar():
            query = search_entry.get()
            con = conectar()
            cur = con.cursor(dictionary=True)
            like_query = f"%{query}%"
            cur.execute("SELECT * FROM productos WHERE codigo LIKE %s OR nombre LIKE %s", (like_query, like_query))
            resultados = cur.fetchall()
            cur.close()
            con.close()
            result_list.delete(0, tk.END)
            for p in resultados:
                result_list.insert(tk.END, f"{p['codigo']} - {p['nombre']} ({p['precio']})")

        def agregar():
            selected = result_list.curselection()
            if not selected:
                messagebox.showwarning("Advertencia", "Seleccione un producto de la lista.")
                return
            selected_text = result_list.get(selected[0])
            codigo = selected_text.split(' - ')[0]
            try:
                cantidad = int(cantidad_entry.get())
                result = self.factura.agregar_producto(codigo, cantidad)
                if result["estado"]:
                    self.actualizar_tabla()
                    win.destroy()
                else:
                    messagebox.showerror("Error", result["mensaje"])
            except ValueError:
                messagebox.showerror("Error", "Cantidad debe ser un número")

        Button(win, text="Buscar", command=buscar).grid(row=0, column=2, padx=5, pady=5)
        Button(win, text="Agregar a factura", command=agregar).grid(row=3, column=0, columnspan=3, pady=10)

    def actualizar_tabla(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        total = 0
        for item in self.factura.factura["items"]:
            self.tree.insert("", "end", values=(
                item["codigo"], item["nombre"], item["precio"], item["cantidad"], item["subtotal"]
            ))
            total += item["subtotal"]
        self.total_label.config(text=f"Total: {total:.2f}")

    def guardar_factura(self):
        from datetime import datetime
        from tkinter import messagebox
        from database import conectar

        def validar_entero(valor, nombre_campo):
            """Valida que el valor pueda convertirse a entero"""
            try:
                return int(valor)
            except (ValueError, TypeError):
                raise ValueError(f"{nombre_campo} debe ser un número entero. Valor recibido: {repr(valor)}")

        try:
            con = conectar()
            cur = con.cursor()

            if not self.factura.factura["items"]:
                messagebox.showwarning("Advertencia", "No hay productos en la factura.")
                return

            for idx, item in enumerate(self.factura.factura["items"]):
                print(f"Procesando ítem {idx + 1}: {item}")

                try:
                    producto_id = validar_entero(item.get('id'), "ID del producto")
                    cantidad = validar_entero(item.get('cantidad'), "Cantidad del producto")
                    user_id = validar_entero(self.user_id, "ID del usuario")
                except ValueError as ve:
                    raise ValueError(f"Datos inválidos en ítem {idx + 1}: {str(ve)}")

                cur.execute("SELECT stock FROM productos WHERE id = %s", (producto_id,))
                resultado = cur.fetchone()
                if not resultado:
                    raise Exception(f"No se encontró el producto con ID {producto_id}")

                stock_actual = resultado[0]
                if cantidad > stock_actual:
                    raise Exception(f"Stock insuficiente para '{item.get('nombre', 'Producto desconocido')}'")

                cur.execute("""
                    INSERT INTO salidas (producto_id, cantidad, fecha, usuario_id)
                    VALUES (%s, %s, %s, %s)
                """, (
                    producto_id,
                    cantidad,
                    datetime.now(),
                    user_id
                ))

                cur.execute("UPDATE productos SET stock = stock - %s WHERE id = %s",
                            (cantidad, producto_id))

            con.commit()

            self.factura.limpiar_factura()
            self.actualizar_tabla()
            self.total_label.config(text="Total: 0.00")
            messagebox.showinfo("Éxito", "Salida de productos registrada correctamente.")

        except Exception as e:
            con.rollback()
            messagebox.showerror("Error", f"No se pudo registrar la salida: {str(e)}")
        finally:
            cur.close()
            con.close()


    def ventana_nuevo_producto(self):
        win = tk.Toplevel(self.master)
        win.title("Nuevo Producto")
        entries = {}
        campos = ["codigo", "nombre", "precio", "stock"]
        for i, campo in enumerate(campos):
            Label(win, text=campo.capitalize()).grid(row=i, column=0, padx=5, pady=5)
            e = Entry(win)
            e.grid(row=i, column=1, padx=5, pady=5)
            entries[campo] = e

        def guardar():
            try:
                agregar_producto_db(
                    entries["codigo"].get(),
                    entries["nombre"].get(),
                    float(entries["precio"].get()),
                    int(entries["stock"].get())
                )
                messagebox.showinfo("Éxito", "Producto agregado")
                win.destroy()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        Button(win, text="Guardar", command=guardar).grid(row=len(campos), column=0, columnspan=2, pady=10)

    def ventana_actualizar_producto(self):
        win = tk.Toplevel(self.master)
        win.title("Buscar Producto a Actualizar")
        Label(win, text="Código o nombre:").grid(row=0, column=0, padx=5, pady=5)
        search_entry = Entry(win)
        search_entry.grid(row=0, column=1, padx=5, pady=5)
        result_list = tk.Listbox(win, height=6, width=50)
        result_list.grid(row=1, column=0, columnspan=2, padx=5, pady=5)

        def buscar():
            query = search_entry.get()
            con = conectar()
            cur = con.cursor(dictionary=True)
            like_query = f"%{query}%"
            cur.execute("SELECT * FROM productos WHERE codigo LIKE %s OR nombre LIKE %s", (like_query, like_query))
            resultados = cur.fetchall()
            cur.close()
            con.close()
            result_list.delete(0, tk.END)
            for p in resultados:
                result_list.insert(tk.END, f"{p['codigo']} - {p['nombre']} ({p['precio']})")

        def seleccionar_producto():
            seleccionado = result_list.curselection()
            if not seleccionado:
                messagebox.showwarning("Advertencia", "Seleccione un producto.")
                return
            producto_info = result_list.get(seleccionado[0])
            codigo = producto_info.split(' - ')[0]

            con = conectar()
            cur = con.cursor(dictionary=True)
            cur.execute("SELECT * FROM productos WHERE codigo = %s", (codigo,))
            producto = cur.fetchone()
            cur.close()
            con.close()

            win.destroy()
            editar_win = tk.Toplevel(self.master)
            editar_win.title("Editar Producto")

            # Campos normales
            campos = ["codigo", "nombre", "precio"]
            entries = {}
            for i, campo in enumerate(campos):
                Label(editar_win, text=campo.capitalize()).grid(row=i, column=0, padx=5, pady=5)
                e = Entry(editar_win)
                e.insert(0, str(producto[campo]))
                e.grid(row=i, column=1, padx=5, pady=5)
                entries[campo] = e

            # Campo de stock actual
            Label(editar_win, text="Stock actual").grid(row=len(campos), column=0, padx=5, pady=5)
            Label(editar_win, text=str(producto["stock"])).grid(row=len(campos), column=1, padx=5, pady=5)

            # Nuevo campo: cantidad_stock (para aumentar/disminuir stock)
            Label(editar_win, text="Cantidad a ajustar").grid(row=len(campos)+1, column=0, padx=5, pady=5)
            cantidad_stock_entry = Entry(editar_win)
            cantidad_stock_entry.grid(row=len(campos)+1, column=1, padx=5, pady=5)

            def actualizar():
                try:
                    nuevo_codigo = entries["codigo"].get()
                    nuevo_nombre = entries["nombre"].get()
                    nuevo_precio = float(entries["precio"].get())
                    cantidad_stock = int(cantidad_stock_entry.get())

                    # Calcular nuevo stock
                    nuevo_stock = producto["stock"] + cantidad_stock  # Puedes usar '-' si lo deseas como resta

                    # Llamar a tu función de base de datos
                    actualizar_producto_db(nuevo_codigo, nuevo_nombre, nuevo_precio, nuevo_stock)

                    messagebox.showinfo("Éxito", "Producto actualizado correctamente.")
                    editar_win.destroy()
                except ValueError as ve:
                    messagebox.showerror("Error", f"Valores inválidos: {str(ve)}")
                except Exception as e:
                    messagebox.showerror("Error", f"No se pudo actualizar el producto: {str(e)}")

            Button(editar_win, text="Actualizar", command=actualizar).grid(row=len(campos)+2, column=0, columnspan=2, pady=10)
        
        Button(win, text="Buscar", command=buscar).grid(row=0, column=2, padx=5)
        Button(win, text="Seleccionar", command=seleccionar_producto).grid(row=2, column=0, columnspan=2, pady=10)

    def volver_al_login(self):
        """Cierra la ventana del encargado y regresa al login"""
        self.frame.destroy()
        from login import LoginVentana
        LoginVentana(self.master)