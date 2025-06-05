# factura.py

from database import conectar
from datetime import datetime
from decimal import Decimal

class Factura:
    def __init__(self, user_id):
        self.user_id = user_id
        self.factura = {
            'cliente': {'nombre': 'Consumidor Final', 'nit': 'CF'},
            'items': [],
            'subtotal': Decimal('0.00'),
            'impuesto': Decimal('0.00'),
            'total': Decimal('0.00')
        }

    def generar_numero_factura(self):
        return f"FAC-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    def limpiar_factura(self):
        self.factura["items"].clear()
        self.factura["subtotal"] = Decimal('0.00')
        self.factura["impuesto"] = Decimal('0.00')
        self.factura["total"] = Decimal('0.00')

    def establecer_cliente(self, nombre, nit):
        """Permite cambiar los datos del cliente"""
        self.factura['cliente']['nombre'] = nombre
        self.factura['cliente']['nit'] = nit

    def agregar_producto(self, codigo, cantidad):
        con = conectar()
        cur = con.cursor(dictionary=True)
        cur.execute("SELECT * FROM productos WHERE codigo = %s", (codigo,))
        prod = cur.fetchone()
        cur.close()
        con.close()

        if not prod:
            return {"estado": False, "mensaje": "Producto no encontrado"}
        if cantidad <= 0:
            return {"estado": False, "mensaje": "Cantidad debe ser mayor a 0"}
        if cantidad > prod['stock']:
            return {"estado": False, "mensaje": "Stock insuficiente"}

        subtotal = Decimal(prod['precio']) * Decimal(cantidad)
        self.factura['items'].append({
            'id': prod['id'],
            'codigo': prod['codigo'],
            'nombre': prod['nombre'],
            'precio': Decimal(prod['precio']),
            'cantidad': cantidad,
            'subtotal': subtotal
        })
        self.recalcular()
        return {"estado": True, "mensaje": "Producto agregado"}

    def recalcular(self):
        try:
            subtotal = sum(i['subtotal'] for i in self.factura['items'])
            impuesto = subtotal * Decimal('0.13')  # Impuesto del 13%
            total = subtotal + impuesto

            self.factura['subtotal'] = subtotal
            self.factura['impuesto'] = impuesto
            self.factura['total'] = total
        except Exception as e:
            raise ValueError(f"Error al recalcular la factura: {str(e)}")

    def mostrar_factura(self):
        salida = "FACTURA\n" + "-" * 50 + "\n"
        for item in self.factura['items']:
            salida += f"{item['nombre']} x{item['cantidad']} = ${item['subtotal']:.2f}\n"
        salida += "-" * 50 + f"\nTOTAL: ${self.factura['total']:.2f}\n"
        return salida

    def obtener_datos(self):
        return {
            "cliente": self.factura["cliente"],
            "items": self.factura["items"],
            "subtotal": self.factura["subtotal"],
            "impuesto": self.factura["impuesto"],
            "total": self.factura["total"]
        }