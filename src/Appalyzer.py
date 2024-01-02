"""Base class used to decompile and search for secrets in applications"""
import threading
import datetime
import json
import shutil
import re
import logging
import subprocess
import hashlib
from pathlib import Path
from AppAnalyzerConfig import AppAnalyzerConfig
from AppalyzerObjects import RegExMatchPosition, RegExMatch


class Appalyzer():
    """
    Base class used to decompile and search for secrets in applications
    """

    logger = logging.getLogger(__name__)
    section_break = "*"*60
    TRUNCATE_LINE = 100
    TRUNCATE_SECRET = 80
    TRUNCATE_OFFSET = 80

    def __init__(self, app:str, regexfile:str=None):
        """        
        Parameters
        ----------
        app : str
            The path to the application to analyze (can be a file or directory)
        """
        self._config = AppAnalyzerConfig()
        self._thread_lock = threading.Lock()
        self._results = []
        self._time_now = datetime.datetime.now().strftime("%d-%m-%y_%H%M")
        self._outdir = Path(self._config.get_outdir_path())
        self._regexes = None
        self._curdir = Path().absolute()
        self._apptype = None
        self.app = Path(app)
        self._is_dir = bool(self.app.is_dir())
        self.outfile =  self.app.parent.joinpath(f"{self.app.name}_{self._time_now}_results.out")

        if regexfile:
            self._regexes = self.__process_regex_file(regexfile)
        else:
            self._regexes = self.__process_regex_file(self._config.get_regex_path())


    def __str__(self) -> str:
        """
        Print string representation of the class object

        Returns
        ----------
        str
            string representation of class object

        """
        output = None
        if self._is_dir:
            output = f"Process Dir: {self.app.absolute()}"

        else:
            filesize = self.get_filesize(self.app, unit="mb")
            md5sum = self.__get_md5(self.app)
            output = f"App: {self.app}\nFile Size: {filesize} mb \
                \nLocation: {self.app.parent} \
                \nMD5 Sum: {md5sum}"

        return output


    def __get_md5(self, file: str) -> str:
        """
        Return the md5 of the given file

        Returns
        ----------
        str
            string representation of hex bytes for md5 value
        """
        file_hash = hashlib.md5()

        with open(file, "rb") as fd:
            while chunk := fd.read(8192):
                file_hash.update(chunk)

        return file_hash.hexdigest()


    def __process_regex_file(self, regexfile:Path) -> dict[str, any]:
        """
        Injest json file containing regular expressions

        Parameters
        ----------
        regexfile : Path
            Absolute Path of regular expressions

        Returns
        ----------
        dict[str, any]
            A json object of regular expressions
        """

        Appalyzer.logger.info("Loaded regexes from file %s", regexfile)

        with open(regexfile, 'r', encoding="utf-8") as fd:
            regexes = json.load(fd)

        Appalyzer.logger.info("Loaded %s regular expressions", len(regexes))

        return regexes


    def _decompile_app(self) -> None:
        """ 
        Decompile the app and store in directory
        Process will take some time to decompile application
        """


    def _write_header(self) -> None:
        """
        Write a header to the outputfile
        """

        with open(self.outfile, "w", encoding="utf-8") as fd:

            fd.write(f"{Appalyzer.section_break}\n")
            fd.write(f"{str(self)}\n")
            fd.write(f"Date: {self._time_now}\n")
            fd.write(f"{Appalyzer.section_break}\n\n")


    def _run_strings(self, afile:str) -> None:
        """
        Run strings on a file
        """

        outfile = f"{afile}.strings"

        Appalyzer.logger.debug("Running strings on %s", afile)

        with open(outfile, "w", encoding="utf-8") as fd:
            strcmd = ["strings", "-a", str(afile)]
            proc = subprocess.Popen(strcmd, stdout=fd)
            proc.wait()

        Appalyzer.logger.debug("Result written to %s", outfile)


    def _get_dir_listing(self, target_dir:str) -> list[str]:
        """
        Return a list of all files in directory

        Parameters
        ----------
        target_dir : str
            Directory to get all files
         

        Returns
        ----------
        list[str]
            List of all files in directory
        """
        Appalyzer.logger.debug("Walking Directory %s to get list of files to process", target_dir)

        Appalyzer.logger.debug("Gettings all the files under %s", target_dir)
        p = Path(target_dir).glob('**/*')
        file_list = [x for x in p if x.is_file()]

        Appalyzer.logger.debug("Found %s files in directory %s", len(file_list), target_dir)

        return file_list


    def _finder(self, pattern:str, file_list:list, parent_dir:str) -> dict[str, RegExMatch]:
        """
        Search through directory using regular expressions

        Parameters
        ----------
        pattern : str
            Regular expression to match on

        path : str
            Directory of files to search through            

        Returns
        ----------
        dict[str, tuple[str, str]
            List of matches
        """

        matches = {}

        try:
            matcher = re.compile(pattern)

        except Exception as err:
            Appalyzer.logger.error("\n[!]Error: %s\n", err)

        else:

            for file_path in file_list:

                with open(file_path, "r", encoding="utf-8", errors='ignore') as fd:
                    lines = fd.readlines()

                try:
                    for line in lines:
                        mo = matcher.search(line)

                        if mo:
                            s = f"{str(file_path)}{mo.group()}"
                            h = hashlib.md5(s.encode('utf-8')).hexdigest()

                            rel_path = Path(file_path).relative_to(parent_dir)

                            if h not in matches:

                                a_match = RegExMatch(rel_path=rel_path,
                                                    line_match=line.strip(),
                                                    regex_match=mo.group(),
                                                    match_pos=RegExMatchPosition(
                                                    mo.start(),
                                                    mo.end()))

                                matches[h] = a_match

                                #print(f"Start: {mo.start()}, End: {mo.end()}, Group: {mo.group()}")
                                #matches[h] = (rel_path, mo.group(), line.strip())

                except Exception:
                    pass

        return matches


    def _extract(self, pattern_name:str, matches:dict[str, RegExMatch]) -> None:
        """
        Process any matches that have been found

        Parameters
        ----------
        pattern_name : str
            Regex pattern that was matched

        matches : dict[str, RegEx_Match]
            dictionary with all the matches
        """

        if len(matches):

            Appalyzer.logger.info("Pattern: %s, Num Matches: %s", pattern_name, len(matches))

            # Write results to file
            with self._thread_lock:
                with open(self.outfile, "a", encoding="utf-8") as fd:

                    fd.write(f"[+]{pattern_name}\n")
                    fd.write(f"{Appalyzer.section_break}\n")

                    for _, matchobj in matches.items():

                        secret = matchobj.regex_match
                        line = matchobj.line_match
                        rel_path = matchobj.rel_path

                        # For readability, truncate secret if it is more than 80 characters
                        if len(secret) > Appalyzer.TRUNCATE_SECRET:
                            secret = f"{secret[:Appalyzer.TRUNCATE_SECRET]}"

                        # Get the total length of the line
                        line_length = len(line)

                        if line_length > Appalyzer.TRUNCATE_LINE:

                            # Get the index of the secret
                            idx_start = line.find(secret)
                            idx_end = idx_start + len(secret)

                            # Get the offset positions
                            left_pos = idx_start - Appalyzer.TRUNCATE_OFFSET
                            right_pos = idx_end + Appalyzer.TRUNCATE_OFFSET

                            # Do some checking to make sure we don't go out of bounds
                            if left_pos < 0:
                                left_pos = 0

                            if right_pos > line_length:
                                right_pos = line_length

                            # Get the new line to print to file
                            line = line[left_pos:right_pos]

                        fd.write(f"- PATH: {rel_path}\
                                    \n  SECRET: {secret.strip()}\
                                    \n  LINE: {line}\n\n")

                    fd.write(f"{Appalyzer.section_break}\n\n")


    def _search(self, scan_dir:str) -> None:

        # Walk directory and save all the file paths
        file_list = self._get_dir_listing(scan_dir)

        Appalyzer.logger.info("Scanning Directory: %s", Path(scan_dir).absolute())
        Appalyzer.logger.info(" ** Be patient...  This could take a while...")

        thread_list = []
        # Loop through regexes
        for name, pattern in self._regexes.items():

            Appalyzer.logger.debug("[*] Starting regex search for %s", name)

            a_thread = threading.Thread(target=self._extract,
                                      args=(name, self._finder(pattern, file_list, scan_dir)))

            thread_list.append(a_thread)
            a_thread.start()

            Appalyzer.logger.debug("[*] Starting thread %s for %s", a_thread.ident, name)

        # Wait for the threads to finish or timeout is hit
        _ = [t.join(timeout=500) for t in thread_list]

        for thread in thread_list:
            if thread.is_alive():
                Appalyzer.logger.debug("[*] %s is still alive", thread.ident)

            else:
                Appalyzer.logger.debug("[*] %s is dead", thread.ident)


    def get_filesize(self, file_path:str, unit:str = 'bytes') -> int:
        """
        Get the size of a file

        Parameters
        ----------
        file_path : str
            Absolute Path of the file

        unit : str
            Size to return.  Valid selections are
                ['bytes', 'kb', 'mb', 'gb']
                Default is bytes

        Returns
        ----------
        int
            size of the file

        Raises
        ------
        ValueError
            If unit is not defined
        """

        exponents_map = {'bytes': 0, 'kb': 1, 'mb': 2, 'gb': 3}

        if unit not in exponents_map:
            raise ValueError("Must select from ['bytes', 'kb', 'mb', 'gb']")

        file_size = Path(file_path).stat().st_size
        size = file_size / 1024 ** exponents_map[unit]

        return round(size, 3)


    def secret_search(self):
        """ 
        Perform secret search
        """


    def cleanup(self) -> None:
        """
        Cleanup any temporary files created during execution
        """

        if self._outdir:
            shutil.rmtree(self._outdir.parent)

        cache_dir = Path(f"{self.app}.cache")
        if cache_dir.is_dir():
            shutil.rmtree(cache_dir)
