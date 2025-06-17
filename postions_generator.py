import json
import ephem
import argparse
from random import uniform
from pathlib import Path
from datetime import datetime, timedelta, UTC
from typing import Tuple, List

from info_extractor import search_tle_by_date, sat_pos_and_vel, jday, sun_pos_from_sc

# Constants
DATE_FORMAT = '%d-%m-%Y %H:%M:%S.%f'
OUTPUT_PATH = Path('Simulation/Assets/Resources/generated_positions.json')
DEFAULT_START_DATE = "01-01-2023 00:00:00.000000"

def parse_arguments() -> Tuple[int, datetime, int]:
  """
  Parse command line arguments.

  Returns:
      Tuple containing burst rate, starting date, and time step in seconds.
  """
  parser = argparse.ArgumentParser(
    description='Generate satellite positions for Unity simulation',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
  )

  parser.add_argument(
    '--burst', '-b',
    type=int,
    default=3,
    help='Burst rate after each step'
  )
  parser.add_argument(
    '--num_bursts', '-n',
    type=int,
    default=2,
    help='Number of bursts per step'
  )
  parser.add_argument(
    '--starting_date', '-d',
    type=str,
    default=None,
    help=f'Starting date in format "{DATE_FORMAT}"'
  )
  parser.add_argument(
    '--step', '-s',
    type=int,
    default=3600,
    help='Time step in seconds'
  )
  parser.add_argument(
    '--output', '-o',
    type=str,
    default=str(OUTPUT_PATH),
    help='Output JSON file path'
  )

  args = parser.parse_args()

  # Use the default start date if none provided
  if args.starting_date is None:
    starting_date = datetime.strptime(DEFAULT_START_DATE, DATE_FORMAT).replace(tzinfo=UTC)
  else:
    try:
      starting_date = datetime.strptime(args.starting_date, DATE_FORMAT).replace(tzinfo=UTC)
    except ValueError:
      parser.error(f"Invalid date format! Expected '{DATE_FORMAT}' but got '{args.starting_date}'")

  return args.burst, starting_date, args.step, args.output, args.num_bursts


def subsolar_point_at_utc(utc_datetime: datetime) -> Tuple[float, float]:
  """
  Calculate the subsolar point (latitude and longitude) at a given UTC time.

  Args:
      utc_datetime: The UTC datetime for calculation

  Returns:
      Tuple of (latitude, longitude) in degrees
  """
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

def generate_position(dt: datetime) -> Tuple[List[float], Tuple[float, float], List[float]]:
  """
  Generate satellite and sun positions for a given datetime.

  Args:
      dt: The datetime for calculation

  Returns:
      Tuple containing (sun position, subsolar point, satellite position)
  """
  jd = jday(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)

  line1, line2= search_tle_by_date(jd, dt.year)

  pos, _ = sat_pos_and_vel(line1, line2, jd)

  sun_pos = sun_pos_from_sc(jd, pos)

  subsolar_point = subsolar_point_at_utc(dt)

  return sun_pos, subsolar_point, pos

def satellite_tumble(starting_orientation: List[float], tumble: List[float], time_elapsed: float) -> List[float]:
  """
  Calculate satellite orientation based on initial orientation, tumble rates, and elapsed time.

  Args:
      starting_orientation: Initial orientation angles [x, y, z] in degrees
      tumble: Tumble rates [x, y, z] in degrees per second
      time_elapsed: Time elapsed in seconds since simulation start

  Returns:
      List of rotation angles [x, y, z] in degrees
  """
  # Calculate the new orientation
  new_orientation = [
    (starting_orientation[i] + tumble[i] * time_elapsed) % 360
    for i in range(3)
  ]
  return new_orientation

if __name__ == '__main__':
  burst, starting_date, step, output_path, num_bursts = parse_arguments()

  positions = {
    'time_elapsed': [],
    'subsolar_points': [],
    'sun_pos': [],
    'burst': burst,
    'num_burst': num_bursts,
    'satellites': [{
      'name': 'cubesat',
      'pos': [],
      'rotations': []
    }]
  }

  # Set the end date to the end of the year
  end_date = datetime(starting_date.year + 1, 1, 1, tzinfo=UTC) - timedelta(seconds=1)

  # Initialize counters
  i = 0

  # Main simulation loop
  current_date = starting_date
  while current_date <= end_date:
    # Generate position data
    sun_pos, subsolar_point, sat_pos = generate_position(current_date)

    # Calculate time elapsed for rotation
    time_elapsed = (current_date - starting_date).total_seconds()

    # Update data structure
    positions['time_elapsed'].append(time_elapsed)
    positions['subsolar_points'].append(subsolar_point)
    positions['sun_pos'].append(sun_pos)
    positions['satellites'][0]['pos'].append(sat_pos)

    rotations = []
    for j in range(num_bursts):
      # Calculate sarting orientation and tubmble
      starting_orientation = [uniform(0.0, 360.0) for _ in range(3)]
      tumble = [uniform(0.0, 1.0) for _ in range(3)] # in degrees per second

      # Generate positions for each burst point
      for k in range(burst):
        # Generate rotation
        rotation = satellite_tumble(starting_orientation, tumble, time_elapsed + k)
        rotations.append(rotation)

    i += 1
    positions['satellites'][0]['rotations'].append(rotations)
    current_date = starting_date + timedelta(seconds=i*step)

  positions['total'] = i

  with open(output_path, 'w') as outfile:
    json.dump(positions, outfile, indent=2)