import configparser


def get_config(fine_name:str)-> configparser.ConfigParser:
    config = configparser.ConfigParser()
    ini_file_path=f"./resource/{fine_name}.ini"
    config.read(ini_file_path)

    return config