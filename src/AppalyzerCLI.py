"""CLI Module to Appalyzer"""
import argparse
from pathlib import Path
import sys
import json
import logging
import time
from AppAnalyzerConfig import AppAnalyzerConfig
from ApkAnalyzer import ApkAnalyzer
from IpaAnalyzer import IpaAnalyzer
from DirAnalyzer import DirAnalyzer
from ZipAnalyzer import ZipAnalyzer
from DllAnalyzer import DllAnalyzer

TYPES = ['android','ios']
FILE_EXT = ['apk', 'ipa', 'zip', 'jar', 'dll']

def banner():
	"""ASCII Art banner"""

	print("""
		
                                     _                               
     /\                             | |                              
    /  \     _ __    _ __     __ _  | |  _   _   ____   ___   _ __   
   / /\ \   | '_ \  | '_ \   / _` | | | | | | | |_  /  / _ \ | '__|  
  / ____ \  | |_) | | |_) | | (_| | | | | |_| |  / /  |  __/ | |     
 /_/    \_\ | .__/  | .__/   \__,_| |_|  \__, | /___|  \___| |_|     
            | |     | |                   __/ |                      
            |_|     |_|                  |___/                       

		""")


def exit_with_help(parser:argparse.ArgumentParser):
	"""
	Print help message and then exit
	"""
	parser.print_help(sys.stderr)
	sys.exit(1)


def configure_logging():
	"""
	Setup logging stuff
	"""

	appconfig = AppAnalyzerConfig()
	outdir = appconfig.get_outdir_path()
	fname = Path(__file__).name
	logfilename = Path(outdir).joinpath(f"{fname}.log")

	print(f"[*] Log file path: {logfilename}")

	# logger to write to file
	logging.basicConfig(level=logging.DEBUG,
						format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
						datefmt='%m-%d %H:%M',
						filename=logfilename,
						filemode='w')

	# define a Handler which writes INFO messages or higher to the sys.stderr
	console = logging.StreamHandler()
	console.setLevel(logging.INFO)
	# set a format which is simpler for console use
	formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
	# tell the handler to use this format
	console.setFormatter(formatter)
	# add the handler to the root logger
	logging.getLogger('').addHandler(console)


def main():
	"""Main Execution Module for Appalyzer"""

	# Print Banner
	banner()

	# Cofnigure logging
	configure_logging()

	# Get the uesr arguments
	parser = argparse.ArgumentParser(description="Search for secrets in a directory or application")

	# What to process: a file, directory containing decompiled app, etc...
	parser.add_argument("scanobj", help=f"Directory or Application file to scan.  Currently only supports apps with extensions, {FILE_EXT} ", type=str)
	parser.add_argument('--cleanup', help="Cleanup working directory on exit (Default = False)", dest='do_cleanup', action='store_true')
	parser.add_argument('-r', '--regex', help="Custom regex file to use in JSON format", dest='regex_file', type=str, default=None)
	args = parser.parse_args()

	# define some vars
	app_extension = None
	do_cleanup = args.do_cleanup
	appalyzer = None
	scanobj = Path(args.scanobj)
	regex_file = args.regex_file

	if regex_file:
		if Path(regex_file).is_file():
			regex_file = Path(regex_file)

			if (regex_file.suffix != ".json"):
				print(f"[!] {regex_file} must be a json file")
				exit_with_help(parser)

			try:
				with open(regex_file, encoding="utf-8") as fd:
					json.load(fd)

			except ValueError as e:
				print(f"[!] {regex_file} Does not appear to be valid json format, {e}")

			else:
				print(f"[+] {regex_file} contains valid JSON...")

		else:
			print(f"[!] {regex_file} - Regex file not found...")
			exit_with_help(parser)

	else:
		print("[*] Using default regex file")

	if Path(scanobj).is_dir():
		print("[+] Creating Directory scanner...")
		appalyzer = DirAnalyzer(scanobj, regex_file)

	elif Path(scanobj).is_file():

		app_extension = scanobj.suffix

		if (app_extension == ".apk" or app_extension == ".jar"):
			print("[*] Creating Android app scanner...")
			appalyzer = ApkAnalyzer(scanobj, regex_file)

		elif (app_extension == ".ipa"):
			print("[*] Creating iOS app scanner...")
			appalyzer = IpaAnalyzer(scanobj, regex_file)

		elif (app_extension == ".zip"):
			print("[*] Creating Zip analyzer scanner...")
			appalyzer = ZipAnalyzer(scanobj, regex_file)

		elif (app_extension == ".dll"):
			print("[*] Creating DLL analyzer scanner...")
			appalyzer = DllAnalyzer(scanobj, regex_file)

		else:
			print(f"[!] Unsupported file format: {app_extension}...")
			exit_with_help(parser)

	else:
		print(f"[!] {scanobj} Does not Exist...")
		exit_with_help(parser)

	start_time = time.time()
	if appalyzer:
		print(str(appalyzer))
		appalyzer.secret_search()
	
	end_time = time.time()
	time_diff = end_time - start_time

	if time_diff > 60:

		minutes_time_diff = round(time_diff/60,1)
		print(f"Search execution took {minutes_time_diff} minutes")

	else:
		print(f"Search execution took {time_diff} seconds")

	if do_cleanup and Path(scanobj).is_file():

		if appalyzer:
			print("[*] Cleaning up working directories....")
			appalyzer.cleanup()

if __name__ == '__main__':
	main()