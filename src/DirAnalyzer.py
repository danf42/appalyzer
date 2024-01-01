"""Module to handle secret searching in Directories """
import logging
from Appalyzer import Appalyzer

class DirAnalyzer(Appalyzer):
    """
    Class used to search for secrets in directory
    Nothing fancy, just read whatever files are in the directory and search for stuff
    """

    logger = logging.getLogger(__name__)

    def __init__(self, app:str, regexfile:str=None) -> None:
        """        
        Parameters
        ----------
        app : str
            The path to the application to analyze (can be a file or directory)
        """
        super().__init__(app, regexfile)

        self.outfile =  self.app.joinpath(f"dirscan_{self._time_now}_results.out")

        if not self._is_dir:
            raise NotADirectoryError("f{self.app} is not a directory")

    def secret_search(self) -> None:
        """ 
        Perform secret search
        """

        # Write header
        self._write_header()

        # Start searching for secrets
        self._search(self.app)

        DirAnalyzer.logger.info("Results can be found here %s", self.outfile)
