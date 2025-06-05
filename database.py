import mysql.connector

def conectar():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Josetun778@SQL",
        database="facturacion"
    )