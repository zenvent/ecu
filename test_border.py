import tkinter as tk
import time

def turn_on_border():
    entry.config(highlightthickness=2, highlightbackground='#b04a00', highlightcolor='#b04a00')
    entry.focus_set()
    print(f"Border ON. Thickness: {entry.cget('highlightthickness')}")

def on_return(event=None):
    print("Return pressed")
    # Simulate sending input
    text = entry.get()
    print(f"Input: {text}")
    entry.delete(0, tk.END)
    
    # Reset border
    entry.config(highlightthickness=0, highlightbackground='#1c1c1c', highlightcolor='#1c1c1c')
    print(f"Border OFF. Thickness: {entry.cget('highlightthickness')}")
    root.quit()

root = tk.Tk()
root.configure(bg='#1c1c1c')

entry = tk.Entry(root, font=("Consolas", 10), borderwidth=0, highlightthickness=0, bg="#1c1c1c", fg="#fafafa")
entry.pack(padx=20, pady=20)
entry.bind('<Return>', on_return)

# Auto-run test
root.after(1000, lambda: entry.insert(0, "Test Input"))
root.after(2000, turn_on_border)
root.after(3000, lambda: on_return())

root.mainloop()
