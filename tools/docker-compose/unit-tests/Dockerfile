FROM gcr.io/ansible-tower-engineering/awx_devel:latest

# For UI tests
RUN yum install -y pango libXcomposite libXcursor libXdamage \
  libXext libXi libXtst cups-libs libXScrnSaver libXrandr GConf2 alsa-lib atk \
  gtk3 ipa-gothic-fonts xorg-x11-fonts-100dpi xorg-x11-fonts-75dpi \
  xorg-x11-utils xorg-x11-fonts-cyrillic xorg-x11-fonts-Type1 \
  xorg-x11-fonts-misc

RUN npm set progress=false

WORKDIR "/awx_devel"

ADD tools/docker-compose/unit-tests/entrypoint.sh /
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
