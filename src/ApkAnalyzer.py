"""Class used to decompile and search for secrets in Android Mobile Applications"""
import shlex
import subprocess
import logging
from Appalyzer import Appalyzer

class ApkAnalyzer(Appalyzer):
    """
    Class used to decompile and search for secrets in Android Mobile Applications
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
        jadx_path = self._config.get_jadx_path()

        # Create the decompile command
        decompile_cmd = [str(jadx_path), "--output-dir", str(self._outdir), str(self.app)]

        ApkAnalyzer.logger.info("Decompiling app %s... This may take awhile...", self.app.name)
        ApkAnalyzer.logger.debug("Decompile command: \"%s\"", shlex.join(decompile_cmd))

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
        