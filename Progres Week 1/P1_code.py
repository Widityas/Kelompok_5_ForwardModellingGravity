import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import matplotlib.pyplot as plt

# Fungsi menghitung anomali gravitasi sederhana
def gravity_anomaly(x, y, z, rho):
    G = 6.67430e-11  # konstanta gravitasi (m^3 kg^-1 s^-2)
    return G * rho * z / (x**2 + y**2 + z**2)**1.5 * 1e5  # hasil dalam mGal

# Fungsi untuk membuat peta dan grafik anomali gravitasi
def plot_gravity(x0, y0, z0, rho0):
    # Grid koordinat
    x = np.linspace(-100, 100, 300)
    y = np.linspace(-100, 100, 300)
    X, Y = np.meshgrid(x, y)

    # Hitung nilai anomali
    Z = gravity_anomaly(X - x0, Y - y0, z0, rho0)

    # Membuat figure dan axes
    fig, axs = plt.subplots(2, 1, figsize=(9, 9), gridspec_kw={'height_ratios': [3, 1]})

    # Batas warna (simetris agar terlihat + dan -)
    vmax = np.max(np.abs(Z))
    vmin = -vmax

    # Peta kontur anomali gravitasi
    im = axs[0].imshow(Z, extent=[-100, 100, -100, 100],
                       origin='lower', cmap='viridis', vmin=vmin, vmax=vmax)

    # Tambahkan titik sumber dan label
    axs[0].scatter(x0, y0, color='black', s=50)
    axs[0].text(x0 + 5, y0 + 5, f"x={x0:.1f} y={y0:.1f} z={z0:.1f}",
                color='white', fontsize=9, weight='bold', ha='left', va='bottom')

    axs[0].set_title("Gravity anomaly map (g_z) [mGal]", fontsize=12)
    axs[0].set_xlabel("X (m)")
    axs[0].set_ylabel("Y (m)")

    # Dua colorbar: positif dan negatif
    # Pisahkan peta menjadi dua mask: positif & negatif
    pos_mask = np.ma.masked_where(Z <= 0, Z)
    neg_mask = np.ma.masked_where(Z >= 0, Z)

    # Tambahkan overlay untuk positif dan negatif
    axs[0].imshow(pos_mask, extent=[-100, 100, -100, 100], origin='lower', cmap='viridis', vmin=0, vmax=vmax)
    axs[0].imshow(neg_mask, extent=[-100, 100, -100, 100], origin='lower', cmap='viridis', vmin=vmin, vmax=0)


    # Colorbar positif
    cbar_pos = fig.colorbar(plt.cm.ScalarMappable(cmap='viridis', norm=plt.Normalize(vmin=0, vmax=vmax)),
                            ax=axs[0], fraction=0.046, pad=0.04)
    cbar_pos.set_label('Positive anomaly (mGal)')
    # Colorbar negatif
    cbar_neg = fig.colorbar(plt.cm.ScalarMappable(cmap='viridis', norm=plt.Normalize(vmin=vmin, vmax=0)),
                            ax=axs[0], fraction=0.046, pad=0.12)
    cbar_neg.set_label('Negative anomaly (mGal)')

    # Grafik profil g_z di sepanjang X (y = 0)
    g_z_profile = gravity_anomaly(x - x0, 0 - y0, z0, rho0)
    axs[1].plot(x, g_z_profile, color='purple', linewidth=2)
    axs[1].set_title("g_z profile along X axis")
    axs[1].set_xlabel("X (m)")
    axs[1].set_ylabel("g_z (mGal)")
    axs[1].grid(True, linestyle="--", alpha=0.5)
    axs[1].set_ylim(bottom=min(0, np.min(g_z_profile)))

    plt.tight_layout()
    plt.show()

# Fungsi tombol "Plot"
def on_plot():
    try:
        x = float(entry_x.get())
        y = float(entry_y.get())
        z = float(entry_z.get())
        rho = float(entry_rho.get())

        if z <= 0:
            messagebox.showerror("Input error", "Nilai z (kedalaman) harus > 0")
            return
        if rho <= 0:
            messagebox.showerror("Input error", "Nilai rho (densitas) harus > 0")
            return

        plot_gravity(x, y, z, rho)
    except ValueError:
        messagebox.showerror("Input error", "Masukkan nilai numerik yang valid untuk semua input")

# GUI utama
root = tk.Tk()
root.title("Forward Modelling Gravitasi Sederhana")
ttk.Label(root, text="Input koordinat dan parameter:").grid(row=0, column=0, columnspan=2, pady=10)

ttk.Label(root, text="Nilai x (m):").grid(row=1, column=0, sticky="e")
entry_x = ttk.Entry(root)
entry_x.grid(row=1, column=1)

ttk.Label(root, text="Nilai y (m):").grid(row=2, column=0, sticky="e")
entry_y = ttk.Entry(root)
entry_y.grid(row=2, column=1)

ttk.Label(root, text="Nilai z (kedalaman, m):").grid(row=3, column=0, sticky="e")
entry_z = ttk.Entry(root)
entry_z.grid(row=3, column=1)

ttk.Label(root, text="Nilai rho (densitas, kg/m³):").grid(row=4, column=0, sticky="e")
entry_rho = ttk.Entry(root)
entry_rho.grid(row=4, column=1)

btn_plot = ttk.Button(root, text="Plot", command=on_plot)
btn_plot.grid(row=5, column=0, columnspan=2, pady=15)

root.mainloop()
