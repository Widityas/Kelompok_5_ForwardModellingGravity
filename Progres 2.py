import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import matplotlib.pyplot as plt

# Fungsi menghitung anomali gravitasi untuk sphere (dengan density rho dan radius r)
# Ini menggunakan formula untuk gravitasi dari sphere seragam
def gravity_anomaly(x, y, z, rho, r):
    G = 6.67430e-11  # konstanta gravitasi (m^3 kg^-1 s^-2)
    mass = (4/3) * np.pi * r**3 * rho  # Hitung massa dari density dan radius
    r_squared = x**2 + y**2 + z**2
    return G * mass * z / (r_squared)**1.5 * 1e5  # hasil dalam mGal

# Fungsi untuk membuat peta dan grafik anomali gravitasi dengan multiple titik
# points adalah list of tuples (x, y, z, rho, r)
def plot_gravity(points):
    # Grid koordinat untuk plot (dari -100 sampai 100 meter)
    x = np.linspace(-100, 100, 300)
    y = np.linspace(-100, 100, 300)
    X, Y = np.meshgrid(x, y)

    # Inisialisasi array Z sebagai nol untuk menyimpan total anomali
    Z = np.zeros_like(X)

    # Hitung total anomali dari semua titik (superposisi linier)
    for x0, y0, z0, rho, r in points:
        Z += gravity_anomaly(X - x0, Y - y0, z0, rho, r)

    # Membuat figure dengan 2 subplot: atas untuk map, bawah untuk profil
    fig, axs = plt.subplots(2, 1, figsize=(9, 9), gridspec_kw={'height_ratios': [3, 1]})

    # Tentukan batas warna simetris berdasarkan nilai maks absolut Z
    vmax = np.max(np.abs(Z))
    vmin = -vmax

    # Plot peta anomali menggunakan imshow dengan colormap viridis (biru ke kuning)
    im = axs[0].imshow(Z, extent=[-100, 100, -100, 100],
                       origin='lower', cmap='viridis', vmin=vmin, vmax=vmax)

    # Tambahkan scatter plot untuk titik-titik sumber dan label
    for i, (x0, y0, z0, rho, r) in enumerate(points):
        axs[0].scatter(x0, y0, color='black', s=50)  
        axs[0].text(x0 + 5, y0 + 5, f"P{i+1}: x={x0:.1f} y={y0:.1f} z={z0:.1f} rho={rho:.0f} r={r:.1f}",
                    color='white', fontsize=8, weight='bold', ha='left', va='bottom',
                    bbox=dict(boxstyle="round,pad=0.3", facecolor='black', alpha=0.7))

    # Set judul dan label sumbu untuk map
    axs[0].set_title("Gravity anomaly map (g_z) [mGal]", fontsize=12)
    axs[0].set_xlabel("X (m)")
    axs[0].set_ylabel("Y (m)")

    # Tambahkan satu colorbar simetris (menghilangkan colorbar ganda sebelumnya)
    cbar = fig.colorbar(im, ax=axs[0], fraction=0.046, pad=0.04)
    cbar.set_label('Anomaly (mGal)')

    # Tambahkan scalebar manual (bar skala jarak) di pojok kiri bawah
    scale_length = 50  # Panjang scalebar dalam meter
    axs[0].plot([-90, -90 + scale_length], [-90, -90], color='black', linewidth=3)
    axs[0].text(-90 + scale_length/2, -95, f'{scale_length} m', ha='center', va='top', fontsize=10, color='black')

    # Plot profil g_z sepanjang sumbu X (y=0) - total anomali
    g_z_profile = np.zeros_like(x)
    for x0, y0, z0, rho, r in points:
        g_z_profile += gravity_anomaly(x - x0, 0 - y0, z0, rho, r)
    axs[1].plot(x, g_z_profile, color='purple', linewidth=2)
    axs[1].set_title("g_z profile along X axis (y=0)")
    axs[1].set_xlabel("X (m)")
    axs[1].set_ylabel("g_z (mGal)")
    axs[1].grid(True, linestyle="--", alpha=0.5)
    axs[1].set_ylim(vmin, vmax) 

    # Atur layout dan tampilkan plot
    plt.tight_layout()
    plt.show()
    plt.close(fig)  # Tutup figure untuk menghindari memory leak

# Fungsi untuk tombol "Plot" - validasi input dan panggil plot_gravity
def on_plot():
    points = []  # List untuk menyimpan titik-titik valid
    for i in range(5):  # Loop untuk 5 titik input
        try:
            # Ambil nilai dari entry dan konversi ke float
            x = float(entries_x[i].get())
            y = float(entries_y[i].get())
            z = float(entries_z[i].get())
            rho = float(entries_rho[i].get())
            r = float(entries_r[i].get())
            # Validasi: z, rho, r harus > 0
            if z <= 0 or rho <= 0 or r <= 0:
                messagebox.showerror("Input error", f"Untuk Titik {i+1}: z > 0, rho > 0, r > 0")
                return
            points.append((x, y, z, rho, r))  # Tambahkan ke list jika valid
        except ValueError:
            # Jika entry kosong atau bukan angka, skip titik ini
            continue
    # Jika tidak ada titik valid, tampilkan error
    if not points:
        messagebox.showerror("Input error", "Masukkan setidaknya satu titik yang valid")
        return
    # Panggil fungsi plot
    plot_gravity(points)

# Bagian GUI utama - menggunakan Tkinter untuk interface tabel
root = tk.Tk()
root.title("Gravity Anomaly Calculator")
root.geometry("800x400")  
root.resizable(False, False)  

# Label instruksi
ttk.Label(root, text="Input titik-titik (biarkan kosong jika tidak digunakan):").grid(row=0, column=0, columnspan=6, pady=10)

# Header tabel (kolom untuk setiap parameter)
ttk.Label(root, text="Titik").grid(row=1, column=0)
ttk.Label(root, text="x (m)").grid(row=1, column=1)
ttk.Label(root, text="y (m)").grid(row=1, column=2)
ttk.Label(root, text="z (kedalaman, m)").grid(row=1, column=3)
ttk.Label(root, text="rho (densitas, kg/m³)").grid(row=1, column=4)
ttk.Label(root, text="r (radius, m)").grid(row=1, column=5)

# List untuk menyimpan entry widgets
entries_x = []
entries_y = []
entries_z = []
entries_rho = []
entries_r = []

# Loop untuk membuat 5 baris input (tabel)
for i in range(5):
    # Label nomor titik
    ttk.Label(root, text=f"{i+1}").grid(row=i+2, column=0, sticky="e", padx=5)
    
    # Entry untuk x
    entry_x = ttk.Entry(root, width=10)
    entry_x.grid(row=i+2, column=1, padx=5)
    entries_x.append(entry_x)
    
    # Entry untuk y
    entry_y = ttk.Entry(root, width=10)
    entry_y.grid(row=i+2, column=2, padx=5)
    entries_y.append(entry_y)
    
    # Entry untuk z
    entry_z = ttk.Entry(root, width=10)
    entry_z.grid(row=i+2, column=3, padx=5)
    entries_z.append(entry_z)
    
    # Entry untuk rho
    entry_rho = ttk.Entry(root, width=10)
    entry_rho.grid(row=i+2, column=4, padx=5)
    entries_rho.append(entry_rho)
    
    # Entry untuk r
    entry_r = ttk.Entry(root, width=10)
    entry_r.grid(row=i+2, column=5, padx=5)
    entries_r.append(entry_r)

# Isi default values untuk 3 titik pertama (contoh)
entries_x[0].insert(0, "0")
entries_y[0].insert(0, "0")
entries_z[0].insert(0, "10")
entries_rho[0].insert(0, "2000")
entries_r[0].insert(0, "5")

entries_x[1].insert(0, "10")
entries_y[1].insert(0, "0")
entries_z[1].insert(0, "10")
entries_rho[1].insert(0, "3000")
entries_r[1].insert(0, "5")

entries_x[2].insert(0, "20")
entries_y[2].insert(0, "0")
entries_z[2].insert(0, "10")
entries_rho[2].insert(0, "2500")
entries_r[2].insert(0, "5")

# Tombol untuk plot
btn_plot = ttk.Button(root, text="Plot Gravity Anomaly", command=on_plot)
btn_plot.grid(row=7, column=0, columnspan=6, pady=15)

# Jalankan main loop GUI
root.mainloop()

