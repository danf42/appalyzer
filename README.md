# Appalyzer

Appalyzer is a tool that helps scan for secrets and other interesting strings in files.

Appalyzer currently supports scanning for secrets in:

- Android (*.apk) files
- iOS (*.ipa) files
- .Net DLL (*.dll) files
- JAR (*.jar) files
- ZIP (*.zip) files
- Directories

## Design

Appalyzer uses a JSON formatted list of Python-friendly regular expressions to search for interesting data.  The current list of regular expressions are based on common regexes used in other tools, bug bounty programs, etc.  Decompiling of apps attempts to use industry standard tools to do the heavy lifting.  If no tools is specified, the application will attempt to just read the file in.  Once the application is decompiled and processed, the application will search search for secrets and sensitive data based on the regular expressions supplied.

### Android (apk) and Java Archive Files (jar)

- Uses JADX to decompile the apk file

### iOS (ipa)

- Unzip the ipa file
- Identify the <application_name>.app directory
- Run `strings` on all binary files (i.e. "Mach-O 64-bit arm64"), `*.car` files, and `*.mobileprovision` files
- Use the Python module `plistlib` to extract data from from all plist files

### .Net DLL (dll)

- Use `ilspycmd` to decompile the `*.dll` file

### ZIP (zip)

- Use Python's builtin `zipfile` module to unzip the file

### Directories

- Iterate through files in a directories attempting to read in each file

## Installation

Appalyzer should be installed using the Docker container or in a Linux environment.

Clone this repository and change directory to `appalyzer`

### Docker

Build the container

```bash
docker build -t appalyzer .
```

### Standalone

1. Install all the dependencies

  ```bash
  sudo bash ./install.sh
  ```

2. Update the `config.ini` file with following

  ```text
  [default]
  JADX_PATH=/opt/jadx/bin/jadx
  ILSPYCMD_PATH=/opt/ILSpy/ICSharpCode.ILSpyCmd/bin/Debug/net8.0/ilspycmd
  REGEX_PATH=secrets_regexes_full.json
  OUTDIR_PATH=/data
  ```

## Usage

Appalyzer can be run from a docker container and is the perferred execution method.

```bash
usage: AppAnalyzerCli.py [-h] [--cleanup] scanobj

Search for secrets in a directory or application

positional arguments:
  scanobj               Directory or Application file to scan. Currently only supports apps with extensions, ['apk', 'ipa']

options:
  -h, --help            show this help message and exit
  --cleanup             Cleanup working directory on exit (Default = False)
  -r REGEX_FILE, --regex REGEX_FILE
                        Custom regex file to use in JSON format
  ```

### Running in Docker Container

Run the application in the container

- Searching for secrets in a Directory

  ```bash
  docker run -v /dir/with/secrets:/data --rm -it appalyzer "/data"
  ```

  Data will be saved to `/dir/with/secrets`

- Searching for secrets in supported file types

  ```bash
  docker run -v /path/to/your/app:/data --rm -it appalyzer "/data/yourcoolapp.apk"
  ```

  Data will be saved to `/path/to/your`

### Running Standalone

Run the application from the commandline

- Searching for secrets in a Directory

  ```bash
  python3 ./AppalyzerCLI.py /dir/to/scan
  ```

- Searching for secrets in supported file types

  ```bash
  python3 ./AppalyzerCLI.py /path/to/yourcoolapp.apk
  ```

## Future Improvments

- Ongoing improvements to the regular expressions
- Improve processing of supported file types, especially `ipa` files
- Add a customizable way to only select specific regular expressions to search for
- Add support for searching for high entropy data

## Acknowledgements

The regexes used have been collected over time from others' blog posts and code repos.  
