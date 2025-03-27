import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.animation import FuncAnimation
from math import gcd

# Function to calculate the least common multiple
def lcm(a, b):
  return abs(a * b) // gcd(a, b)

# Function to simulate satellite tumbling
def satellite_tumble(t, x_deg_per_sec, y_deg_per_sec, z_deg_per_sec):
  # Convert degrees per second to radians per second
  x_rad_per_sec = np.deg2rad(x_deg_per_sec)
  y_rad_per_sec = np.deg2rad(y_deg_per_sec)
  z_rad_per_sec = np.deg2rad(z_deg_per_sec)
  
  # Calculate the rotation using simple harmonic motion
  x_rotation = np.sin(x_rad_per_sec * t)
  y_rotation = np.cos(y_rad_per_sec * t)
  z_rotation = np.sin(z_rad_per_sec * t) * np.cos(z_rad_per_sec * t)
  
  return x_rotation, y_rotation, z_rotation

if __name__ == '__main__':
  # Set up the figure and 3D axis
  fig = plt.figure()
  ax = fig.add_subplot(111, projection='3d')

  # Initial plot
  x, y, z = satellite_tumble(0, 0, 0, 0)
  path, = ax.plot([], [], [], 'b-', lw=2)  # Line to track the path

  # Set the limits of the plot
  ax.set_xlim(-1, 1)
  ax.set_ylim(-1, 1)
  ax.set_zlim(-1, 1)

  # Lists to store the path
  x_data, y_data, z_data = [], [], []

  # Rotation rates in degrees per second (as floats)
  x_deg_per_sec = 30
  y_deg_per_sec = 45
  z_deg_per_sec = 60

  # Calculate the time for a full rotation for each axis
  x_full_rotation_time = 360.0 / x_deg_per_sec
  y_full_rotation_time = 360.0 / y_deg_per_sec
  z_full_rotation_time = 360.0 / z_deg_per_sec

  # To calculate the LCM of floating-point numbers, scale them to integers
  scale_factor = 1000  # Scale factor to convert to integers
  x_scaled = int(x_full_rotation_time * scale_factor)
  y_scaled = int(y_full_rotation_time * scale_factor)
  z_scaled = int(z_full_rotation_time * scale_factor)

  # Calculate the LCM of the scaled full rotation times
  lcm_scaled_full_rotation_time = lcm(lcm(x_scaled, y_scaled), z_scaled)

  # Convert back to the original scale
  lcm_full_rotation_time = lcm_scaled_full_rotation_time / scale_factor

  print("LCM of full rotation times:", lcm_full_rotation_time)
  # Initialize the arrow
  arrow = None
  
  # Update function for animation
  def update(frame):
    global arrow
    x, y, z = satellite_tumble(frame, x_deg_per_sec, y_deg_per_sec, z_deg_per_sec)
    x_data.append(x)
    y_data.append(y)
    z_data.append(z)
    
    # Update the path
    path.set_data(x_data, y_data)
    path.set_3d_properties(z_data)
    
    # Remove the previous arrow
    if arrow:
      arrow.remove()
    
    # Draw the new arrow
    arrow = ax.quiver(0, 0, 0, x, y, z, color='r', length=0.5)
    
    # Reset the path data at the end of a full cycle
    if frame >= lcm_full_rotation_time:
      x_data.clear()
      y_data.clear()
      z_data.clear()
    
    return path, arrow

  # Create the animation with more frames for smoother motion
  ani = FuncAnimation(fig, update, frames=np.linspace(0, lcm_full_rotation_time, 500), blit=False, interval=20)

  # Save the animation as a GIF
  ani.save('satellite_tumble.gif', writer='pillow', fps=50)

  # Show the plot
  plt.show()