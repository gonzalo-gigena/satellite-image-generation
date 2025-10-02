import argparse
import os
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

import numpy as np
from PIL import Image


@dataclass
class FileMetadata:
  sat_name: str
  sat_index: str
  num_bursts: str
  burst_index: str
  elapsed_time: str
  sat_position: str
  sat_rotation: str


def extract_metadata_from_filename(filename: str) -> FileMetadata:
  """
  Extract metadata fields from a filename into a FileMetadata object.
  Expected format:
    name_index_numBursts_burstIndex_elapsedTime_position_rotation.jpg
  """
  file_name_parts: List[str] = Path(filename).stem.split('_')

  if len(file_name_parts) < 7:
    print(filename)
    raise ValueError(f'Unexpected filename format: {filename}')

  return FileMetadata(
      sat_name=file_name_parts[0],
      sat_index=file_name_parts[1],
      num_bursts=file_name_parts[2],
      burst_index=file_name_parts[3],
      elapsed_time=file_name_parts[4],
      sat_position=file_name_parts[5],
      sat_rotation=file_name_parts[6],
  )


def validate(data: List[FileMetadata]) -> bool:
  """
  Validate that all files in a sequence belong to the same position and burst.
  """
  if not data:
    return False
  sat_index = data[0].sat_index
  num_bursts = data[0].num_bursts
  return all(d.sat_index == sat_index and d.num_bursts == num_bursts for d in data)


def is_image_empty(
        image_path: str,
        threshold: float = 0.95,
        min_bright_ratio: float = 0.2,
        darkness_threshold: int = 10) -> bool:
  """
  Check if an image is mostly black (empty), while allowing small bright areas to count as non-empty.
  """
  try:
    with Image.open(image_path) as img:
      img_gray = img.convert('L')
      img_array = np.array(img_gray)

    dark_ratio = np.mean(img_array < darkness_threshold)
    bright_ratio = np.mean(img_array > 200)  # pixels that are pretty bright

    return dark_ratio > threshold and bright_ratio < min_bright_ratio
  except Exception as e:
    print(f'Error processing {image_path}: {e}')
    return False


def is_burst_empty(images: List[Path], threshold: float, min_bright_ratio: float) -> bool:
  """Check if all images in a burst are empty (mostly black)."""
  return all(is_image_empty(str(img), threshold, min_bright_ratio) for img in images)


def merge_folders(subfolders: List[Path], frames: int, threshold: float, bright_ratio: float,
                  valid_extensions: Tuple[str, ...], output_folder: Path = Path('merged')) -> None:
  """
  Merge subfolders into a single folder with renumbered prefixes.
  """
  output_folder.mkdir(exist_ok=True)

  count = 0
  for folder in subfolders:
    files = sorted([f for f in folder.iterdir() if f.name.startswith('cubesat')])

    if not files:
      print(f'Skipping empty folder: {folder}')
      continue

    for i in range(0, len(files), frames):
      burst_files = files[i:i + frames]
      files_metadata: List[FileMetadata] = [extract_metadata_from_filename(f.name) for f in burst_files]
      images: List[Path] = [f for f in burst_files if f.suffix.lower() in valid_extensions]

      if not validate(files_metadata) or is_burst_empty(images, threshold, bright_ratio):
        continue

      for j, src in enumerate(burst_files):
        metadata = files_metadata[j]
        new_name = f'{metadata.sat_name}_{count}_{metadata.elapsed_time}_{metadata.sat_position}_{metadata.sat_rotation}{src.suffix}'
        dst = output_folder / new_name
        shutil.copyfile(src, dst)

      count += 1

def get_subfolders(folder: Path, ih: int, iw: int, frames: int) -> List[Path]:
  subfolders = []

  # Regex: ^ih_iw_frames_timestamp
  pattern = re.compile(rf"^{ih}_{iw}_{frames}_(\d+(\.\d+)?)$")
  for f in folder.iterdir():
    if f.is_dir() and pattern.match(f.name):
      subfolders.append(f)
  
  return subfolders

def parse_arguments() -> argparse.Namespace:
  """
  Parse command line arguments.
  """
  parser: argparse.ArgumentParser = argparse.ArgumentParser(
      description='Delete empty (mostly black) images from a folder'
  )

  parser.add_argument('--path', type=str, required=True, help='Path to the folder containing images')
  parser.add_argument('--threshold', type=float, default=0.95, help='Threshold (0.0 to 1.0)')
  parser.add_argument('--bright_ratio', type=float, default=0.95, help='Bright ratio (0.0 to 1.0)')
  parser.add_argument('--frames', type=int, default=3, help='Number of frames per burst')
  parser.add_argument('-ih', '--image_height', type=int, default=102, help='Image height')
  parser.add_argument('-iw', '--image_width', type=int, default=102, help='Image width')

  args: argparse.Namespace = parser.parse_args()

  if not 0 <= args.threshold <= 1:
    parser.error('Threshold must be between 0.0 and 1.0')

  return args

if __name__ == '__main__':
  args = parse_arguments()

  folder_path: Path = Path(args.path)
  threshold, frames, bright_ratio, image_height, image_width = args.threshold, args.frames, args.bright_ratio, args.image_height, args.image_width

  valid_extensions: Tuple[str, ...] = ('.jpg',)

  if not os.path.exists(folder_path):
    raise FileNotFoundError(f'Error: Folder {folder_path} does not exist!')

  subfolders: List[Path] = get_subfolders(folder_path, image_height, image_width, frames)
  
  output_folder = f'{image_height}_{image_width}_{frames}_merged'

  merge_folders(subfolders, frames, threshold, bright_ratio, valid_extensions, output_folder=folder_path / output_folder)
