"""
Created by Elias Obreque
els.obrq@gmail.com
Date: 31-01-2023
SPEL UChile
"""

import numpy as np
from sgp4.api import Satrec
from sgp4.api import WGS84
from datetime import datetime

RAD2DEG = 180 / np.pi
DEG2RAD = 1 / RAD2DEG
AU = 149597870.691  # km

# Calculates the Julian Date from a given date and time.
def jday(year, month, day, hour, minute, seconds):
  jd0 = 367.0 * year - 7.0 * (year + ((month + 9.0) // 12.0)) * 0.25 // 1.0 + 275.0 * month // 9.0 + day + 1721013.5
  utc = ((seconds / 60.0 + minute) / 60.0 + hour)  # UTC in hours
  return jd0 + utc / 24.

# Searches for the TLE (Two-Line Element) data closest to a given date and time.
def search_tle_by_date(jd, year):
  jd_year_start = jday(year, 1, 1, 0, 0, 0)
  epoch_day = jd - jd_year_start
  
  current_epoch_tle = float(f"{year % 100}{round(epoch_day, 8)}")

  file_tle = open("LTE.txt", 'r').read()
  epoch_day_tle = [float(line[17:33]) for line in file_tle.split('\n')[:-1] if line[0] == '1']

  idx = np.argmin(np.abs(current_epoch_tle - np.array(epoch_day_tle)))
  line_1 = file_tle.split('\n')[0 + 2 * idx]
  line_2 = file_tle.split('\n')[0 + 2 * idx + 1]

  return line_1, line_2

def sat_pos_and_vel(line1, line2, jd):
  #High-speed computation of satellite positions and velocities
  satellite = Satrec.twoline2rv(line1, line2, WGS84)
  _, pos, vel = satellite.sgp4(int(jd), jd % 1)

  return pos, vel

def sun_pos_from_sc(jd, sat_pos):
  # all in degree
  n = jd - 2451545.0
  l = (280.459 + 0.98564736 * n) % 360.0
  m = (357.529 + 0.98560023 * n) % 360.0
  m *= DEG2RAD
  lam = (l + 1.915 * np.sin(m) + 0.0200 * np.sin(2 * m)) % 360.0
  lam *= DEG2RAD
  e = 23.439 - 3.56e-7 * n
  e *= DEG2RAD

  r_sun = (1.00014 - 0.01671 * np.cos(m) - 0.000140 * np.cos(2 * m)) * AU
  u_v = np.array([np.cos(lam), np.cos(e) * np.sin(lam), np.sin(lam) * np.sin(e)])
  
  sun_pos_i_earth = r_sun * u_v
  sun_pos_from_sc = sun_pos_i_earth - sat_pos
  
  return sun_pos_from_sc.tolist()

def node_sat(image_name):
  node = 'NAN'
  sat = 'NAN'
  if 'N7' in image_name:
    node = 'N7'
  elif 'N4' in image_name:
    node = 'N4'
  if 'S3' in image_name:
    sat = 'S3'
  elif 'PS' in image_name:
    sat = 'PS'
  return node, sat

def get_file_info(file_name):
  date_time = file_name[:13]

  # UTC + 1
  dt = datetime.strptime(date_time, '%d%m%y_%H%M%S')
  jd = jday(dt.year, dt.month, dt.day, dt.hour - 1.0, dt.minute, dt.second)

  line1, line2= search_tle_by_date(jd, dt.year)
  
  pos, vel = sat_pos_and_vel(line1, line2, jd)

  sun_pos = sun_pos_from_sc(jd, pos)
  
  node, sat = node_sat(file_name)

  return {
    'sun_pos': sun_pos,
    'sc_pos_i': pos,
    'sc_vel_i': vel,
    'jd': jd,
    'filename': file_name,
    'line1': line1,
    'line2': line2,
    'sat_name': sat,
    'sat_node': node
  }