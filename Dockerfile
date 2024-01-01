FROM ubuntu:latest

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
        python3.11 python3.11-dev python3.11-venv python3-pip python3-wheel && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    pip3 install --no-cache-dir --upgrade pip setuptools && \
    pip3 install --no-cache-dir python-magic

# Set working dir to install additional utilities
WORKDIR /opt

# Install JADX-GUI
RUN wget --quiet https://github.com/skylot/jadx/releases/download/v1.4.7/jadx-1.4.7.zip -O jadx.zip && \
    unzip jadx.zip -d jadx && \
    rm -f /opt/jadx.zip

# Install ILSpy
RUN wget --quiet https://packages.microsoft.com/config/ubuntu/22.04/packages-microsoft-prod.deb -O packages-microsoft-prod.deb && \
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

# Copy python code
WORKDIR /app
COPY ./src .

ENTRYPOINT [ "python3", "/app/AppalyzerCLI.py" ]

# DEBUG USE
#ENTRYPOINT ["/bin/sh"]