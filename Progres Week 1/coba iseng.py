# ===============================================================
# FORWARD MODELLING GRAVITASI (INTERAKTIF DALAM SATU JENDELA)
# - import CSV/Excel/TXT
# - save plot & save data
# ===============================================================

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os

# Try importing pandas for easy import; fallback to numpy
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except Exception:
    PANDAS_AVAILABLE = False

# -----------------------------------
# Global variables
# -----------------------------------
sources = []      # list of tuples: (name, x, z, rho)
cbar = None       # colorbar handle
fig = None
axs = None
canvas = None

# -----------------------------------
# Gravity function (vertical component g_z for point mass)
# -----------------------------------
def gravity_anomaly_xy(x, y, z, rho):
    G = 6.67430e-11                     # gravitational constant (SI)
    r3 = (x**2 + y**2 + z**2) ** 1.5
    r3 = np.where(r3 == 0, 1e-20, r3)   # avoid division by zero
    return G * rho * z / r3 * 1e5       # convert to mGal

# -----------------------------------
# Plot update
# -----------------------------------
def update_plot(grid_extent=1000, grid_points=200):
    """Redraw map + profile from current `sources`."""
    global cbar, fig, axs, canvas

    for ax in axs:
        ax.clear()

    if not sources:
        axs[0].text(0.5, 0.5, "Belum ada sumber ditambahkan",
                    ha='center', va='center', fontsize=12, color='gray')
        canvas.draw()
        return

    # Create grid (keep it reasonable by default)
    x = np.linspace(-grid_extent, grid_extent, grid_points)
    y = np.linspace(-grid_extent, grid_extent, grid_points)
    X, Y = np.meshgrid(x, y)
    Z_total = np.zeros_like(X)

    # Sum contributions (assume all sources lie on Y=0 plane)
    for (_, x0, z0, rho0) in sources:
        Z_total += gravity_anomaly_xy(X - x0, Y - 0, z0, rho0)

    # Profile along Y=0
    g_profile = np.zeros_like(x)
    for (_, x0, z0, rho0) in sources:
        g_profile += gravity_anomaly_xy(x - x0, 0, z0, rho0)

    # Plot map
    vmax = np.max(np.abs(Z_total))
    vmin = -vmax if vmax != 0 else -1e-12

    im = axs[0].imshow(Z_total, extent=[x.min(), x.max(), y.min(), y.max()],
                       origin='lower', cmap='viridis', vmin=vmin, vmax=vmax)
    axs[0].set_title("Gravity anomaly map (g_z) [mGal]")
    axs[0].set_xlabel("X (m)")
    axs[0].set_ylabel("Y (m)")

    # Mark sources on map (at Y=0)
    for (name, x0, z0, rho0) in sources:
        axs[0].scatter(x0, 0, color='red', s=40, edgecolor='black', zorder=5)
        axs[0].text(x0 + (grid_extent * 0.02), grid_extent * 0.02,
                    f"{name}\nx={x0:.1f}, z={z0:.1f}\nρ={rho0:.0f}",
                    color='white', fontsize=8, ha='left', va='bottom', weight='bold')

    # Replace colorbar (remove old one first)
    if cbar is not None:
        try:
            cbar.remove()
        except Exception:
            pass
        cbar = None
    cbar = fig.colorbar(im, ax=axs[0], fraction=0.046, pad=0.04)
    cbar.set_label('g_z (mGal)')

    # Profile plot
    axs[1].plot(x, g_profile, color='purple', linewidth=2)
    axs[1].set_title("g_z profile along X axis (Y=0)")
    axs[1].set_xlabel("X (m)")
    axs[1].set_ylabel("g_z (mGal)")
    axs[1].grid(True, linestyle="--", alpha=0.5)

    canvas.draw()

# -----------------------------------
# GUI actions: add / delete / update points
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

def delete_selected():
    if not listbox.curselection():
        messagebox.showerror("Error", "Pilih item dulu!")
        return
    idx = listbox.curselection()[0]
    sources.pop(idx)
    listbox.delete(idx)
    update_plot()

def clear_points():
    sources.clear()
    listbox.delete(0, tk.END)
    update_plot()

def clear_inputs():
    entry_name.delete(0, tk.END)
    entry_x.delete(0, tk.END)
    entry_z.delete(0, tk.END)
    entry_rho.delete(0, tk.END)

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
# Import / Export
# -----------------------------------
def import_file():
    """Import points from CSV / Excel / TXT. Expected columns: optionally name, and x,z,rho."""
    filetypes = [
        ("CSV files", "*.csv"),
        ("Excel files", "*.xls *.xlsx"),
        ("Text files", "*.txt"),
        ("All files", "*.*"),
    ]
    path = filedialog.askopenfilename(title="Open data file", filetypes=filetypes)
    if not path:
        return

    try:
        ext = os.path.splitext(path)[1].lower()
        df = None

        if PANDAS_AVAILABLE:
            if ext in [".xls", ".xlsx"]:
                df = pd.read_excel(path)
            else:
                # read_csv can normally read .csv and many .txt with delimiter autodetect
                df = pd.read_csv(path)
        else:
            # Fallback: try numpy loadtxt for simple whitespace/comma separated files
            try:
                data = np.loadtxt(path, delimiter=None)  # autodetect whitespace/comma
            except Exception:
                # try comma
                data = np.loadtxt(path, delimiter=",")
            # data is 2D array
            if data.ndim == 1:
                data = data[np.newaxis, :]
            # assume columns x,z,rho or name,x,z,rho
            if data.shape[1] == 3:
                # x,z,rho -> create names automatically
                rows = []
                for i, row in enumerate(data):
                    rows.append(("pt"+str(i+1), float(row[0]), float(row[1]), float(row[2])))
            elif data.shape[1] >= 4:
                rows = []
                for i, row in enumerate(data):
                    rows.append((str(row[0]), float(row[1]), float(row[2]), float(row[3])))
            else:
                raise ValueError("File format tidak dikenali (butuh 3 atau 4 kolom).")

            # append rows
            added = 0
            for r in rows:
                name_val, x_val, z_val, rho_val = r
                sources.append((str(name_val), x_val, z_val, rho_val))
                listbox.insert(tk.END, f"{name_val}: x={x_val:.1f}, z={z_val:.1f}, ρ={rho_val:.0f}")
                added += 1
            update_plot()
            messagebox.showinfo("Import selesai", f"Berhasil menambahkan {added} titik dari file.")
            return

        # If we have pandas.DataFrame, normalize columns
        if df is None:
            raise ValueError("Gagal membaca file.")
        # Normalize column names (lower)
        cols = [c.strip().lower() for c in df.columns]
        # Try to find columns for x, z, rho and optional name
        col_x = None; col_z = None; col_rho = None; col_name = None
        for c, original in zip(cols, df.columns):
            if c in ("x", "easting", "east", "longitude", "lon"):
                col_x = original
            elif c in ("z", "depth", "upward", "height"):
                col_z = original
            elif c in ("rho", "density", "dens"):
                col_rho = original
            elif c in ("name", "id", "label"):
                col_name = original
        # If not found, try positional fallback
        if col_x is None or col_z is None or col_rho is None:
            # try positional columns
            if df.shape[1] >= 3:
                # assume order: x, z, rho or name,x,z,rho
                if df.shape[1] == 3:
                    col_x = df.columns[0]; col_z = df.columns[1]; col_rho = df.columns[2]
                else:
                    col_name = df.columns[0]; col_x = df.columns[1]; col_z = df.columns[2]; col_rho = df.columns[3]
            else:
                raise ValueError("File harus memiliki minimal 3 kolom (x, z, rho).")

        added = 0
        for _, row in df.iterrows():
            name_val = str(row[col_name]) if col_name is not None else f"pt{len(sources)+1}"
            x_val = float(row[col_x])
            z_val = float(row[col_z])
            rho_val = float(row[col_rho])
            sources.append((name_val, x_val, z_val, rho_val))
            listbox.insert(tk.END, f"{name_val}: x={x_val:.1f}, z={z_val:.1f}, ρ={rho_val:.0f}")
            added += 1

        update_plot()
        messagebox.showinfo("Import selesai", f"Berhasil menambahkan {added} titik dari file.")

    except Exception as e:
        messagebox.showerror("Import error", f"Gagal mengimpor file:\n{e}")

def save_plot():
    """Save current figure to image file."""
    global fig
    path = filedialog.asksaveasfilename(defaultextension=".png",
                                        filetypes=[("PNG image", "*.png"), ("JPEG image", "*.jpg"), ("PDF file", "*.pdf")])
    if not path:
        return
    try:
        fig.savefig(path, dpi=300, bbox_inches="tight")
        messagebox.showinfo("Simpan berhasil", f"Plot disimpan ke:\n{path}")
    except Exception as e:
        messagebox.showerror("Save error", f"Gagal menyimpan:\n{e}")

def save_data_csv():
    """Export current sources to CSV."""
    path = filedialog.asksaveasfilename(defaultextension=".csv",
                                        filetypes=[("CSV file", "*.csv")])
    if not path:
        return
    try:
        # write header and rows
        with open(path, "w", encoding="utf-8") as f:
            f.write("name,x,z,rho\n")
            for (name, x, z, rho) in sources:
                f.write(f"{name},{x},{z},{rho}\n")
        messagebox.showinfo("Simpan berhasil", f"Data sumber disimpan ke:\n{path}")
    except Exception as e:
        messagebox.showerror("Save error", f"Gagal menyimpan data:\n{e}")

# -----------------------------------
# Build GUI
# -----------------------------------
root = tk.Tk()
root.title("Forward Modelling Gravitasi (Interaktif)")

# Left frame: input + controls
frame_left = ttk.Frame(root, padding=10)
frame_left.grid(row=0, column=0, sticky="ns")

ttk.Label(frame_left, text="Input Titik Sumber").grid(row=0, column=0, columnspan=2, pady=5)
ttk.Label(frame_left, text="Nama:").grid(row=1, column=0, sticky="e")
entry_name = ttk.Entry(frame_left, width=18); entry_name.grid(row=1, column=1, pady=2)

ttk.Label(frame_left, text="x (m):").grid(row=2, column=0, sticky="e")
entry_x = ttk.Entry(frame_left, width=18); entry_x.grid(row=2, column=1, pady=2)

ttk.Label(frame_left, text="z (m, kedalaman):").grid(row=3, column=0, sticky="e")
entry_z = ttk.Entry(frame_left, width=18); entry_z.grid(row=3, column=1, pady=2)

ttk.Label(frame_left, text="ρ (kg/m³):").grid(row=4, column=0, sticky="e")
entry_rho = ttk.Entry(frame_left, width=18); entry_rho.grid(row=4, column=1, pady=2)

ttk.Button(frame_left, text="Tambah Titik", command=add_point).grid(row=5, column=0, columnspan=2, pady=5)
ttk.Button(frame_left, text="Update Titik", command=update_selected).grid(row=6, column=0, columnspan=2, pady=5)
ttk.Button(frame_left, text="Hapus Titik Terpilih", command=delete_selected).grid(row=7, column=0, columnspan=2, pady=5)
ttk.Button(frame_left, text="Hapus Semua", command=clear_points).grid(row=8, column=0, columnspan=2, pady=5)

# Import / Export buttons
ttk.Separator(frame_left, orient="horizontal").grid(row=9, column=0, columnspan=2, sticky="ew", pady=6)
ttk.Button(frame_left, text="Import dari file (CSV/Excel/TXT)", command=import_file).grid(row=10, column=0, columnspan=2, pady=4)
ttk.Button(frame_left, text="Simpan data (CSV)", command=save_data_csv).grid(row=11, column=0, columnspan=2, pady=4)
ttk.Button(frame_left, text="Simpan plot (PNG/JPG/PDF)", command=save_plot).grid(row=12, column=0, columnspan=2, pady=4)

# Listbox
listbox = tk.Listbox(frame_left, width=60, height=15)
listbox.grid(row=13, column=0, columnspan=2, pady=6)
listbox.bind("<<ListboxSelect>>", on_select)

# Right frame: plot area
frame_right = ttk.Frame(root, padding=8)
frame_right.grid(row=0, column=1)

fig, axs = plt.subplots(2, 1, figsize=(10, 8), gridspec_kw={'height_ratios': [3, 1]})
canvas = FigureCanvasTkAgg(fig, master=frame_right)
canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

# Initial draw
update_plot()

# Run
root.mainloop()