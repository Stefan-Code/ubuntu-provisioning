#!/bin/bash
if [[ $EUID -ne 0 ]]; then
   echo "You are not root!"
   exit 1
fi

export LC_ALL="en_US.UTF-8"
export LC_CTYPE="en_US.UTF-8"
dpkg-reconfigure locales

add-apt-repository universe
apt-get update
apt-get install --yes python3-dialog
sed -i '/preserve_hostname: false/c\preserve_hostname: true' /etc/cloud/cloud.cfg
