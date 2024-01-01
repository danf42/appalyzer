"""Class used to decompile and search for secrets in .Net DLLs"""
import shlex
import subprocess
import logging
import sys
from Appalyzer import Appalyzer


class DllAnalyzer(Appalyzer):
    """
    Class used to decompile and search for secrets in .Net DLLs
    """

    logger = logging.getLogger(__name__)

    def _decompile_app(self) -> None:
        """ 
        Decompile the app and store in directory
        Process will take some time to decompile application
        """

        # Create the temp directory
        self._outdir = self._outdir.joinpath(f"{self.app.stem}",
                                             f"{self.app.stem}_{self._time_now}")
        
        self._outdir.mkdir(parents=True, exist_ok=True)

        # Get jadx binary path
        try:
            cmd_path = self._config.get_ilspycmd_path()

        except FileNotFoundError as err:
            DllAnalyzer.logger.error("[!] Could not find ilspycmd! Exiting..." )
            sys.exit(1)

        else:
            
            # Create the decompile command
            decompile_cmd = [str(cmd_path), "--outputdir", str(self._outdir), str(self.app)]

            DllAnalyzer.logger.info("Decompiling dll %s... This may take awhile...", self.app.name)
            DllAnalyzer.logger.debug("Decompile command: \"%s\"", shlex.join(decompile_cmd))

            # Decompile the apk file
            proc = subprocess.Popen(decompile_cmd)
            proc.wait()


    def secret_search(self) -> None:
        """ 
        Perform secret search
        """
        # Write header
        self._write_header()

        # Decompile the App
        self._decompile_app()

        # Start searching for secrets
        self._search(self._outdir)
        