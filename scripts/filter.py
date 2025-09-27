import argparse
import os

import numpy as np
from numpy.typing import NDArray
from PIL import Image

import shutil

from typing import Tuple, TypeAlias, List

FileMetadata: TypeAlias = Tuple[
    str,  # sat_name
    str,  # sat_index
    str,  # num_bursts
    str,  # burst_index
    str,  # elapsed_time
    str,  # sat_position (3D)
    str,  # sat_rotation (4D quaternion)
]

def extract_data_from_filename(filename: str) -> FileMetadata:
    """
    Extract timestamp, satellite position, and rotation from filename.

    Args:
      filename: Name of the image file

    Returns:
      Tuple containing:
        - name: Satellite name
        - i: Satellite index
        - j: Number of bursts
        - k: Burst index
        - elapsed_time: Time elapsed
        - sat_pos: Numpy array of satellite position
        - sat_rot: Numpy array of satellite rotation (quaternion)
    """
    # Extract the relevant parts of the filename
    # filePath =
    # $"{screenshotFolder}/{sat.name}_{sat.index}_{sat.numBurst}_{sat.burstIndex}_{sat.time}_{satPos}_{satRot}.jpg";
    file_name_parts: List[str] = filename.split('_')

    name: str = file_name_parts[0]  # satellite name
    i: str = file_name_parts[1]
    j: str = file_name_parts[2]
    k: str = file_name_parts[3]
    elapsed_time: str = int(file_name_parts[4])
    sat_pos: str = file_name_parts[5]
    sat_rot: str = file_name_parts[6]

    # TODO: normalize elapsed_time [0, 1)
    return name, i, j, k, elapsed_time, sat_pos, sat_rot

def validate(data: List[FileMetadata]) -> bool:
  """
  Validate that all files in a sequence belong to the same position and burst.

  Args:
    data: List of extracted file data tuples

  Returns:
    True if validation passes, False otherwise
  """
  for i in range(len(data) - 1):
    if data[i][1] != data[i + 1][2]:
      return False  # Make sure images are in the same position
    if data[i][2] != data[i + 1][2]:
      return False  # Make sure images are in the same burst
  return True


def is_image_empty(image_path: str, threshold: float = 0.95, darkness_threshold: int = 10) -> bool:
  """
  Check if an image is mostly black (empty)

  Args:
    image_path (str): Path to the image file
    threshold (float): Threshold for determining if image is empty
    darkness_threshold (int): Pixel value below which a pixel is considered black

  Returns:
    bool: True if image is mostly black, False otherwise
  """
  try:
    # Open the image
    img: Image.Image = Image.open(image_path)

    # Convert image to grayscale
    img_gray: Image.Image = img.convert("L")

    # Convert to numpy array
    img_array: np.ndarray = np.array(img_gray)

    # Calculate the percentage of dark pixels
    dark_pixels: int = int(np.sum(img_array < darkness_threshold))
    total_pixels: int = int(img_array.size)

    dark_ratio: float = dark_pixels / total_pixels

    return dark_ratio > threshold

  except Exception as e:
    print(f"Error processing {image_path}: {str(e)}")
    return False


def delete_empty_images(folder_path: str, threshold: float, delete: bool, frames: int, valid_extensions: tuple[str, ...]) -> None:
  """
  Check all images in a folder and delete empty (mostly black) images

  Args:
    folder_path (str): Path to the folder containing images
    threshold (float): Threshold for determining if image is empty
    delete (bool): Whether to delete the images
    frames (int): Number of frames per burst
  """

  files: list[str] = [f for f in os.listdir(folder_path) if f.startswith('cubesat')]
  files.sort()  # The order of files is important

  # Iterate through all files in the folder
  for i in range(0, len(files), frames):
    are_empty: bool = True
    images: list[str] = []


    for j in range(frames):
      if files[i + j].lower().endswith(valid_extensions):
        file_path: str = os.path.join(folder_path, files[i + j])
        are_empty = are_empty and is_image_empty(file_path, threshold)
        images.append(file_path)        
    

    # TODO: make sure all the images belong to the same burst before deleting.
    if delete and are_empty:
      for j in range(frames):
        try:
          if delete:
            os.remove(images[j])
        except Exception as e:
          print(f"Error deleting {images[j]}: {str(e)}")

def merge_folders(subfolders: list[str], valid_extensions: tuple[str, ...], frames: int, output_folder: str = "merged") -> None:
  """
  Merge subfolders into a single folder with renumbered prefixes.

  Args:
      subfolders (list[str]): List of subfolder paths
      output_folder (str): Destination folder for merged images
  """
  os.makedirs(output_folder, exist_ok=True)

  count = 0
  for folder in subfolders:
    files: list[str] = [f for f in os.listdir(folder) if f.startswith('cubesat')]
    files.sort()  # The order of files is important
    
    for i in range(0, len(files), frames):
      files_data: List[FileMetadata] = []
      for j in range(frames):
        files_data.append(extract_data_from_filename(files[i + j]))

      if not validate(files_data):
        continue
      
      for j in range(frames):
        parts = [
          files_data[j][0],
          count,
          files_data[j][-3],
          files_data[j][-2],
          files_data[j][-1],
        ]
        
        new_name = '_'.join(parts) + '.jpg'
        src = os.path.join(folder, files[i+j])
        dst = os.path.join(output_folder, new_name)

        # Copy file into merged folder
        shutil.copy2(src, dst)
        
        count+=1
    
  return


def parse_arguments() -> argparse.Namespace:
  """
  Parse command line arguments

  Returns:
      argparse.Namespace: Parsed command line arguments
  """
  parser: argparse.ArgumentParser = argparse.ArgumentParser(
      description="Delete empty (mostly black) images from a folder"
  )

  parser.add_argument("--path", type=str, required=True, help="Path to the folder containing images")

  parser.add_argument(
      "--threshold", type=float, default=0.95, help="Threshold for determining if an image is empty (0.0 to 1.0)"
  )

  parser.add_argument("--frames", type=int, default=3, help="Number of frames per burst")

  parser.add_argument("--delete", action="store_true", default=True, help="Delete images below the threshold")

  args: argparse.Namespace = parser.parse_args()

  # Validate threshold
  if not 0 <= args.threshold <= 1:
    parser.error("Threshold must be between 0.0 and 1.0")

  return args


if __name__ == "__main__":
  args = parse_arguments()
  folder_path, threshold, delete, frames = args.path, args.threshold, args.delete, args.frames
  
  # Supported image extensions
  valid_extensions: tuple[str, ...] = (".jpg",)
  
  # Check if folder exists
  if not os.path.exists(folder_path):
    raise FileNotFoundError(f"Error: Folder {folder_path} does not exist!")
  
  subfolders = [ f.path for f in os.scandir(folder_path) if f.is_dir() ]
  
  
  for sfolder in subfolders:
    delete_empty_images(sfolder, threshold, delete, frames, valid_extensions)

  merge_folders(subfolders, valid_extensions, frames, output_folder=os.path.join(folder_path, "merged"))
