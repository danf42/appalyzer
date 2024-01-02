"""Configuration Parser module"""
import configparser
from pathlib import Path
import os
import errno

class AppAnalyzerConfig(object):
    """
    Class used to initialize and store configuration data
    """

    _CONFIG_FILE = None
    _CONFIG: None
    _INSTANCE = None

    def __new__(cls, *args, **kwargs):
        if cls._INSTANCE is None:
            cls._INSTANCE = super().__new__(cls)

        return cls._INSTANCE

    def __init__(self, config_file:str = None):
        """        
        Parameters
        ----------
        config_file : str
            Path to the configuraiton file

        Raises
        ----------
        FileNotFoundError
            If configuration file is not found
        """

        if config_file is None:
            config_file = Path('config.ini')

        if not Path(config_file).is_file():
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), config_file)


        AppAnalyzerConfig._CONFIG_FILE = Path(config_file)
        AppAnalyzerConfig._CONFIG = configparser.ConfigParser()
        AppAnalyzerConfig._CONFIG.read(config_file)

    @classmethod
    def get_config_file(cls) -> str:
        """
        Return the absolute path of the configuration file

        Returns
        ----------
        str
            Absolute path of the configuration file

        """
        return cls._CONFIG_FILE.absolute()

    @classmethod
    def get_config_value(cls, key: str) -> str:
        '''
        Return the value of the key specified
        '''
        if key not in AppAnalyzerConfig._CONFIG['default']:
            raise Exception(f"{key} Not found in {AppAnalyzerConfig._CONFIG_FILE}")

        return cls._CONFIG['default'][key]


    @classmethod
    def get_jadx_path(cls) -> str:
        """
        Return the path of the JADX binary

        Returns
        ----------
        str
            Absolute path of the JADX binary

        Raises
        ----------
        FileNotFoundError
            If configuration file is not found

        """
        p = cls._CONFIG['default']['JADX_PATH']

        if not Path(p):
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), p)

        return p

    @classmethod
    def get_ilspycmd_path(cls) -> str:
        """
        Return the path of the ilspycmd binary

        Returns
        ----------
        str
            Absolute path of the ilspycmd binary

        Raises
        ----------
        FileNotFoundError
            If configuration file is not found

        """
        p = cls._CONFIG['default']['ILSPYCMD_PATH']

        if not Path(p):
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), p)

        return p

    @classmethod
    def get_regex_path(cls) -> str:
        """
        Return the path of the regular expressions

        Returns
        ----------
        str
            Absolute path of the regular expressions

        Raises
        ----------
        FileNotFoundError
            If configuration file is not found

        """
        p = cls._CONFIG['default']['REGEX_PATH']

        if not Path(p):
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), p)

        return p

    @classmethod
    def get_outdir_path(cls) -> str:
        """
        Return the path of the output directory

        Returns
        ----------
        str
            Absolute path of the output directory

        Raises
        ----------
        FileNotFoundError
            If configuration file is not found

        """
        p = cls._CONFIG['default']['OUTDIR_PATH']

        if not Path(p):
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), p)

        return p
