# Forward Gravity Modelling 2D  
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
matplotlib.use("TkAgg")


# Variabel global & konstanta
sources = []         # daftar tuple: (nama, x, z, rho)
cbar = None
G = 6.67430e-11      # konstanta gravitasi (SI)
# Jika ingin range warna tetap, isi ini; jika tidak biarkan None untuk autoscale
COLOR_MIN = None
COLOR_MAX = None


# Fisika: pendekatan anomali titik massa
# mengembalikan g_z dalam satuan mGal
def gravity_anomaly_xy(x, y, z, rho):
    r3 = (x**2 + y**2 + z**2) ** 1.5
    r3 = np.where(r3 == 0, 1e-20, r3)  # mencegah pembagian dengan nol
    return G * rho * z / r3 * 1e5


# Memperbarui / Menggambar Plot
def update_plot():
    global cbar, fig, ax_map, ax_profile

    ax_map.cla()
    ax_profile.cla()

    # Jika belum ada sumber, tampilkan pesan
    if not sources:
        ax_map.text(0.5, 0.5, "Belum ada sumber ditambahkan",
                    ha='center', va='center', transform=ax_map.transAxes,
                    fontsize=14, color='gray')
        ax_map.set_xticks([]); ax_map.set_yticks([])
        canvas.draw_idle()
        return

    # grid (grid kasar untuk perhitungan model)
    x = np.linspace(-200, 200, 600)
    y = np.linspace(-200, 200, 600)
    X, Y = np.meshgrid(x, y)
    Z_total = np.zeros_like(X)

    # penjumlahan kontribusi semua sumber (superposisi)
    for (_, x0, z0, rho0) in sources:
        Z_total += gravity_anomaly_xy(X - x0, Y, z0, rho0)

    # profil anomali pada garis y=0
    g_profile = np.zeros_like(x)
    for (_, x0, z0, rho0) in sources:
        g_profile += gravity_anomaly_xy(x - x0, 0, z0, rho0)

    # autoscale vmin/vmax kecuali user menentukan sendiri
    if COLOR_MIN is None or COLOR_MAX is None:
        vmin = np.min(Z_total)
        vmax = np.max(Z_total)
        if vmin == vmax:
            vmin -= 1e-12; vmax += 1e-12
    else:
        vmin = COLOR_MIN
        vmax = COLOR_MAX

    # heatmap tunggal (tanpa pemisahan pos/neg), tampilkan interpolasi halus
    im = ax_map.imshow(Z_total, extent=[x.min(), x.max(), y.min(), y.max()],
                      origin='lower', cmap='viridis', interpolation='bicubic',
                      vmin=vmin, vmax=vmax)

    ax_map.set_title("Peta Anomali Gravitasi (g_z) [mGal]")
    ax_map.set_xlabel("X (m)"); ax_map.set_ylabel("Y (m)")

    # gambar posisi sumber
    for (name, x0, z0, rho0) in sources:
        ax_map.scatter(x0, 0, color='black', s=40, zorder=5)
        ax_map.text(x0 + 5, 5,
                    f"{name}\nx={x0:.1f}, z={z0:.1f}, ρ={rho0:.0f}",
                    color='white', fontsize=8, weight='bold',
                    zorder=6, bbox=dict(facecolor='black', alpha=0.0, pad=0))

    # colorbar tunggal
    if cbar is not None:
        try:
            cbar.remove()
        except Exception:
            pass
        cbar = None

    cbar = fig.colorbar(im, ax=ax_map, fraction=0.046, pad=0.04)
    cbar.set_label("g_z (mGal)")

    # plot profil
    ax_profile.plot(x, g_profile, color='purple', linewidth=2)
    ax_profile.set_title("Profil g_z Sepanjang Sumbu X (Y=0)")
    ax_profile.set_xlabel("X (m)"); ax_profile.set_ylabel("g_z (mGal)")
    ax_profile.grid(True, linestyle="--", alpha=0.5)
    ax_profile.set_ylim(bottom=min(0, np.min(g_profile)))

    canvas.draw_idle()


# Fungsi tombol GUI
def clear_inputs():
    entry_name.delete(0, tk.END)
    entry_x.delete(0, tk.END)
    entry_z.delete(0, tk.END)
    entry_rho.delete(0, tk.END)

def add_point():
    try:
        name_val = entry_name.get().strip() or f"p{len(sources)+1}"
        x_val = float(entry_x.get())
        z_val = float(entry_z.get())
        rho_val = float(entry_rho.get())

        # validasi kedalaman
        if z_val <= 0:
            messagebox.showerror("Input error", "Nilai z (kedalaman) harus > 0")
            return
        # validasi densitas
        if rho_val == 0:
            messagebox.showerror("Input error", "Nilai ρ tidak boleh 0")
            return

        # tambah sumber ke daftar
        sources.append((name_val, x_val, z_val, rho_val))
        listbox.insert(tk.END, f"{name_val}: x={x_val:.1f}, z={z_val:.1f}, ρ={rho_val:.0f}")
        clear_inputs()
        update_plot()

    except ValueError:
        messagebox.showerror("Input error", "Masukkan angka yang valid.")

def delete_selected():
    sel = listbox.curselection()
    if not sel:
        messagebox.showerror("Error", "Pilih item dulu!")
        return
    idx = sel[0]
    sources.pop(idx)
    listbox.delete(idx)
    update_plot()

def clear_points():
    sources.clear()  # hapus semua sumber
    listbox.delete(0, tk.END)
    update_plot()

def on_select(event):
    sel = listbox.curselection()
    if not sel:
        return
    idx = sel[0]
    name, x0, z0, rho0 = sources[idx]

    # tampilkan data sumber pada input
    entry_name.delete(0, tk.END); entry_name.insert(0, str(name))
    entry_x.delete(0, tk.END); entry_x.insert(0, str(x0))
    entry_z.delete(0, tk.END); entry_z.insert(0, str(z0))
    entry_rho.delete(0, tk.END); entry_rho.insert(0, str(rho0))

def update_selected():
    sel = listbox.curselection()
    if not sel:
        messagebox.showerror("Error", "Pilih item dulu!")
        return

    idx = sel[0]
    try:
        name_val = entry_name.get().strip() or f"p{idx+1}"
        x_val = float(entry_x.get())
        z_val = float(entry_z.get())
        rho_val = float(entry_rho.get())
    except ValueError:
        messagebox.showerror("Input error", "Masukkan angka valid!")
        return

    # perbarui sumber
    sources[idx] = (name_val, x_val, z_val, rho_val)
    listbox.delete(idx)
    listbox.insert(idx, f"{name_val}: x={x_val:.1f}, z={z_val:.1f}, ρ={rho_val:.0f}")
    update_plot()

def save_plot():
    fname = filedialog.asksaveasfilename(defaultextension=".png",
                                         filetypes=[("PNG image",".png"), ("All files",".*")],
                                         title="Save plot as...")
    if not fname:
        return
    try:
        fig.savefig(fname, dpi=150)
        messagebox.showinfo("Saved", f"Menyimpan gambar ke:\n{fname}")
    except Exception as e:
        messagebox.showerror("Error", f"Gagal menyimpan: {e}")


# Penyesuaian ukuran plot ketika frame kanan di-resize
def on_right_configure(event):
    try:
        dpi = fig.get_dpi()
        w_in = max(4, event.width / dpi)
        h_in = max(3, event.height / dpi)
        fig.set_size_inches(w_in, h_in, forward=True)
        canvas.draw_idle()
    except Exception:
        pass


# Membangun GUI
root = tk.Tk()
root.title("Forward Modelling Gravitasi (Interaktif, Multi-Sumber)")

# buka jendela dengan mode diperbesar
try:
    root.state("zoomed")
except Exception:
    pass

# pengaturan layout grid
root.grid_columnconfigure(0, weight=0)
root.grid_columnconfigure(1, weight=1)
root.grid_rowconfigure(0, weight=1)

# frame input kiri
frame_left = ttk.Frame(root, padding=8)
frame_left.grid(row=0, column=0, sticky="ns")

ttk.Label(frame_left, text="Input Titik Sumber").grid(row=0, column=0, columnspan=2, pady=4)

ttk.Label(frame_left, text="Nama:").grid(row=1, column=0, sticky="e")
entry_name = ttk.Entry(frame_left, width=18); entry_name.grid(row=1, column=1, pady=2)

ttk.Label(frame_left, text="x (m):").grid(row=2, column=0, sticky="e")
entry_x = ttk.Entry(frame_left, width=18); entry_x.grid(row=2, column=1, pady=2)

ttk.Label(frame_left, text="z (m, kedalaman):").grid(row=3, column=0, sticky="e")
entry_z = ttk.Entry(frame_left, width=18); entry_z.grid(row=3, column=1, pady=2)

ttk.Label(frame_left, text="ρ (kg/m³):").grid(row=4, column=0, sticky="e")
entry_rho = ttk.Entry(frame_left, width=18); entry_rho.grid(row=4, column=1, pady=2)

ttk.Button(frame_left, text="Tambah", command=add_point).grid(row=5, column=0, columnspan=2, pady=(6,2))
ttk.Button(frame_left, text="Update", command=update_selected).grid(row=6, column=0, columnspan=2)
ttk.Button(frame_left, text="Hapus Terpilih", command=delete_selected).grid(row=7, column=0, columnspan=2)
ttk.Button(frame_left, text="Clear Semua", command=clear_points).grid(row=8, column=0, columnspan=2, pady=4)
ttk.Button(frame_left, text="Save PNG", command=save_plot).grid(row=9, column=0, columnspan=2, pady=(6,2))

listbox = tk.Listbox(frame_left, width=32, height=12)
listbox.grid(row=10, column=0, columnspan=2, pady=(8,2))
listbox.bind("<<ListboxSelect>>", on_select)

# frame plot kanan
frame_right = ttk.Frame(root)
frame_right.grid(row=0, column=1, sticky="nsew")
frame_right.grid_rowconfigure(0, weight=1)
frame_right.grid_columnconfigure(0, weight=1)

fig = plt.figure(constrained_layout=True)
gs = fig.add_gridspec(2, 1, height_ratios=[2, 1])
ax_map = fig.add_subplot(gs[0])
ax_profile = fig.add_subplot(gs[1])

canvas = FigureCanvasTkAgg(fig, master=frame_right)
canvas_widget = canvas.get_tk_widget()
canvas_widget.pack(fill="both", expand=True)

frame_right.bind("<Configure>", on_right_configure)

# gambar pertama kali
update_plot()

# shortcut keyboard: ESC untuk keluar dari fullscreen
def on_key(event):
    if event.keysym == 'Escape':
        try:
            root.attributes("-fullscreen", False)
        except Exception:
            pass

root.bind("<Key>", on_key)

root.mainloop()