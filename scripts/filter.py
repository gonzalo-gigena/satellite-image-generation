import argparse
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

from PIL import Image
from tqdm import tqdm


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


def load_and_resize(image_path: Path, resize_to: Tuple[int, int]) -> Image.Image:
  """Decode an image and downsample it to resize_to.

  draft() lets the JPEG decoder produce a reduced-resolution image directly
  (DCT-domain scaling), so the full-size bitmap is never materialized; the
  final LANCZOS resize only covers the remaining factor. No-op for non-JPEGs.
  """
  with Image.open(image_path) as img:
    img.draft(img.mode, resize_to)
    return img.resize(resize_to, Image.Resampling.LANCZOS)


def is_image_empty(
        img: Image.Image,
        threshold: float = 0.95,
        min_bright_ratio: float = 0.2,
        darkness_threshold: int = 10) -> bool:
  """
  Check if an image is mostly black (empty), while allowing small bright areas to count as non-empty.
  """
  hist = img.convert('L').histogram()
  total = img.width * img.height
  dark_ratio = sum(hist[:darkness_threshold]) / total
  bright_ratio = sum(hist[201:]) / total  # pixels that are pretty bright
  return dark_ratio > threshold or bright_ratio < min_bright_ratio


def load_burst_if_valid(
        images: List[Path],
        threshold: float,
        min_bright_ratio: float,
        resize_to: Tuple[int, int]) -> dict | None:
  """Decode and resize each burst frame once, checking emptiness as it goes.

  Returns a {path: resized image} dict for the whole burst, or None as soon
  as any frame is empty (mostly black) or unreadable, so remaining frames
  are never decoded. The kept images are saved directly by the caller,
  avoiding a second decode+resize pass.
  """
  loaded: dict = {}
  for path in images:
    try:
      img = load_and_resize(path, resize_to)
    except Exception as e:
      print(f'Error processing {path}: {e}')
      return None
    if is_image_empty(img, threshold, min_bright_ratio):
      return None
    loaded[path] = img
  return loaded


def merge_folders(
        subfolders: List[Path],
        frames: int,
        threshold: float,
        bright_ratio: float,
        valid_extensions: Tuple[str, ...],
        output_folder: Path = Path('merged'),
        resize_to: Tuple[int, int] | None = None) -> None:
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
    print(f'Processing {len(files)} images from {folder}...')
    num_sequences = len(files) // frames
    with tqdm(total=num_sequences, desc='Processing sequences', unit='seq') as pbar:
      for i in range(0, len(files), frames):
        burst_files = files[i:i + frames]
        files_metadata: List[FileMetadata] = [extract_metadata_from_filename(f.name) for f in burst_files]
        images: List[Path] = [f for f in burst_files if f.suffix.lower() in valid_extensions]

        if not validate(files_metadata):
          pbar.update(1)
          continue

        loaded = load_burst_if_valid(images, threshold, bright_ratio, resize_to)
        if loaded is None:
          pbar.update(1)
          continue

        for j, src in enumerate(burst_files):
          metadata = files_metadata[j]
          new_name = (
              f'{metadata.sat_name}_'
              f'{count}_'
              f'{metadata.elapsed_time}_'
              f'{metadata.sat_position}_'
              f'{metadata.sat_rotation}'
              f'{src.suffix}'
          )
          dst = output_folder / new_name

          # Already decoded and downsampled by load_burst_if_valid; high JPEG
          # quality avoids compounding the loss from the capture-time
          # compression in a second pass.
          img = loaded.get(src)
          if img is None:  # file skipped by the extension filter
            img = load_and_resize(src, resize_to)
          img.save(dst, quality=95)
        pbar.update(1)
        count += 1


def get_subfolders(folder: Path, frames: int, degrees: int) -> List[Path]:
  subfolders = []

  pattern = re.compile(rf"^{frames}_{degrees}_[0-9]+\.[0-9]+$")
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

  parser.add_argument('-p', '--path', type=str, required=True, help='Path to the folder containing images')
  parser.add_argument('-t', '--threshold', type=float, default=0.95, help='Threshold (0.0 to 1.0)')
  parser.add_argument(
      '-br', '--bright_ratio', type=float, default=0.2,
      help='Minimum ratio of bright pixels (>200) for an image to count as non-empty (0.0 to 1.0)'
  )
  parser.add_argument('-f', '--frames', type=int, default=3, help='Number of frames per burst')
  parser.add_argument('-ih', '--image_height', type=int, default=102, help='Image height')
  parser.add_argument('-iw', '--image_width', type=int, default=102, help='Image width')
  parser.add_argument('-d', '--degrees', type=int, default=1, help='Degrees rotation')

  args: argparse.Namespace = parser.parse_args()

  if not 0 <= args.threshold <= 1:
    parser.error('Threshold must be between 0.0 and 1.0')

  return args


if __name__ == '__main__':
  args = parse_arguments()

  folder_path: Path = Path(args.path)
  threshold, frames, bright_ratio, image_width, image_height, degrees = args.threshold, args.frames, args.bright_ratio, args.image_width, args.image_height, args.degrees

  valid_extensions: Tuple[str, ...] = ('.jpg',)

  if not os.path.exists(folder_path):
    raise FileNotFoundError(f'Error: Folder {folder_path} does not exist!')

  subfolders: List[Path] = get_subfolders(folder_path, frames, degrees)

  output_folder = f'{image_width}_{image_height}_{frames}_{degrees}_merged'

  resize_to = (image_width, image_height)

  merge_folders(
      subfolders,
      frames,
      threshold,
      bright_ratio,
      valid_extensions,
      output_folder=folder_path / output_folder,
      resize_to=resize_to
  )
