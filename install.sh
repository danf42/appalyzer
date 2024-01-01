#!/bin/bash

readonly WORKDIR="/opt"
readonly CWD=$(pwd)

# Check if running as root
is_root() {

  if [[ "$EUID" -eq 0 ]]; then
    return 0
  else
    return 1
  fi

}

# Install ILSpy into the WORKDIR
install_ilspy() {

  echo "Installing ILSpy..."
  cd $WORKDIR
  wget --quiet https://packages.microsoft.com/config/ubuntu/22.04/packages-microsoft-prod.deb -O packages-microsoft-prod.deb && \
    dpkg -i packages-microsoft-prod.deb && \
    rm -f packages-microsoft-prod.deb && \
    apt-get update && \
    apt install -y dotnet-host dotnet-sdk-8.0 && \
    wget --quiet https://github.com/PowerShell/PowerShell/releases/download/v7.4.0/powershell_7.4.0-1.deb_amd64.deb -O powershell.deb && \
    dpkg -i powershell.deb && \
    rm -f powershell.deb && \
    git clone https://github.com/icsharpcode/ILSpy.git && \
    cd ILSpy && \
    git submodule update --init --recursive && \
    dotnet build ILSpy.XPlat.slnf

  cd $CWD

}

# Install JDAX into the WORKDIR
install_jdax() {

  # Install JDAX
  echo "Install JDAX"
  cd $WORKDIR
  wget --quiet https://github.com/skylot/jadx/releases/download/v1.4.7/jadx-1.4.7.zip -O jadx.zip && \
    unzip jadx.zip -d jadx && \
    rm -f /opt/jadx.zip

  cd $CWD

}

# Install OS and python dependencies
install_dependencies() {

  echo "Install Required OS packages and Python3 modules"

  apt update && apt upgrade -y && \
    apt install --no-install-recommends -y default-jre default-jdk libmagic-dev wget unzip git binutils \
      python3.11 python3.11-dev python3.11-venv python3-pip python3-wheel && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    pip3 install --no-cache-dir --upgrade pip setuptools && \
    pip3 install --no-cache-dir python-magic

}

# Print usage of the script.  
# Uses here-document syntax
usage() {
	cat <<- EOF
 
	This script will install the dependenceis required to run Appalyzer.

	It MUST be run as root! 

	EOF
}

main() {
  
  if ! is_root ; then
    usage
    exit 1
  fi

  # Create work directory if it doesn't exist
  if [ ! -d "$WORKDIR" ]; then
    echo "$WORKDIR does not exist, creating it now..."
    mkdir $WORKDIR
  fi

  install_dependencies

  install_jdax

  install_ilspy

  echo "Setup is now complete"
 }

 main
