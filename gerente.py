import tkinter as tk
from tkinter import ttk, messagebox
from ttkbootstrap import Style
from database import conectar
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class GerenteVentana:
    def __init__(self, master, user):
        self.master = master
        self.master.title("Panel del Gerente")
        self.style = Style(theme="flatly")  # Puedes cambiar el tema si deseas

        # Frame principal
        self.frame = ttk.Frame(master)
        self.frame.pack(padx=20, pady=20, fill="both", expand=True)
        # Dentro de __init__ de GerenteVentana
        self.btn_salir = tk.Button(self.frame, text="Cerrar Sesión", command=self.volver_al_login)
        self.btn_salir.pack(pady=10)

# Opcional: si usas ttkbootstrap
# self.btn_salir = ttk.Button(self.frame, text="Cerrar Sesión", command=self.volver_al_login, bootstyle="danger")
# self.btn_salir.pack(pady=10)

        # Notebook para pestañas
        self.notebook = ttk.Notebook(self.frame)
        self.notebook.pack(fill="both", expand=True)

        # Bienvenida
        self.welcome_label = ttk.Label(self.frame, text=f"Bienvenido Gerente {user['usuario']}", font=("Arial", 16))
        self.welcome_label.pack(pady=10)
        self.saldo_label = ttk.Label(self.frame, text="Dinero Disponible: $0.00", font=("Arial", 14, "bold"), foreground="green")
        self.saldo_label.pack(pady=5)

        # Pestañas
        self.crear_pestana_ventas()
        self.crear_pestana_inventario()
        self.crear_pestana_ganancias()
        self.crear_pestana_graficas()
        self.crear_pestana_ingresos_egresos()
        self.crear_pestana_registrar_gasto()
        self.actualizar_saldo()
        self.crear_pestana_productos_bajo_stock()
        self.cargar_total_gastos()
        # Actualizar saldo al iniciar

    # --- Pestaña: Ventas ---
    def crear_pestana_ventas(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Ventas")

        # Etiqueta para total
        self.total_venta_label = ttk.Label(frame, text="Total vendido hoy: $0.00", font=("Arial", 12, "bold"))
        self.total_venta_label.pack(pady=10)
        # Etiqueta para mostrar total de gastos
        self.total_gastos_label = ttk.Label(self.frame, text="Total Gastos: $0.00", font=("Arial", 12))
        self.total_gastos_label.pack(pady=5)

        # Tabla de ventas por producto
        columns = ("Producto", "Cantidad Vendida", "Total Vendido")
        self.tree_ventas = ttk.Treeview(frame, columns=columns, show="headings")
        for col in columns:
            self.tree_ventas.heading(col, text=col)
            self.tree_ventas.column(col, width=150)
        self.tree_ventas.pack(fill="both", expand=True, padx=10, pady=10)

        # Botón para cargar datos
        ttk.Button(frame, text="Cargar Ventas del Día", command=lambda: self.cargar_ventas_del_dia()).pack(pady=5)

        # Cargar datos al inicio
        self.cargar_ventas_del_dia()
    # --- Pestaña: Inventario (Entradas y Salidas) ---
    def crear_pestana_inventario(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Inventario")

        notebook_inventario = ttk.Notebook(frame)
        notebook_inventario.pack(fill="both", expand=True, padx=10, pady=10)

        # Tabla de salidas
        frame_salidas = ttk.Frame(notebook_inventario)
        notebook_inventario.add(frame_salidas, text="Salidas")

        tree_salidas = ttk.Treeview(frame_salidas, columns=("ID", "Producto ID", "Cantidad", "Fecha", "Usuario ID"), show="headings")
        for col in tree_salidas["columns"]:
            tree_salidas.heading(col, text=col)
            tree_salidas.column(col, width=100)
        tree_salidas.pack(fill="both", expand=True)

        def cargar_salidas():
            con = conectar()
            cur = con.cursor()
            cur.execute("""
                SELECT s.id, s.producto_id, s.cantidad, s.fecha, s.usuario_id 
                FROM salidas s
                ORDER BY s.fecha DESC
            """)
            rows = cur.fetchall()
            for row in rows:
                tree_salidas.insert("", "end", values=row)
            con.close()

        cargar_salidas()

        # Tabla de entradas (suponiendo que tienes una tabla 'entradas')
        frame_entradas = ttk.Frame(notebook_inventario)
        notebook_inventario.add(frame_entradas, text="Entradas")

        tree_entradas = ttk.Treeview(frame_entradas, columns=("ID", "Producto ID", "Cantidad", "Fecha", "Proveedor"), show="headings")
        for col in tree_entradas["columns"]:
            tree_entradas.heading(col, text=col)
            tree_entradas.column(col, width=100)
        tree_entradas.pack(fill="both", expand=True)

        def cargar_entradas():
            con = conectar()
            cur = con.cursor()
            cur.execute("""
                SELECT e.id, e.producto_id, e.cantidad, e.fecha, e.proveedor
                FROM entradas e
                ORDER BY e.fecha DESC
            """)
            rows = cur.fetchall()
            for row in rows:
                tree_entradas.insert("", "end", values=row)
            con.close()

        cargar_entradas()

    # --- Pestaña: Ganancias ---
    def crear_pestana_ganancias(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Ganancias")

        # Tabla con columnas: Fecha, Ventas Totales, Compras Totales, Ganancia Neta
        columns = ("Fecha", "Ventas Totales", "Compras Totales", "Ganancia Neta")
        tree = ttk.Treeview(frame, columns=columns, show="headings")
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150)

        tree.pack(fill="both", expand=True, padx=10, pady=10)

        def cargar_datos():
            from database import conectar
            con = conectar()
            cur = con.cursor(dictionary=True)

            # Consulta unificada de ventas y compras por fecha
            query = """
                SELECT 
                    v.fecha_venta,
                    COALESCE(v.total_ventas, 0) AS total_ventas,
                    COALESCE(c.total_compras, 0) AS total_compras,
                    ROUND(COALESCE(v.total_ventas, 0) - COALESCE(c.total_compras, 0), 2) AS ganancia_neta
                FROM (
                    SELECT DATE(s.fecha) AS fecha_venta, 
                        SUM(p.precio * s.cantidad) AS total_ventas
                    FROM salidas s
                    JOIN productos p ON s.producto_id = p.id
                    GROUP BY DATE(s.fecha)
                ) v
                LEFT JOIN (
                    SELECT DATE(fecha_compra) AS fecha_compra, 
                        SUM(monto_total) AS total_compras
                    FROM compras
                    GROUP BY DATE(fecha_compra)
                ) c ON v.fecha_venta = c.fecha_compra

                UNION

                SELECT 
                    c.fecha_compra AS fecha_venta,
                    COALESCE(v.total_ventas, 0) AS total_ventas,
                    COALESCE(c.total_compras, 0) AS total_compras,
                    ROUND(COALESCE(v.total_ventas, 0) - COALESCE(c.total_compras, 0), 2) AS ganancia_neta
                FROM (
                    SELECT DATE(fecha_compra) AS fecha_compra, 
                        SUM(monto_total) AS total_compras
                    FROM compras
                    GROUP BY DATE(fecha_compra)
                ) c
                LEFT JOIN (
                    SELECT DATE(s.fecha) AS fecha_venta, 
                        SUM(p.precio * s.cantidad) AS total_ventas
                    FROM salidas s
                    JOIN productos p ON s.producto_id = p.id
                    GROUP BY DATE(s.fecha)
                ) v ON v.fecha_venta = c.fecha_compra
                WHERE v.fecha_venta IS NULL

                ORDER BY fecha_venta DESC;
            """

            cur.execute(query)
            rows = cur.fetchall()

            for row in rows:
                tree.insert("", "end", values=(
                    row["fecha_venta"],
                    f"${row['total_ventas']:.2f}",
                    f"${row['total_compras']:.2f}",
                    f"${row['ganancia_neta']:.2f}"
                ))

            con.close()

        cargar_datos()

    def cargar_ganancias(self):
        for item in self.ganancias_tree.get_children():
            self.ganancias_tree.delete(item)

        fecha = self.fecha_entry.get().strip() if self.fecha_entry.get().strip() else None

        con = conectar()
        cur = con.cursor()

        if fecha:
            cur.execute("""
                SELECT %s AS fecha,
                    (SELECT COALESCE(SUM(total), 0) FROM facturas WHERE DATE(fecha) = %s) AS ventas,
                    (SELECT COALESCE(SUM(monto_total), 0) FROM compras WHERE DATE(fecha_compra) = %s) AS compras;
            """, (fecha, fecha, fecha))
            row = cur.fetchone()
            if row and row[1] is not None:
                ganancia_neta = float(row[1]) - float(row[2])
                self.ganancias_tree.insert("", "end", values=(row[0], row[1], row[2], f"{ganancia_neta:.2f}"))
        else:
            cur.execute("""
                SELECT v.fecha_venta, v.total_ventas, c.total_compras,
                       ROUND(v.total_ventas - c.total_compras, 2) AS ganancia_neta
                FROM (
                    SELECT DATE(fecha) AS fecha_venta, SUM(total) AS total_ventas
                    FROM facturas GROUP BY fecha_venta
                ) v
                JOIN (
                    SELECT DATE(fecha_compra) AS fecha_compra, SUM(monto_total) AS total_compras
                    FROM compras GROUP BY fecha_compra
                ) c ON v.fecha_venta = c.fecha_compra
                ORDER BY v.fecha_venta DESC;
            """)
            rows = cur.fetchall()
            for row in rows:
                self.ganancias_tree.insert("", "end", values=row)

        con.close()

    # --- Pestaña: Gráficas ---
    def crear_pestana_graficas(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Gráficas")

        label = ttk.Label(frame, text="Ventas Diarias por Producto (Hoy)", font=("Arial", 14))
        label.pack(pady=10)

        fig, ax = plt.subplots(figsize=(8, 4))
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.get_tk_widget().pack(fill="both", expand=True)

        def graficar():
            from database import conectar
            con = conectar()
            cur = con.cursor(dictionary=True)

            cur.execute("""
                SELECT p.nombre, SUM(s.cantidad) AS cantidad
                FROM salidas s
                JOIN productos p ON s.producto_id = p.id
                WHERE DATE(s.fecha) = CURDATE()
                GROUP BY p.nombre
            """)
            datos = cur.fetchall()
            con.close()

            nombres = [d['nombre'] for d in datos]
            cantidades = [d['cantidad'] for d in datos]

            ax.clear()
            ax.bar(nombres, cantidades, color='skyblue')
            ax.set_title("Productos Vendidos Hoy")
            ax.set_xlabel("Producto")
            ax.set_ylabel("Cantidad Vendida")
            ax.grid(True)
            canvas.draw()

        graficar()

    # --- Pestaña: Ingresos y Egresos ---
    def crear_pestana_ingresos_egresos(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Ingresos y Egresos")
        
        tree = ttk.Treeview(frame, columns=("Tipo", "Monto", "Fecha", "Descripción"), show="headings")
        for col in tree["columns"]:
            tree.heading(col, text=col)
            tree.column(col, width=150)
        tree.pack(fill="both", expand=True, padx=10, pady=10)

        def cargar_movimientos():
            for item in tree.get_children():
                tree.delete(item)
            
            con = conectar()
            cur = con.cursor()

            # Ventas
            cur.execute("SELECT 'Venta' AS tipo, total, fecha, 'Factura' AS descripcion FROM facturas")
            rows = cur.fetchall()

            # Compras
            cur.execute("SELECT 'Compra' AS tipo, monto_total, fecha_compra, proveedor FROM compras")
            rows += cur.fetchall()

            # Gastos
            cur.execute("SELECT 'Gasto' AS tipo, monto, fecha_gasto, descripcion FROM gastos")
            rows += cur.fetchall()

            con.close()

            # Ordenar por fecha descendente
            for row in sorted(rows, key=lambda x: x[2], reverse=True):
                tree.insert("", "end", values=row)

        cargar_movimientos()
    def cargar_ventas_del_dia(self):
        from database import conectar

        # Limpiar tabla
        for item in self.tree_ventas.get_children():
            self.tree_ventas.delete(item)

        con = conectar()
        cur = con.cursor(dictionary=True)

        # Consulta SQL para agrupar por producto
        cur.execute("""
            SELECT 
                p.nombre AS producto,
                SUM(s.cantidad) AS cantidad_vendida,
                ROUND(p.precio * SUM(s.cantidad), 2) AS total_vendido
            FROM salidas s
            JOIN productos p ON s.producto_id = p.id
            WHERE DATE(s.fecha) = CURDATE()
            GROUP BY p.id, p.nombre
            ORDER BY total_vendido DESC
        """)

        rows = cur.fetchall()
        total_general = sum(row['total_vendido'] for row in rows) if rows else 0

        # Insertar datos en la tabla
        for row in rows:
            self.tree_ventas.insert("", "end", values=(
                row["producto"],
                row["cantidad_vendida"],
                f"{row['total_vendido']:.2f}"
            ))

        con.close()

        # Actualizar etiqueta de total
        self.total_venta_label.config(text=f"Total vendido hoy: ${total_general:.2f}")

    def crear_pestana_ganancias(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Ganancias")

        tree = ttk.Treeview(frame, columns=("Fecha", "Total Vendido"), show="headings")
        for col in tree["columns"]:
            tree.heading(col, text=col)
        tree.pack(fill="both", expand=True, padx=10, pady=10)

        def cargar_datos():
            from database import conectar
            con = conectar()
            cur = con.cursor(dictionary=True)

            cur.execute("""
                SELECT DATE(s.fecha) AS fecha_venta, 
                    SUM(p.precio * s.cantidad) AS total_vendido
                FROM salidas s
                JOIN productos p ON s.producto_id = p.id
                GROUP BY DATE(s.fecha)
                ORDER BY fecha_venta DESC
            """)
            rows = cur.fetchall()
            for row in rows:
                tree.insert("", "end", values=(row["fecha_venta"], f"{row['total_vendido']:.2f}"))

            con.close()

        cargar_datos()
    def volver_al_login(self):
        """Cierra la ventana del gerente y regresa al login"""
        self.frame.destroy()
        from login import LoginVentana
        LoginVentana(self.master)
    def crear_pestana_registrar_gasto(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Registrar Gasto")

        ttk.Label(frame, text="Nombre del Responsable:").pack(pady=5)
        nombre_entry = ttk.Entry(frame, width=40)
        nombre_entry.pack(pady=5)

        ttk.Label(frame, text="Descripción:").pack(pady=5)
        descripcion_entry = ttk.Entry(frame, width=40)
        descripcion_entry.pack(pady=5)

        ttk.Label(frame, text="Monto:").pack(pady=5)
        monto_entry = ttk.Entry(frame, width=20)
        monto_entry.pack(pady=5)

        def guardar_gasto():
            nombre = nombre_entry.get().strip()
            descripcion = descripcion_entry.get().strip()
            monto = monto_entry.get().strip()

            if not nombre or not descripcion or not monto:
                messagebox.showwarning("Error", "Todos los campos son obligatorios.")
                return

            try:
                monto = float(monto)
            except ValueError:
                messagebox.showerror("Error", "El monto debe ser un número válido.")
                return

            con = conectar()
            cur = con.cursor()
            cur.execute("""
                INSERT INTO gastos (descripcion, monto, fecha_gasto, responsable)
                VALUES (%s, %s, NOW(), %s)
            """, (descripcion, monto, nombre))
            con.commit()
            con.close()

            messagebox.showinfo("Éxito", "Gasto registrado correctamente.")
            self.refrescar_pantallas()  # Refrescar pestañas
            nombre_entry.delete(0, tk.END)
            descripcion_entry.delete(0, tk.END)
            monto_entry.delete(0, tk.END)

        ttk.Button(frame, text="Guardar Gasto", command=guardar_gasto).pack(pady=10)

    def actualizar_saldo(self):
        from database import conectar
        con = conectar()
        cur = con.cursor()

        # Total vendido (desde salidas + productos)
        cur.execute("""
            SELECT COALESCE(SUM(p.precio * s.cantidad), 0) 
            FROM salidas s
            JOIN productos p ON s.producto_id = p.id
        """)
        total_vendido = float(cur.fetchone()[0])

        # Total comprado (desde tabla compras)
        cur.execute("SELECT COALESCE(SUM(monto), 0) FROM gastos")
        total_comprado = float(cur.fetchone()[0])

        con.close()

        saldo = total_vendido - total_comprado
        self.saldo_label.config(text=f"Dinero Disponible: ${saldo:.2f}")

    def refrescar_pantallas(self):
        if hasattr(self, 'actualizar_saldo'):
            self.actualizar_saldo()
            self.cargar_total_gastos()
    
    def crear_pestana_productos_bajo_stock(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Productos Bajo Stock")

        # Tabla
        columns = ("Código", "Nombre", "Precio", "Stock")
        tree = ttk.Treeview(frame, columns=columns, show="headings")
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120)
        tree.pack(fill="both", expand=True, padx=10, pady=10)

        def cargar_datos():
            from database import conectar
            con = conectar()
            cur = con.cursor(dictionary=True)
            cur.execute("SELECT codigo, nombre, precio, stock FROM productos WHERE stock < 4 ORDER BY stock ASC")
            rows = cur.fetchall()
            con.close()

            for row in rows:
                tree.insert("", "end", values=(
                    row["codigo"],
                    row["nombre"],
                    f"${row['precio']:.2f}",
                    row["stock"]
                ))

        cargar_datos()



    def cargar_total_gastos(self):
        from database import conectar
        con = conectar()
        cur = con.cursor()
        cur.execute("SELECT COALESCE(SUM(monto), 0) FROM gastos")
        total = float(cur.fetchone()[0])
        con.close()
        self.total_gastos_label.config(text=f"Total Gastos: ${total:.2f}")

        

