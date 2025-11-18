# ===============================================================
# FORWARD MODELLING GRAVITASI (INTERAKTIF DALAM SATU JENDELA)
# - GUI kiri: input dan daftar sumber
# - Area kanan: peta & profil anomali
# ===============================================================

import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# -----------------------------------
# Global variables
# -----------------------------------
sources = []      # list: (x, z, rho)
cbar = None        # colorbar global

# -----------------------------------
# Fungsi gravitasi
# -----------------------------------
def gravity_anomaly_xy(x, y, z, rho):
    G = 6.67430e-11
    r3 = (x**2 + y**2 + z**2) ** 1.5
    r3 = np.where(r3 == 0, 1e-20, r3)
    return G * rho * z / r3 * 1e5  # mGal

# -----------------------------------
# Update plot
# -----------------------------------
def update_plot():
    global cbar

    # Clear axes
    for ax in axs:
        ax.clear()

    # Remove old colorbar
    if cbar is not None:
        cbar.remove()
        cbar = None

    # Jika belum ada sumber
    if not sources:
        axs[0].text(0.5, 0.5, "Belum ada sumber ditambahkan",
                    ha='center', va='center', fontsize=12, color='gray')
        canvas.draw()
        return

    # Buat grid
    x = np.linspace(-100, 100, 300)
    y = np.linspace(-100, 100, 300)
    X, Y = np.meshgrid(x, y)
    Z_total = np.zeros_like(X)

    # Hitung total anomali
    for (x0, z0, rho0) in sources:
        Z_total += gravity_anomaly_xy(X - x0, Y, z0, rho0)

    # Profil X
    g_profile = np.zeros_like(x)
    for (x0, z0, rho0) in sources:
        g_profile += gravity_anomaly_xy(x - x0, 0, z0, rho0)

    # Plot peta
    vmax = np.max(np.abs(Z_total))
    vmin = -vmax if vmax != 0 else -1e-12

    im = axs[0].imshow(Z_total, extent=[x.min(), x.max(), y.min(), y.max()],
                       origin='lower', cmap='viridis', vmin=vmin, vmax=vmax)
    axs[0].set_title("Gravity anomaly map (g_z) [mGal]")
    axs[0].set_xlabel("X (m)")
    axs[0].set_ylabel("Y (m)")

    # Plot titik sumber
    for (x0, z0, rho0) in sources:
        axs[0].scatter(x0, 0, color='black', s=50)
        axs[0].text(x0 + 2, 2, f"x={x0:.1f}, z={z0:.1f}\nρ={rho0:.0f}",
                    color='white', fontsize=8, ha='left', va='bottom')

    # Tambahkan colorbar baru
    cbar = fig.colorbar(im, ax=axs[0], fraction=0.046, pad=0.04, label='g_z (mGal)')

    # Plot profil
    axs[1].plot(x, g_profile, color='purple', linewidth=2)
    axs[1].set_title("g_z profile along X axis (Y=0)")
    axs[1].set_xlabel("X (m)")
    axs[1].set_ylabel("g_z (mGal)")
    axs[1].grid(True)

    canvas.draw()

# -----------------------------------
# Tombol-tombol GUI
# -----------------------------------
def add_point():
    try:
        x_val = float(entry_x.get())
        z_val = float(entry_z.get())
        rho_val = float(entry_rho.get())

        if z_val <= 0:
            messagebox.showerror("Input error", "Nilai z harus > 0")
            return

        sources.append((x_val, z_val, rho_val))
        listbox.insert(tk.END, f"{x_val:.1f}, {z_val:.1f}, {rho_val:.0f}")
        clear_inputs()
        update_plot()

    except ValueError:
        messagebox.showerror("Input error", "Masukkan angka valid!")

def clear_points():
    global sources
    sources = []
    listbox.delete(0, tk.END)
    update_plot()

def clear_inputs():
    entry_x.delete(0, tk.END)
    entry_z.delete(0, tk.END)
    entry_rho.delete(0, tk.END)

# -----------------------------------
# EDIT DATA
# -----------------------------------
def on_select(event):
    """Ketika memilih item, tampilkan di input."""
    if not listbox.curselection():
        return
    idx = listbox.curselection()[0]
    x, z, rho = sources[idx]

    entry_x.delete(0, tk.END); entry_x.insert(0, str(x))
    entry_z.delete(0, tk.END); entry_z.insert(0, str(z))
    entry_rho.delete(0, tk.END); entry_rho.insert(0, str(rho))

def update_selected():
    """Update nilai item yang dipilih."""
    if not listbox.curselection():
        messagebox.showerror("Error", "Pilih item dulu!")
        return

    idx = listbox.curselection()[0]

    try:
        x_val = float(entry_x.get())
        z_val = float(entry_z.get())
        rho_val = float(entry_rho.get())
    except ValueError:
        messagebox.showerror("Input error", "Masukkan angka valid!")
        return

    sources[idx] = (x_val, z_val, rho_val)
    listbox.delete(idx)
    listbox.insert(idx, f"{x_val:.1f}, {z_val:.1f}, {rho_val:.0f}")

    update_plot()

# -----------------------------------
# GUI
# -----------------------------------
root = tk.Tk()
root.title("Forward Modelling Gravitasi (Interaktif)")

# Frame kiri
frame_left = ttk.Frame(root, padding=10)
frame_left.grid(row=0, column=0, sticky="ns")

ttk.Label(frame_left, text="x (m):").grid(row=1, column=0, sticky="e")
entry_x = ttk.Entry(frame_left, width=15); entry_x.grid(row=1, column=1)

ttk.Label(frame_left, text="z (m):").grid(row=2, column=0, sticky="e")
entry_z = ttk.Entry(frame_left, width=15); entry_z.grid(row=2, column=1)

ttk.Label(frame_left, text="ρ (kg/m³):").grid(row=3, column=0, sticky="e")
entry_rho = ttk.Entry(frame_left, width=15); entry_rho.grid(row=3, column=1)

ttk.Button(frame_left, text="Tambah Titik", command=add_point).grid(row=4, column=0, columnspan=2, pady=5)
ttk.Button(frame_left, text="Update titik", command=update_selected).grid(row=5, column=0, columnspan=2, pady=5)

listbox = tk.Listbox(frame_left, width=40, height=20)
listbox.grid(row=6, column=0, columnspan=2, pady=5)
listbox.bind("<<ListboxSelect>>", on_select)

ttk.Button(frame_left, text="Hapus Semua", command=clear_points).grid(row=7, column=0, columnspan=2, pady=5)

# Frame kanan
frame_right = ttk.Frame(root, padding=6)
frame_right.grid(row=0, column=1)

fig, axs = plt.subplots(2, 1, figsize=(12, 12), gridspec_kw={'height_ratios': [3, 1]})
canvas = FigureCanvasTkAgg(fig, master=frame_right)
canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

update_plot()
root.mainloop()