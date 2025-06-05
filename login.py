import tkinter as tk
from tkinter import messagebox
from encargado import EncargadoVentana
from gerente import GerenteVentana
from database import conectar

class LoginVentana:
    def __init__(self, master):
        self.master = master
        self.master.title("Login - Sistema de Facturación")
        self.frame = tk.Frame(master)
        self.frame.pack(padx=20, pady=20)

        tk.Label(self.frame, text="Usuario:").grid(row=0, column=0, sticky="e")
        tk.Label(self.frame, text="Contraseña:").grid(row=1, column=0, sticky="e")

        self.usuario = tk.Entry(self.frame)
        self.clave = tk.Entry(self.frame, show="*")
        self.usuario.grid(row=0, column=1)
        self.clave.grid(row=1, column=1)

        tk.Button(self.frame, text="Iniciar sesión", command=self.login).grid(row=2, columnspan=2, pady=10)

    def login(self):
        usuario = self.usuario.get()
        clave = self.clave.get()
        con = conectar()
        cur = con.cursor(dictionary=True)
        cur.execute("SELECT * FROM usuarios WHERE usuario = %s AND clave = %s", (usuario, clave))
        user = cur.fetchone()
        con.close()

        if user:
            self.frame.destroy()
            if user["rol"] == "gerente":
                GerenteVentana(self.master, user)  # Pasamos todo el diccionario
            else:
                EncargadoVentana(self.master, user_id=user["id"])  # Solo el id
        else:
            messagebox.showerror("Error", "Credenciales incorrectas")