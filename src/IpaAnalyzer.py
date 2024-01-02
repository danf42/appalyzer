"""Module to Decompile and Search for secrets in iOS Mobile Applications"""
import logging
from zipfile import ZipFile
import plistlib
import json
from datetime import date, datetime
from pathlib import Path
import magic
from Appalyzer import Appalyzer

class IpaAnalyzer(Appalyzer):
    """
    Class used to decompile and search for secrets in iOS Mobile Applications
    """

    logger = logging.getLogger(__name__)

    MACO_EXE_MAGIC = "Mach-O 64-bit arm64"

    def __init__(self, app:str, regexfile:str=None) -> None:
        """        
        Parameters
        ----------
        app : str
            The path to the application to analyze (can be a file or directory)
        """

        super().__init__(app, regexfile)

        self.__toscan_dir = None


    def __json_serializer(self, obj:any) -> any:
        """
        Decode byte opjects when processing json objects
        Parameters
        ---------
        obj:Any
            Object that needs to be decoded

        Returns
        ---------
        obj:Any 
            Decoded object

        Raises
        ---------
            TypeError unsupported object type
        """
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()

        elif isinstance(obj, bytes):
            return obj.decode('utf-8', errors="ignore")

        else:
            IpaAnalyzer.logger.debug("[!] Unsupported serializable object %s : type: %s", obj, type(obj))
            raise TypeError (f"[!] Type {type(obj)} not serializable")

    def __plist_to_json(self, pfile:str) -> None:
        """
        Convert plist file to json file

        Parameters
        ----------
        pfile : str
            Absolute path to the plist file

        """

        outfile = f"{pfile}.json"

        with open(pfile, 'rb') as fd:

            try:
                pfiledata = plistlib.load(fd)

            except plistlib.InvalidFileException as e:
                IpaAnalyzer.logger.error("[!] Error processing %s : %s", pfile, str(e))

            else:
                IpaAnalyzer.logger.debug("[plistfile] Writing contentes to %s", outfile)
                with open(outfile, "w", encoding="utf-8") as fd:
                    json.dump(pfiledata, fd, indent=4, default=self.__json_serializer)


    def __decompile_app(self) -> None:
        """
        Decompile the app and store in directory
        Process will take some time to decompile application
        """

        # Create the temp directory
        self._outdir = self._outdir.joinpath(f"{self.app.stem}", \
                                             f"{self.app.stem}_{self._time_now}")
        self._outdir.mkdir(parents=True, exist_ok=True)

        # Unzip ipa file to self_outdir
        IpaAnalyzer.logger.info("Unzipping file...")
        unzipped_dir = self._outdir.joinpath("unzipped")
        zfile = ZipFile(self.app, mode='r')
        zfile.extractall(path=unzipped_dir)

        # Find mobile file in the extracted archive
        appdir =  Path(sorted(unzipped_dir.glob("**/*.app"))[0])
        dirlist = sorted(appdir.rglob("*"))

        # Set the scandir to the *.app directory
        self.__toscan_dir = appdir

        for item in dirlist:

            if Path(item).is_file():

                m = magic.from_file(item)
                ext = Path(item).suffix

                if IpaAnalyzer.MACO_EXE_MAGIC in m:
                    IpaAnalyzer.logger.debug("Pricessing binary file:  %s in binary %s", \
                                             {IpaAnalyzer.MACO_EXE_MAGIC}, item)
                    self._run_strings(item)

                elif ext == ".plist":
                    IpaAnalyzer.logger.debug("Processing plist file: %s", item)
                    self.__plist_to_json(item)

                elif ext == ".car" or ext == ".mobileprovision":
                    IpaAnalyzer.logger.debug("Running strings on file:  %s", item)
                    self._run_strings(item)


    def secret_search(self) -> None:
        """
        Perform secret search
        """

        # Write header
        self._write_header()

        # Decompile the App
        self.__decompile_app()

        # Start searching for secrets
        self._search(self.__toscan_dir)
