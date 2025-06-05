from login import LoginVentana
import tkinter as tk

if __name__ == "__main__":
    app = tk.Tk()
    ventana_login = LoginVentana(app)
    app.mainloop()