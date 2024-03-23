import configparser
import os
from pathlib import Path


def get_config(fine_name: str) -> configparser.ConfigParser:
    config = configparser.ConfigParser()

    path = os.path.join(Path(__file__).parent.parent, "resource")
    ini_file_path = f'{path}/{fine_name}.ini'

    print(ini_file_path)
    config.read(ini_file_path)
    return config
