FROM ghcr.io/osgeo/gdal:ubuntu-full-3.12.0beta0

RUN apt-get update && apt-get -y install pip tippecanoe git python3.12-venv nano && rm -rf /var/lib/apt/lists/*

WORKDIR /root
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
RUN unzip awscliv2.zip
RUN ./aws/install

USER ubuntu
WORKDIR /home/ubuntu
RUN curl -fsSL https://pixi.sh/install.sh | sh
RUN echo 'eval "$(~/.pixi/bin/pixi shell-hook)"' >> .bashrc
RUN git clone https://github.com/fiboa/cli.git

WORKDIR /home/ubuntu/cli
RUN ~/.pixi/bin/pixi install

SHELL ["/bin/bash", "-c"]
CMD bash
