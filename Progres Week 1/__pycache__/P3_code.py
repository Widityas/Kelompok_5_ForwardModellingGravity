# FORWARD MODELLING GRAVITASI (INTERAKTIF, MULTI-SUMBER)
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os
matplotlib.use("TkAgg")

# Global storage
sources = []      # list: (name, x, z, rho)
cbar = None       # colorbar global
G = 6.67430e-11   # gravitational constant

# Physics: point-mass like anomaly (approx)
def gravity_anomaly_xy(x, y, z, rho):
    # returns g_z in mGal
    r3 = (x**2 + y**2 + z**2) ** 1.5
    r3 = np.where(r3 == 0, 1e-20, r3)
    return G * rho * z / r3 * 1e5

# Update / Draw Plot
def update_plot():
    global cbar, fig, ax_map, ax_profile

    # clear axes
    ax_map.cla()
    ax_profile.cla()

    # if no sources, show text and return
    if not sources:
        ax_map.text(0.5, 0.5, "Belum ada sumber ditambahkan",
                    ha='center', va='center', transform=ax_map.transAxes,
                    fontsize=14, color='gray')
        ax_map.set_xticks([])
        ax_map.set_yticks([])
        canvas.draw_idle()
        return

    # Grid X-Y for map (world coordinates)
    x = np.linspace(-200, 200, 600)
    y = np.linspace(-200, 200, 600)
    X, Y = np.meshgrid(x, y)
    Z_total = np.zeros_like(X)

    # superposition of contributions (assume sources at y=0 plane)
    for (_, x0, z0, rho0) in sources:
        Z_total += gravity_anomaly_xy(X - x0, Y, z0, rho0)

    # profile along y=0
    g_profile = np.zeros_like(x)
    for (_, x0, z0, rho0) in sources:
        g_profile += gravity_anomaly_xy(x - x0, 0, z0, rho0)

    # symmetric color limits
    vmax = np.max(np.abs(Z_total))
    vmin = -vmax if vmax != 0 else -1e-12

    # masks for positive/negative if you want different mapping (we keep same colormap)
    pos_mask = np.ma.masked_where(Z_total <= 0, Z_total)
    neg_mask = np.ma.masked_where(Z_total >= 0, Z_total)

    # Map plot
    im_pos = ax_map.imshow(pos_mask, extent=[x.min(), x.max(), y.min(), y.max()],
                           origin='lower', cmap='viridis', vmin=0, vmax=vmax)
    im_neg = ax_map.imshow(neg_mask, extent=[x.min(), x.max(), y.min(), y.max()],
                           origin='lower', cmap='viridis', vmin=vmin, vmax=0)

    ax_map.set_title("Gravity anomaly map (g_z) [mGal]")
    ax_map.set_xlabel("X (m)")
    ax_map.set_ylabel("Y (m)")

    # plot sources
    for idx, (name, x0, z0, rho0) in enumerate(sources, start=1):
        ax_map.scatter(x0, 0, color='black', s=40, zorder=5)
        # label near the marker
        ax_map.text(x0 + 5, 5,
                    f"{name}\nx={x0:.1f}, z={z0:.1f}, ρ={rho0:.0f}",
                    color='white', fontsize=8, weight='bold',
                    zorder=6, bbox=dict(facecolor='black', alpha=0.0, pad=0))

    # single colorbar: remove existing then add new
    if cbar is not None:
        try:
            cbar.remove()
        except Exception:
            pass
        cbar = None

    norm = plt.Normalize(vmin=vmin, vmax=vmax)
    mappable = plt.cm.ScalarMappable(norm=norm, cmap='viridis')
    cbar = fig.colorbar(mappable, ax=ax_map, fraction=0.046, pad=0.04)
    cbar.set_label("g_z (mGal)")

    # profile plot
    ax_profile.plot(x, g_profile, color='purple', linewidth=2)
    ax_profile.set_title("g_z profile along X axis (Y=0)")
    ax_profile.set_xlabel("X (m)")
    ax_profile.set_ylabel("g_z (mGal)")
    ax_profile.grid(True, linestyle="--", alpha=0.5)
    ax_profile.set_ylim(bottom=min(0, np.min(g_profile)))

    # force redraw
    canvas.draw_idle()

# GUI button functions
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

def save_plot():
    # Ask file path
    fname = filedialog.asksaveasfilename(defaultextension=".png",
                                         filetypes=[("PNG image","*.png"), ("All files","*.*")],
                                         title="Save plot as...")
    if not fname:
        return
    try:
        fig.savefig(fname, dpi=150)
        messagebox.showinfo("Saved", f"Saved figure to:\n{fname}")
    except Exception as e:
        messagebox.showerror("Error", f"Gagal menyimpan: {e}")

# Responsive resizing: resize figure to fit right_frame
def on_right_configure(event):
    # event.width/height are widget pixels
    w_px = event.width
    h_px = event.height
    dpi = fig.get_dpi()
    # convert pixels to inches for figure size
    w_in = max(4, w_px / dpi)
    h_in = max(3, h_px / dpi)
    # set fig size and redraw
    fig.set_size_inches(w_in, h_in, forward=True)
    canvas.draw_idle()

# Build GUI
root = tk.Tk()
root.title("Forward Modelling Gravitasi (Interaktif, Multi-Sumber)")

# FULLSCREEN DINONAKTIFKAN KARENA MENGUNCI WINDOWS
try:
    root.state("zoomed")       # maximize window, masih bisa resize dan close
except Exception:
    pass

# configure grid: left narrow, right wide
root.grid_columnconfigure(0, weight=0)   # left column fixed-ish
root.grid_columnconfigure(1, weight=1)   # right column takes remaining space
root.grid_rowconfigure(0, weight=1)

# LEFT panel (controls) — keep narrow
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

ttk.Button(frame_left, text="Tambah", command=add_point).grid(row=5, column=0, columnspan=2, pady=(6,2))
ttk.Button(frame_left, text="Update", command=update_selected).grid(row=6, column=0, columnspan=2)
ttk.Button(frame_left, text="Hapus Terpilih", command=delete_selected).grid(row=7, column=0, columnspan=2)
ttk.Button(frame_left, text="Clear Semua", command=clear_points).grid(row=8, column=0, columnspan=2, pady=4)
ttk.Button(frame_left, text="Save PNG", command=save_plot).grid(row=9, column=0, columnspan=2, pady=(8,2))

# listbox area
listbox = tk.Listbox(frame_left, width=30, height=12)
listbox.grid(row=10, column=0, columnspan=2, pady=(8,2))
listbox.bind("<<ListboxSelect>>", on_select)

# RIGHT panel (plot) — takes all remaining space
frame_right = ttk.Frame(root)
frame_right.grid(row=0, column=1, sticky="nsew")
frame_right.grid_rowconfigure(0, weight=1)
frame_right.grid_columnconfigure(0, weight=1)

# create figure and axes using GridSpec for better control
fig = plt.figure(constrained_layout=True)
gs = fig.add_gridspec(2, 1, height_ratios=[2, 1])
ax_map = fig.add_subplot(gs[0])
ax_profile = fig.add_subplot(gs[1])

canvas = FigureCanvasTkAgg(fig, master=frame_right)
canvas_widget = canvas.get_tk_widget()
canvas_widget.pack(fill="both", expand=True)

# Bind configure of frame_right to adjust figure size for true fill
frame_right.bind("<Configure>", on_right_configure)

# initial draw
update_plot()

# Allow 'Esc' to quit fullscreen / close app
def on_key(event):
    if event.keysym == 'Escape':
        # Exit fullscreen if in fullscreen, otherwise quit
        try:
            root.attributes("-fullscreen", False)
        except Exception:
            pass

root.bind("<Key>", on_key)

# Start GUI
root.mainloop()