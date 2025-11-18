# ===============================================================
# FORWARD MODELLING GRAVITASI (MULTI POINT MASS, GUI SEDERHANA)
# - Tampilan: sama seperti versi awal (peta X-Y di atas, profil X di bawah)
# - Semua sumber diletakkan pada y = 0 (input y diabaikan)
# - Bisa menambah beberapa titik sumber; list ditampilkan di GUI
# - Hanya 1 colorbar (negatif → positif) pada peta
# ===============================================================

import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import matplotlib.pyplot as plt

# -----------------------------------
# Fungsi: g_z untuk titik (x,y,z) dengan 'rho' (satuan: kg/m^3)
# Mengembalikan nilai dalam mGal
# -----------------------------------
def gravity_anomaly_xy(x, y, z, rho):
    G = 6.67430e-11  # konstanta gravitasi SI
    r3 = (x**2 + y**2 + z**2) ** 1.5
    # hindari pembagian nol (meskipun z>0 seharusnya aman), tambahkan epsilon kecil
    r3 = np.where(r3 == 0, 1e-20, r3)
    return G * rho * z / r3 * 1e5  # hasil dalam mGal

# -----------------------------------
# Plot: peta X-Y di atas; profil di bawah (y=0)
# sources: list of (x0, z0, rho0), semua sumber dianggap berada pada y=0
# -----------------------------------
def plot_gravity(sources):
    # Grid pengamatan untuk peta (X-Y)
    x = np.linspace(-100, 100, 300)   # koordinat X (m)
    y = np.linspace(-100, 100, 300)   # koordinat Y (m)
    X, Y = np.meshgrid(x, y)          # grid 2D untuk peta

    # Hitung field total pada grid X-Y (setiap sumber di y=0)
    Z_total = np.zeros_like(X, dtype=float)
    for (x0, z0, rho0) in sources:
        # untuk peta: gunakan (X-x0, Y-0, z0)
        Z_total += gravity_anomaly_xy(X - x0, Y - 0.0, z0, rho0)

    # Persiapkan profil g_z di sepanjang y=0 (array 1D)
    g_profile = np.zeros_like(x, dtype=float)
    for (x0, z0, rho0) in sources:
        g_profile += gravity_anomaly_xy(x - x0, 0.0, z0, rho0)

    # Buat figure dengan dua subplot (peta & profil)
    fig, axs = plt.subplots(2, 1, figsize=(9, 9), gridspec_kw={'height_ratios': [3, 1]})

    # Satu colorbar simetris (negatif sampai positif)
    vmax = np.max(np.abs(Z_total))
    if vmax == 0:
        vmax = 1e-12  # agar tidak nol
    vmin = -vmax

    # Tampilkan peta (X = hor., Y = vert.)
    im = axs[0].imshow(Z_total, extent=[x.min(), x.max(), y.min(), y.max()],
                       origin='lower', cmap='viridis', vmin=vmin, vmax=vmax, aspect='auto')

    # Titik sumber pada peta (semua ada di y=0)
    for (x0, z0, rho0) in sources:
        axs[0].scatter(x0, 0.0, color='black', s=50, zorder=5)
        axs[0].text(x0 + 2, 2, f"x={x0:.1f} z={z0:.1f}\nρ={rho0:.0f}",
                    color='white', fontsize=8, ha='left', va='bottom', weight='bold')

    axs[0].set_title("Gravity Anomaly Map Y=0)")
    axs[0].set_xlabel("X (m)")
    axs[0].set_ylabel("Y (m)")

    # Satu colorbar untuk seluruh peta
    cbar = fig.colorbar(im, ax=axs[0], fraction=0.046, pad=0.04)
    cbar.set_label('mGal')

    # Profil g_z di sepanjang X (y=0)
    axs[1].plot(x, g_profile, color='purple', linewidth=2)
    axs[1].set_title("profile along X  ")
    axs[1].set_xlabel("X (m)")
    axs[1].set_ylabel("(mGal)")
    axs[1].grid(True, linestyle="--", alpha=0.5)

    # Set y-limits sedikit lebih lebar agar grafik rapi
    ymin = np.min(g_profile)
    ymax = np.max(g_profile)
    if ymin == ymax:
        # bila datanya konstan, buat batas kecil
        axs[1].set_ylim(ymin - 1e-6, ymax + 1e-6)
    else:
        pad = 0.1 * max(abs(ymin), abs(ymax))
        axs[1].set_ylim(ymin - pad, ymax + pad)

    plt.tight_layout()
    plt.show()

# -----------------------------------
# GUI: sama sederhana seperti awal
# - Tidak ada input Y; semua sumber di Y=0
# - Tombol "Tambah Titik" untuk menambah ke list
# - Tombol "Hapus Semua" dan "Plot"
# -----------------------------------
sources = []  # list sumber global

def add_point():
    """Tambah titik sumber (x, z, rho). y diabaikan (dipakai 0)."""
    try:
        x_val = float(entry_x.get())
        z_val = float(entry_z.get())
        rho_val = float(entry_rho.get())

        if z_val <= 0:
            messagebox.showerror("Input error", "Nilai z (kedalaman) harus > 0")
            return
        if rho_val == 0:
            messagebox.showerror("Input error", "Nilai rho tidak boleh 0")
            return

        sources.append((x_val, z_val, rho_val))
        listbox.insert(tk.END, f"x={x_val:.1f} m, z={z_val:.1f} m, ρ={rho_val:.0f} kg/m³")

        # Kosongkan entry setelah tambah
        entry_x.delete(0, tk.END)
        entry_z.delete(0, tk.END)
        entry_rho.delete(0, tk.END)
    except ValueError:
        messagebox.showerror("Input error", "Masukkan nilai numerik yang valid")

def clear_points():
    """Hapus semua titik dari daftar."""
    sources.clear()
    listbox.delete(0, tk.END)

def on_plot():
    """Cek minimal 1 sumber lalu plot."""
    if not sources:
        messagebox.showinfo("Info", "Tambahkan minimal satu titik sumber terlebih dahulu.")
        return
    plot_gravity(sources)

# -----------------------------------
# Buat GUI
# -----------------------------------
root = tk.Tk()
root.title("Forward Modelling Gravitasi (Multi Point Mass)")

ttk.Label(root, text="Input parameter titik sumber (Y diabaikan; sources berada di Y=0):").grid(row=0, column=0, columnspan=2, pady=8)

tk.Label(root, text="x (m):").grid(row=1, column=0, sticky="e")
entry_x = ttk.Entry(root, width=20)
entry_x.grid(row=1, column=1, padx=4, pady=2)

tk.Label(root, text="z (kedalaman, m):").grid(row=2, column=0, sticky="e")
entry_z = ttk.Entry(root, width=20)
entry_z.grid(row=2, column=1, padx=4, pady=2)

tk.Label(root, text="ρ (kg/m³):").grid(row=3, column=0, sticky="e")
entry_rho = ttk.Entry(root, width=20)
entry_rho.grid(row=3, column=1, padx=4, pady=2)

btn_add = ttk.Button(root, text="Tambah Titik", command=add_point)
btn_add.grid(row=4, column=0, columnspan=2, pady=6)

listbox = tk.Listbox(root, width=45, height=6)
listbox.grid(row=5, column=0, columnspan=2, pady=6)

btn_clear = ttk.Button(root, text="Hapus Semua", command=clear_points)
btn_clear.grid(row=6, column=0, pady=6)

btn_plot = ttk.Button(root, text="Plot", command=on_plot)
btn_plot.grid(row=6, column=1, pady=6)

root.mainloop()
