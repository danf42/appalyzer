"""Base class used to decompile and search for secrets in applications"""
import datetime
import json
import shutil
import re
import logging
import subprocess
import hashlib
import concurrent.futures
from pathlib import Path
from AppAnalyzerConfig import AppAnalyzerConfig
from AppalyzerObjects import RegExMatchPosition, RegExMatch

class Appalyzer():
    """
    Base class used to decompile and search for secrets in applications
    """

    logger = logging.getLogger(__name__)
    LOGGER_FILENAME = "AppalyzerCLI.py.log"
    SECTION_BREAK = "*"*60
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

            fd.write(f"{Appalyzer.SECTION_BREAK}\n")
            fd.write(f"{str(self)}\n")
            fd.write(f"Date: {self._time_now}\n")
            fd.write(f"{Appalyzer.SECTION_BREAK}\n\n")


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


    def _finder(self, filename:str, parent_dir:str, regex_dict:dict[str:str]) -> dict[str, RegExMatch]:
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

        # Dont Scan the logger or output file
        if (Appalyzer.LOGGER_FILENAME in filename.name) or (self.outfile.name in filename.name):
            Appalyzer.logger.debug("[*]Skipping scanning for %s", filename)
            return None

        try:
            with open(filename, "r", encoding="utf-8", errors='ignore') as fd:
                content = fd.read()

        except Exception as err:
            Appalyzer.logger.error("\n[!]Error: %s\n", err)

        else:
            for name, pattern in regex_dict.items():

                try:
                    matcher = re.compile(pattern)

                except Exception as err:
                    Appalyzer.logger.error("\n[!]Error: %s\n", err)

                else:

                    mo = matcher.search(content)

                    if mo:
                        s = f"{str(filename)}{mo.group()}"
                        h = hashlib.md5(s.encode('utf-8')).hexdigest()

                        rel_path = Path(filename).relative_to(parent_dir)

                        if h not in matches:

                            left_pos = mo.start()
                            right_pos = mo.end()

                            # Calculate some context to save
                            content_lenth = len(content)

                            if content_lenth > Appalyzer.TRUNCATE_LINE:

                                left_pos = left_pos - Appalyzer.TRUNCATE_OFFSET
                                right_pos = right_pos + Appalyzer.TRUNCATE_OFFSET

                                # Do some checking to make sure we don't go out of bounds
                                left_pos = max(left_pos, 0)
                                right_pos = min(right_pos, content_lenth)

                            m = content[left_pos:right_pos]

                            Appalyzer.logger.debug("\n\nMatch Found:\n\t%s\n\t%s\n\t%s\n\n",
                                                   name, rel_path, mo.group())

                            a_match = RegExMatch(rel_path=rel_path,
                                                absolute_path=filename,
                                                line_match=m.strip(),
                                                regex_match=mo.group(),
                                                regex_name=name.strip(),
                                                match_pos=RegExMatchPosition(left_pos, right_pos))

                            matches[h] = a_match

        return matches


    def _extract(self, matches:list[RegExMatch]) -> None:
        """
        Process any matches that have been found

        Parameters
        ----------
        matches : list[RegExMatch]
            list of all the matches
        """

        if len(matches):

            # Sort the matches by regex hit
            sorted_matches: dict[str, list] = {}
            for match in matches:

                for _, matchobj in match.items():

                    regex_name = matchobj.regex_name

                    if regex_name in sorted_matches:

                        l = sorted_matches[regex_name]
                        l.append(matchobj)
                        sorted_matches[regex_name] = l

                    else:
                        sorted_matches[regex_name] = [matchobj]

            # Write results to file
            with open(self.outfile, "a", encoding="utf-8") as fd:

                # iterate through sorted matches
                for key, matchlist in sorted_matches.items():

                    fd.write(f"[+]{key}\n")
                    fd.write(f"{Appalyzer.SECTION_BREAK}\n")

                    for matchobj in matchlist:

                        regex_name = matchobj.regex_name
                        secret = matchobj.regex_match
                        line = matchobj.line_match
                        rel_path = matchobj.rel_path

                        fd.write(f"- PATH: {rel_path}\
                                    \n  RegEx: {regex_name}\
                                    \n  SECRET: {secret.strip()}\
                                    \n  LINE: {line}\n\n")

                    fd.write(f"{Appalyzer.SECTION_BREAK}\n")

    def _search(self, scan_dir:str) -> None:

        # Walk directory and save all the file paths
        file_list = self._get_dir_listing(scan_dir)

        Appalyzer.logger.info("Scanning Directory: %s", Path(scan_dir).absolute())
        Appalyzer.logger.info(" ** Be patient...  This could take a while...")

        with concurrent.futures.ThreadPoolExecutor(thread_name_prefix='LocalSecretScanner_') as executor:
            results = list(executor.map(self._finder, file_list,
                                        [scan_dir]*len(file_list),
                                        [self._regexes]*len(file_list)))

        # Filter all the empty results
        results = list(filter(None, results))

        # Extract all the matches and write to the output file
        self._extract(results)


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
