import tkinter as tk

# Prueba.py

def greet():
    label.config(text="Hello, Tkinter!")

root = tk.Tk()
root.title("Tkinter Demo")

label = tk.Label(root, text="Welcome!")
label.pack(pady=10)

button = tk.Button(root, text="Greet", command=greet)
button.pack(pady=5)

root.mainloop()
