# ===============================================================
# FORWARD MODELLING GRAVITASI (INTERAKTIF DALAM SATU JENDELA)
# ===============================================================

import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# -----------------------------------
# Global variables
# -----------------------------------
sources = []      # list: (name, x, z, rho)
cbar = None       # colorbar global

# -----------------------------------
# Fungsi: g_z untuk titik (x,y,z) dengan densitas rho (kg/m³)
# -----------------------------------
def gravity_anomaly_xy(x, y, z, rho):
    G = 6.67430e-11                     # konstanta gravitasi SI
    r3 = (x**2 + y**2 + z**2) ** 1.5
    r3 = np.where(r3 == 0, 1e-20, r3)   # hindari pembagian nol
    return G * rho * z / r3 * 1e5       # hasil dalam mGal

# -----------------------------------
# Fungsi untuk memperbarui grafik
# -----------------------------------
def update_plot():
    global cbar
    for ax in axs:
        ax.clear()

    if not sources:
        axs[0].text(0.5, 0.5, "Belum ada sumber ditambahkan",
                    ha='center', va='center', fontsize=12, color='gray')
        canvas.draw()
        return

    # Grid X-Y untuk peta
    x = np.linspace(-200, 200, 600)
    y = np.linspace(-200, 200, 600)
    X, Y = np.meshgrid(x, y)
    Z_total = np.zeros_like(X)

    # Hitung total field (asumsi semua di y=0)
    for (_, x0, z0, rho0) in sources:
        Z_total += gravity_anomaly_xy(X - x0, Y, z0, rho0)

    # Profil (y=0)
    g_profile = np.zeros_like(x)
    for (_, x0, z0, rho0) in sources:
        g_profile += gravity_anomaly_xy(x - x0, 0, z0, rho0)

    # Peta anomali
    vmax = np.max(np.abs(Z_total))
    vmin = -vmax if vmax != 0 else -1e-12

    im = axs[0].imshow(Z_total, extent=[x.min(), x.max(), y.min(), y.max()],
                       origin='lower', cmap='viridis', vmin=vmin, vmax=vmax)
    axs[0].set_title("Gravity anomaly map (g_z) [mGal]")
    axs[0].set_xlabel("X (m)")
    axs[0].set_ylabel("Y (m)")

    for (name, x0, z0, rho0) in sources:
        axs[0].scatter(x0, 0, color='black', s=50)
        axs[0].text(x0 + 2, 2, f"{name}\nx={x0:.1f}, z={z0:.1f}\nρ={rho0:.0f}",
                    color='white', fontsize=8, ha='left', va='bottom', weight='bold')

    # Colorbar (hapus lama, buat baru sekali)
    if cbar:
        cbar.ax.remove()
    cbar = fig.colorbar(im, ax=axs[0], fraction=0.046, pad=0.04, label='g_z (mGal)')

    # Profil g_z di sepanjang X (y=0)
    axs[1].plot(x, g_profile, color='purple', linewidth=2)
    axs[1].set_title("g_z profile along X axis (Y=0)")
    axs[1].set_xlabel("X (m)")
    axs[1].set_ylabel("g_z (mGal)")
    axs[1].grid(True, linestyle="--", alpha=0.5)

    canvas.draw()

# -----------------------------------
# Fungsi tombol-tombol GUI
# -----------------------------------
def add_point():
    try:
        name_val = entry_name.get().strip()
        x_val = float(entry_x.get())
        z_val = float(entry_z.get())
        rho_val = float(entry_rho.get())

        if not name_val:
            messagebox.showerror("Input error", "Nama titik harus diisi")
            return
        if z_val <= 0:
            messagebox.showerror("Input error", "Nilai z (kedalaman) harus > 0")
            return
        if rho_val == 0:
            messagebox.showerror("Input error", "Nilai ρ tidak boleh 0")
            return

        sources.append((name_val, x_val, z_val, rho_val))
        listbox.insert(tk.END, f"{name_val}: x={x_val:.1f}, z={z_val:.1f}, ρ={rho_val:.0f}")
        clear_inputs()
        update_plot()

    except ValueError:
        messagebox.showerror("Input error", "Masukkan angka yang valid.")

def clear_points():
    global sources
    sources.clear()
    listbox.delete(0, tk.END)
    update_plot()

def clear_inputs():
    entry_name.delete(0, tk.END)
    entry_x.delete(0, tk.END)
    entry_z.delete(0, tk.END)
    entry_rho.delete(0, tk.END)

def delete_selected():
    if not listbox.curselection():
        messagebox.showerror("Error", "Pilih item dulu!")
        return
    idx = listbox.curselection()[0]
    sources.pop(idx)
    listbox.delete(idx)
    update_plot()

# -----------------------------------
# EDIT DATA
# -----------------------------------
def on_select(event):
    if not listbox.curselection():
        return
    idx = listbox.curselection()[0]
    name, x, z, rho = sources[idx]

    entry_name.delete(0, tk.END); entry_name.insert(0, str(name))
    entry_x.delete(0, tk.END); entry_x.insert(0, str(x))
    entry_z.delete(0, tk.END); entry_z.insert(0, str(z))
    entry_rho.delete(0, tk.END); entry_rho.insert(0, str(rho))

def update_selected():
    if not listbox.curselection():
        messagebox.showerror("Error", "Pilih item dulu!")
        return
    idx = listbox.curselection()[0]
    try:
        name_val = entry_name.get().strip()
        x_val = float(entry_x.get())
        z_val = float(entry_z.get())
        rho_val = float(entry_rho.get())
    except ValueError:
        messagebox.showerror("Input error", "Masukkan angka valid!")
        return
    sources[idx] = (name_val, x_val, z_val, rho_val)
    listbox.delete(idx)
    listbox.insert(idx, f"{name_val}: x={x_val:.1f}, z={z_val:.1f}, ρ={rho_val:.0f}")
    update_plot()

# -----------------------------------
# GUI Utama
# -----------------------------------
root = tk.Tk()
root.title("Forward Modelling Gravitasi (Interaktif)")

# Frame kiri
frame_left = ttk.Frame(root, padding=10)
frame_left.grid(row=0, column=0, sticky="ns")

ttk.Label(frame_left, text="Input Titik Sumber").grid(row=0, column=0, columnspan=2, pady=5)
ttk.Label(frame_left, text="Nama:").grid(row=1, column=0, sticky="e")
entry_name = ttk.Entry(frame_left, width=15); entry_name.grid(row=1, column=1, pady=2)

ttk.Label(frame_left, text="x (m):").grid(row=2, column=0, sticky="e")
entry_x = ttk.Entry(frame_left, width=15); entry_x.grid(row=2, column=1, pady=2)

ttk.Label(frame_left, text="z (m, kedalaman):").grid(row=3, column=0, sticky="e")
entry_z = ttk.Entry(frame_left, width=15); entry_z.grid(row=3, column=1, pady=2)

ttk.Label(frame_left, text="ρ (kg/m³):").grid(row=4, column=0, sticky="e")
entry_rho = ttk.Entry(frame_left, width=15); entry_rho.grid(row=4, column=1, pady=2)

ttk.Button(frame_left, text="Tambah Titik", command=add_point).grid(row=5, column=0, columnspan=2, pady=5)
ttk.Button(frame_left, text="Update Titik", command=update_selected).grid(row=6, column=0, columnspan=2, pady=5)
ttk.Button(frame_left, text="Hapus Titik Terpilih", command=delete_selected).grid(row=7, column=0, columnspan=2, pady=5)
ttk.Button(frame_left, text="Hapus Semua", command=clear_points).grid(row=8, column=0, columnspan=2, pady=5) 

listbox = tk.Listbox(frame_left, width=60, height=25)
listbox.grid(row=9, column=0, columnspan=2, pady=5  )
listbox.bind("<<ListboxSelect>>", on_select) 

# Frame kanan untuk plot
frame_right = ttk.Frame(root, padding=12)
frame_right.grid(row=0, column=1)
fig, axs = plt.subplots(2, 1, figsize=(10, 10), gridspec_kw={'height_ratios': [3, 1]})

canvas = FigureCanvasTkAgg(fig, master=frame_right)
canvas.get_tk_widget().pack()
update_plot()
canvas.get_tk_widget().pack()
root.mainloop()