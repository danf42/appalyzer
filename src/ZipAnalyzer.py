"""Module to Decompile and Search for secrets in iOS Mobile Applications"""
import logging
from zipfile import ZipFile
from Appalyzer import Appalyzer

class ZipAnalyzer(Appalyzer):
    """
    Class used to decompile and search for secrets in iOS Mobile Applications
    """

    logger = logging.getLogger(__name__)

    def __decompile_app(self) -> None:
        """
        Decompile the app and store in directory
        Process will take some time to decompile application
        """

        # Create the temp directory
        self._outdir = self._outdir.joinpath(f"{self.app.stem}", \
                                             f"{self.app.stem}_{self._time_now}")
        self._outdir.mkdir(parents=True, exist_ok=True)

        # Unzip file to self_outdir
        ZipAnalyzer.logger.info("Unzipping file...")
        unzipped_dir = self._outdir.joinpath("unzipped")
        zfile = ZipFile(self.app, mode='r')
        zfile.extractall(path=unzipped_dir)

    def secret_search(self) -> None:
        """
        Perform secret search
        """

        # Write header
        self._write_header()

        # Decompile the App
        self.__decompile_app()

         # Start searching for secrets
        self._search(self._outdir)
