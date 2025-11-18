import numpy as np
import matplotlib.pyplot as plt
from harmonica import point

# ======================================================
# 1. BUAT GRID OBSERVASI
# ======================================================
east = np.linspace(-2000, 2000, 100)   # meter
north = np.linspace(-2000, 2000, 100)

E, N = np.meshgrid(east, north)
U = np.zeros_like(E)  # di permukaan tanah

coordinates = (E, N, U)

# ======================================================
# 2. MODELKAN POINT MASS
# ======================================================
# titik massa di tengah domain
e_p = np.array([0.0])           # meter
n_p = np.array([0.0])           
u_p = np.array([-1000.0])       # 1 km bawah permukaan

points = (e_p, n_p, u_p)
masses = np.array([5e12])       # kg

# ======================================================
# 3. HITUNG g_z (anomali gaya berat)
# ======================================================
gz = point_gravity(
    coordinates=coordinates,
    points=points,
    masses=masses,
    field="g_z",
    coordinate_system="cartesian"
)

# ======================================================
# 4. PLOT
# ======================================================
plt.figure(figsize=(6,5))
plt.contourf(E, N, gz, 30)
plt.colorbar(label="g_z (mGal)")
plt.title("Forward Modelling Gravity - Point Mass")
plt.xlabel("Easting (m)")
plt.ylabel("Northing (m)")
plt.show()