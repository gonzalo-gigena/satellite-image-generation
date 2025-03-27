import json
import ephem
import argparse

from datetime import datetime, timedelta, UTC
from info_extractor import search_tle_by_date, sat_pos_and_vel, jday, sun_pos_from_sc

DATE_FORMAT = '%d-%m-%Y %H:%M:%S.%f'

def parse_arguments():
  # Create the argument parser
  parser = argparse.ArgumentParser(description='Generae satellite positions for unity simulation')

  parser.add_argument('--n', type=int, default=1000, help='Number of positions to generate (default: 1000)')
  parser.add_argument('--starting_date', type=str, default=None, help='Starting date in format "DD-MM-YYYY HH:MM:SS.ffffff"')
  parser.add_argument('--step', type=int, help='Time step in seconds')

  # Parse the arguments
  args = parser.parse_args()
  
  # Use the current UTC time if no starting_date is provided
  if args.starting_date is None:
    starting_date = datetime.now(UTC)
  else:
    try:
      starting_date = datetime.strptime(args.starting_date, DATE_FORMAT).replace(tzinfo=UTC)
    except ValueError:
      parser.error(f"Invalid date format! Expected '{DATE_FORMAT}' but got '{args.starting_date}'")
  
  return args.n, starting_date, args.step

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

if __name__ == '__main__':
  N, starting_date, step = parse_arguments()
  
  positions = {
    'total': N,
    'dates': [],
    'subsolar_points': [],
    'sun_pos': [],
    'satellites': [{
      'name': 'cubesat',
      'pos': []
    }]
  }

  for i in range(0, N):
    new_date = starting_date + timedelta(seconds=i*step)
    sun_pos, subsolar_point, sat_pos = generate_position(new_date)
    positions['dates'].append(new_date.strftime(DATE_FORMAT))
    positions['subsolar_points'].append(subsolar_point)
    positions['sun_pos'].append(sun_pos)
    positions['satellites'][0]['pos'].append(sat_pos)

  with open('Simulation/Assets/Resources/generated_positions.json', 'w') as outfile:
    json.dump(positions, outfile, indent=2)