from database import conectar

def agregar_producto_db(codigo, nombre, precio, stock):
    con = conectar()
    cur = con.cursor()
    cur.execute("INSERT INTO productos (codigo, nombre, precio, stock) VALUES (%s, %s, %s, %s)", (codigo, nombre, precio, stock))
    con.commit()
    con.close()

def actualizar_producto_db(codigo, nombre, precio, stock):
    con = conectar()
    cur = con.cursor()
    cur.execute("UPDATE productos SET nombre = %s, precio = %s, stock = %s WHERE codigo = %s", (nombre, precio, stock, codigo))
    con.commit()
    con.close()
