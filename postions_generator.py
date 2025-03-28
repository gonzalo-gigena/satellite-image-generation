import json
import ephem
import argparse
from random import uniform

from datetime import datetime, timedelta, UTC
from info_extractor import search_tle_by_date, sat_pos_and_vel, jday, sun_pos_from_sc

DATE_FORMAT = '%d-%m-%Y %H:%M:%S.%f'

def parse_arguments():
  # Create the argument parser
  parser = argparse.ArgumentParser(description='Generae satellite positions for unity simulation')

  parser.add_argument('--b', type=int, default=3, help='Burst rate after each step')
  parser.add_argument('--starting_date', type=str, default=None, help='Starting date in format "DD-MM-YYYY HH:MM:SS.ffffff"')
  parser.add_argument('--step', type=int, default=3600, help='Time step in seconds')

  # Parse the arguments
  args = parser.parse_args()

  # Use the current UTC time if no starting_date is provided
  if args.starting_date is None:
    starting_date = datetime.strptime("01-01-2023 00:00:00.000000", DATE_FORMAT).replace(tzinfo=UTC)
  else:
    try:
      starting_date = datetime.strptime(args.starting_date, DATE_FORMAT).replace(tzinfo=UTC)
    except ValueError:
      parser.error(f"Invalid date format! Expected '{DATE_FORMAT}' but got '{args.starting_date}'")

  return args.b, starting_date, args.step

def subsolar_point_at_utc(utc_datetime):
  # Initialize an observer location (use a central point on Earth)
  # Create an observer object at the center of the Earth
  observer = ephem.Observer()
  observer.lat, observer.lon = '0', '0'
  observer.date = utc_datetime

  # Create a Sun object and compute its position
  sun = ephem.Sun(observer)

  # Calculate the subsolar latitude
  subsolar_lat_deg = sun.dec * 180 / ephem.pi

  # Calculate the subsolar longitude
  gst = observer.sidereal_time() - sun.ra
  subsolar_lon_deg = gst * 180 / ephem.pi

  return subsolar_lat_deg, subsolar_lon_deg

def generate_position(dt):
  jd = jday(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)

  line1, line2= search_tle_by_date(jd, dt.year)

  pos, _ = sat_pos_and_vel(line1, line2, jd)

  sun_pos = sun_pos_from_sc(jd, pos)

  subsolar_point = subsolar_point_at_utc(dt)

  return sun_pos, subsolar_point, pos

def satellite_tumble(starting_orientation, tumble, time_elapsed):
  # Calculate the new orientation
  new_orientation = [
    (starting_orientation[i] + tumble[i] * time_elapsed) % 360
    for i in range(3)
  ]
  return new_orientation

if __name__ == '__main__':
  burst, starting_date, step = parse_arguments()

  starting_orientation = [uniform(0.0, 360.0), uniform(.0, 360.0), uniform(0.0, 360.0)]
  tumble = [0.03, 0.045, 0.06] # in degrees per second

  positions = {
    'time_elapsed': [],
    'subsolar_points': [],
    'sun_pos': [],
    'starting_orientation': starting_orientation,
    'satellites': [{
      'name': 'cubesat',
      'pos': [],
      'rotations': []
    }]
  }

  new_date = starting_date
  i = 0
  while new_date.year == starting_date.year:
    new_date = starting_date + timedelta(seconds=i*step)
    i+=1
    for j in range(1, burst + 1):
      current_date = new_date + timedelta(seconds=j)
      sun_pos, subsolar_point, sat_pos = generate_position(current_date)
      positions['subsolar_points'].append(subsolar_point)
      positions['sun_pos'].append(sun_pos)
      positions['satellites'][0]['pos'].append(sat_pos)

      # Calculate rotation based on the time elapsed since the start of the year
      time_elapsed = (current_date - starting_date).total_seconds()
      positions['time_elapsed'].append(time_elapsed)

      rotation = satellite_tumble(starting_orientation, tumble, time_elapsed)
      positions['satellites'][0]['rotations'].append(rotation)

  positions['total'] = len(positions['time_elapsed'])

  with open('Simulation/Assets/Resources/generated_positions.json', 'w') as outfile:
    json.dump(positions, outfile, indent=2)