# Forward Gravity Modelling 2D - GUI Variation
# Improved UI features: colormap selector, interpolation toggle, grid resolution,
# import/export sources (CSV/TXT), save figure, persistent single colorbar,
# editable source list, better layout and comments.
# Original local file (for user's reference):
# D:\UGM otw 2028\SEMESTER 3\METODE KOMPUTASI\Metode-Komputasi\Kelompok_5_ForwardModellingGravity\harmonica

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import csv
import os

matplotlib.use("TkAgg")

# -------------------------------
# Configuration / Globals
# -------------------------------
sources = []         # list of tuples: (name, x, z, rho)
cbar = None
G = 6.67430e-11      # gravitational constant (SI)
COLOR_MIN = None
COLOR_MAX = None

# default plotting params
DEFAULT_CMAP = 'viridis'
DEFAULT_INTERP = 'bicubic'  # or 'nearest'

# -------------------------------
# Physics: point-mass vertical component (mGal)
# -------------------------------

def gravity_anomaly_xy(x, y, z, rho):
    """Return g_z in mGal for point mass/density rho at relative offset (x,y,z).

    Note: z should be the vertical separation (obs_z - source_z). If you store
    source.depth as positive down, remember to convert when calling.
    """
    r3 = (x**2 + y**2 + z**2) ** 1.5
    # avoid division by zero singularity by small epsilon
    r3 = np.where(r3 == 0, 1e-20, r3)
    return G * rho * z / r3 * 1e5


# -------------------------------
# Plotting / UI logic
# -------------------------------

def compute_field(resolution, extent=200, interpolation=DEFAULT_INTERP, cmap=DEFAULT_CMAP):
    """Compute grid (X,Y) and total Z_total from current sources.
    resolution: int, number of points per axis
    extent: half-width in meters for both +X and +Y
    returns: x, y, X, Y, Z_total, g_profile
    """
    # create observation grid
    x = np.linspace(-extent, extent, resolution)
    y = np.linspace(-extent, extent, resolution)
    X, Y = np.meshgrid(x, y)
    Z_total = np.zeros_like(X)

    # sum contributions
    for (_, x0, z0, rho0) in sources:
        Z_total += gravity_anomaly_xy(X - x0, Y - 0.0, z0, rho0)

    # profile along y=0
    g_profile = np.zeros_like(x)
    for (_, x0, z0, rho0) in sources:
        g_profile += gravity_anomaly_xy(x - x0, 0.0, z0, rho0)

    return x, y, X, Y, Z_total, g_profile


def update_plot():
    """Refresh matplotlib axes with current sources and UI parameters."""
    global cbar
    ax_map.cla()
    ax_profile.cla()

    if not sources:
        ax_map.text(0.5, 0.5, "Belum ada sumber ditambahkan",
                    ha='center', va='center', transform=ax_map.transAxes,
                    fontsize=14, color='gray')
        ax_map.set_xticks([]); ax_map.set_yticks([])
        canvas.draw_idle()
        return

    # read UI controls
    try:
        res = int(scale_res.get())
        extent = float(entry_extent.get())
    except Exception:
        res = 400
        extent = 200

    cmap = cmap_var.get() or DEFAULT_CMAP
    interp_on = interp_var.get()
    interp = 'bicubic' if interp_on else 'nearest'

    # compute field
    x, y, X, Y, Z_total, g_profile = compute_field(resolution=res, extent=extent,
                                                    interpolation=interp, cmap=cmap)

    # vmin/vmax handling
    if COLOR_MIN is None or COLOR_MAX is None:
        vmin = np.nanmin(Z_total)
        vmax = np.nanmax(Z_total)
        if vmin == vmax:
            vmin -= 1e-12; vmax += 1e-12
    else:
        vmin = COLOR_MIN; vmax = COLOR_MAX

    # draw heatmap
    im = ax_map.imshow(Z_total, extent=[x.min(), x.max(), y.min(), y.max()],
                       origin='lower', cmap=cmap, interpolation=interp,
                       vmin=vmin, vmax=vmax, aspect='auto')

    ax_map.set_title("Peta Anomali Gravitasi (g_z) [mGal]")
    ax_map.set_xlabel("X (m)"); ax_map.set_ylabel("Y (m)")

    # plot sources markers and labels
    for (name, x0, z0, rho0) in sources:
        ax_map.scatter(x0, 0, color='black', s=40, zorder=5)
        ax_map.text(x0 + 0.02 * (x.max()-x.min()), 0.02 * (y.max()-y.min()),
                    f"{name}\nx={x0:.1f}, z={z0:.1f}, ρ={rho0:.0f}",
                    color='white', fontsize=8, weight='bold', zorder=6,
                    bbox=dict(facecolor='black', alpha=0.0, pad=0))

    # persistent single colorbar: remove old then create new
    if cbar is not None:
        try:
            cbar.remove()
        except Exception:
            pass
        cbar = None

    cbar = fig.colorbar(im, ax=ax_map, fraction=0.046, pad=0.04)
    cbar.set_label('g_z (mGal)')

    # profile plot
    ax_profile.plot(x, g_profile, color='purple', linewidth=2)
    ax_profile.set_title("Profil g_z Sepanjang Sumbu X (Y=0)")
    ax_profile.set_xlabel("X (m)"); ax_profile.set_ylabel("g_z (mGal)")
    ax_profile.grid(True, linestyle="--", alpha=0.5)
    ax_profile.set_ylim(bottom=min(0.0, np.nanmin(g_profile)))

    canvas.draw_idle()


# -------------------------------
# File IO: import/export simple CSV format
# CSV format expected: name,x,z,rho  (header optional)
# -------------------------------

def import_sources():
    fname = filedialog.askopenfilename(title='Import sources (CSV/TXT)',
                                       filetypes=[('CSV files','*.csv'), ('Text files','*.txt'), ('All','*.*')])
    if not fname:
        return
    try:
        new = []
        with open(fname, 'r', newline='') as f:
            reader = csv.reader(f)
            for row in reader:
                if not row:
                    continue
                # allow header: detect non-numeric in 2nd column
                try:
                    name = row[0].strip()
                    x = float(row[1]); z = float(row[2]); rho = float(row[3])
                except Exception:
                    # skip header or malformed
                    continue
                new.append((name, x, z, rho))
        if not new:
            messagebox.showwarning('Import', 'Tidak menemukan data sumber yang valid di file.')
            return
        # append to existing list and update listbox
        start = len(sources)
        sources.extend(new)
        for (name,x,z,rho) in new:
            listbox.insert(tk.END, f"{name}: x={x:.1f}, z={z:.1f}, ρ={rho:.0f}")
        update_plot()
        messagebox.showinfo('Import', f'Berhasil mengimpor {len(new)} sumber dari:\n{os.path.basename(fname)}')
    except Exception as e:
        messagebox.showerror('Import error', str(e))


def export_sources():
    if not sources:
        messagebox.showerror('Export', 'Tidak ada sumber untuk diexport.')
        return
    fname = filedialog.asksaveasfilename(defaultextension='.csv', filetypes=[('CSV','*.csv')])
    if not fname:
        return
    try:
        with open(fname, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['name','x','z','rho'])
            for (name,x,z,rho) in sources:
                writer.writerow([name,x,z,rho])
        messagebox.showinfo('Export', f'Saved sources to:\n{fname}')
    except Exception as e:
        messagebox.showerror('Export error', str(e))


# -------------------------------
# UI callbacks for source management
# -------------------------------
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
            messagebox.showerror('Input error', 'Nilai z (kedalaman) harus > 0')
            return
        if rho_val == 0:
            messagebox.showerror('Input error', 'Nilai ρ tidak boleh 0')
            return
        sources.append((name_val, x_val, z_val, rho_val))
        listbox.insert(tk.END, f"{name_val}: x={x_val:.1f}, z={z_val:.1f}, ρ={rho_val:.0f}")
        clear_inputs() 
        update_plot()
    except ValueError:
        messagebox.showerror('Input error', 'Masukkan angka yang valid.')


def delete_selected():
    sel = listbox.curselection()
    if not sel:
        messagebox.showerror('Error', 'Pilih item dulu!')
        return
    idx = sel[0]
    sources.pop(idx)
    listbox.delete(idx)
    update_plot()


def clear_points():
    if messagebox.askyesno('Confirm', 'Hapus semua sumber?'):
        sources.clear()
        listbox.delete(0, tk.END)
        update_plot()


def on_select(event):
    sel = listbox.curselection()
    if not sel:
        return
    idx = sel[0]
    name, x0, z0, rho0 = sources[idx]
    entry_name.delete(0, tk.END); entry_name.insert(0, str(name))
    entry_x.delete(0, tk.END); entry_x.insert(0, str(x0))
    entry_z.delete(0, tk.END); entry_z.insert(0, str(z0))
    entry_rho.delete(0, tk.END); entry_rho.insert(0, str(rho0))


def update_selected():
    sel = listbox.curselection()
    if not sel:
        messagebox.showerror('Error', 'Pilih item dulu!')
        return
    idx = sel[0]
    try:
        name_val = entry_name.get().strip() or f"p{idx+1}"
        x_val = float(entry_x.get())
        z_val = float(entry_z.get())
        rho_val = float(entry_rho.get())
    except ValueError:
        messagebox.showerror('Input error', 'Masukkan angka valid!')
        return
    sources[idx] = (name_val, x_val, z_val, rho_val)
    listbox.delete(idx)
    listbox.insert(idx, f"{name_val}: x={x_val:.1f}, z={z_val:.1f}, ρ={rho_val:.0f}")
    update_plot()


# -------------------------------
# Save figure
# -------------------------------
def save_plot():
    fname = filedialog.asksaveasfilename(defaultextension='.png', filetypes=[('PNG','*.png'),('PDF','*.pdf')])
    if not fname:
        return
    try:
        fig.savefig(fname, dpi=200)
        messagebox.showinfo('Saved', f'Figure saved to:\n{fname}')
    except Exception as e:
        messagebox.showerror('Save error', str(e))


# -------------------------------
# Resize handler
# -------------------------------
def on_right_configure(event):
    try:
        dpi = fig.get_dpi()
        w_in = max(4, event.width / dpi)
        h_in = max(3, event.height / dpi)
        fig.set_size_inches(w_in, h_in, forward=True)
        canvas.draw_idle()
    except Exception:
        pass


# -------------------------------
# Build GUI
# -------------------------------
root = tk.Tk()
root.title('Forward Modelling Gravitasi (Interaktif) - Variation')

# try to maximize
try:
    root.state('zoomed')
except Exception:
    pass

root.grid_columnconfigure(0, weight=0)
root.grid_columnconfigure(1, weight=1)
root.grid_rowconfigure(0, weight=1)

# left control panel
frame_left = ttk.Frame(root, padding=10)
frame_left.grid(row=0, column=0, sticky='ns')

ttk.Label(frame_left, text='Input Titik Sumber', font=('Segoe UI', 11, 'bold')).grid(row=0, column=0, columnspan=2, pady=4)

ttk.Label(frame_left, text='Nama:').grid(row=1, column=0, sticky='e')
entry_name = ttk.Entry(frame_left, width=18); entry_name.grid(row=1, column=1, pady=2)

ttk.Label(frame_left, text='x (m):').grid(row=2, column=0, sticky='e')
entry_x = ttk.Entry(frame_left, width=18); entry_x.grid(row=2, column=1, pady=2)

ttk.Label(frame_left, text='z (m, kedalaman):').grid(row=3, column=0, sticky='e')
entry_z = ttk.Entry(frame_left, width=18); entry_z.grid(row=3, column=1, pady=2)

ttk.Label(frame_left, text='ρ (kg/m³):').grid(row=4, column=0, sticky='e')
entry_rho = ttk.Entry(frame_left, width=18); entry_rho.grid(row=4, column=1, pady=2)

btn_add = ttk.Button(frame_left, text='Tambah', command=add_point); btn_add.grid(row=5, column=0, columnspan=2, pady=(6,2))
btn_update = ttk.Button(frame_left, text='Update', command=update_selected); btn_update.grid(row=6, column=0, columnspan=2)
btn_delete = ttk.Button(frame_left, text='Hapus Terpilih', command=delete_selected); btn_delete.grid(row=7, column=0, columnspan=2)
btn_clear = ttk.Button(frame_left, text='Clear Semua', command=clear_points); btn_clear.grid(row=8, column=0, columnspan=2, pady=4)

# import/export controls
btn_import = ttk.Button(frame_left, text='Import CSV/TXT', command=import_sources); btn_import.grid(row=9, column=0, columnspan=2, pady=(6,2))
btn_export = ttk.Button(frame_left, text='Export sources', command=export_sources); btn_export.grid(row=10, column=0, columnspan=2)

# listbox of sources
listbox = tk.Listbox(frame_left, width=70, height=12)
listbox.grid(row=11, column=0, columnspan=2, pady=(8,2))
listbox.bind('<<ListboxSelect>>', on_select)

# colormap and interpolation options
ttk.Label(frame_left, text='Colormap:').grid(row=12, column=0, sticky='e')
cmap_var = tk.StringVar(value=DEFAULT_CMAP)
cmaps = ['viridis','plasma','inferno','magma','cividis','coolwarm','seismic']
cb_cmap = ttk.Combobox(frame_left, textvariable=cmap_var, values=cmaps, state='readonly', width=16)
cb_cmap.grid(row=12, column=1, pady=2)
cb_cmap.bind('<<ComboboxSelected>>', lambda e: update_plot())

ttk.Label(frame_left, text='Map extent (m):').grid(row=15, column=0, sticky='e')
entry_extent = ttk.Entry(frame_left, width=18); entry_extent.insert(0,'200'); entry_extent.grid(row=15, column=1, pady=2)

# save figure
btn_save = ttk.Button(frame_left, text='Save Figure', command=save_plot); btn_save.grid(row=16, column=0, columnspan=2, pady=(8,2))

# right plot panel
frame_right = ttk.Frame(root)
frame_right.grid(row=0, column=1, sticky='nsew')
frame_right.grid_rowconfigure(0, weight=1)
frame_right.grid_columnconfigure(0, weight=1)

fig = plt.figure(constrained_layout=True)
gs = fig.add_gridspec(2, 1, height_ratios=[2, 1])
ax_map = fig.add_subplot(gs[0]); ax_profile = fig.add_subplot(gs[1])

canvas = FigureCanvasTkAgg(fig, master=frame_right)
canvas_widget = canvas.get_tk_widget()
canvas_widget.pack(fill='both', expand=True)

frame_right.bind('<Configure>', on_right_configure)

# initial draw
update_plot()

# keyboard shortcut: ESC to exit fullscreen
root.bind('<Key>', lambda e: root.quit() if e.keysym == 'Escape' else None)

root.mainloop()
