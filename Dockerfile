FROM ubuntu:22.04

###########################################################
# Build: docker build -t appalyzer .
# Run:   docker run -v /path/to/your/app:/data --rm -it appalyzer -f "/data/yourcoolapp.apk"
###########################################################

# libmagic and python-magic are used to get file types (equivalent to file command)

# avoid stuck build due to user prompt
ARG DEBIAN_FRONTEND=noninteractive

# Install OS packages and python modules
RUN apt update && apt upgrade -y && \
    apt install --no-install-recommends -y default-jre default-jdk libmagic-dev wget unzip git binutils \
        python3 python3-dev python3-venv python3-pip python3-wheel && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    pip3 install setuptools python-magic

# pip3 install setuptools python-magic --break-system-packages

# Set working dir to install additional utilities
WORKDIR /opt

# Install JADX-GUI
RUN wget --quiet https://github.com/skylot/jadx/releases/download/v1.4.7/jadx-1.4.7.zip -O jadx.zip && \
    unzip jadx.zip -d jadx && \
    rm -f /opt/jadx.zip

# Install ILSpy
RUN apt update && apt upgrade -y && \
    apt install -y wget apt-transport-https software-properties-common && \
    apt install -y dotnet-sdk-8.0 dotnet-runtime-8.0 && \
    wget --quiet https://github.com/PowerShell/PowerShell/releases/download/v7.4.2/powershell_7.4.2-1.deb_amd64.deb && \
    dpkg -i powershell_7.4.2-1.deb_amd64.deb && \
    rm powershell_7.4.2-1.deb_amd64.deb && \
    git clone https://github.com/icsharpcode/ILSpy.git && \
    cd ILSpy && \
    git submodule update --init --recursive && \    
    dotnet build ILSpy.XPlat.slnf

# Copy python code
WORKDIR /app
COPY ./src .

ENTRYPOINT [ "python3", "/app/AppalyzerCLI.py" ]

# DEBUG USE
#ENTRYPOINT ["/bin/sh"]