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
apt-get install --yes python3-dialog git
sed -i '/preserve_hostname: false/c\preserve_hostname: true' /etc/cloud/cloud.cfg
git clone https://github.com/Stefan-Code/ubuntu-provisioning.git && chown -R `logname`:$(id -gn $(logname)) ubuntu-provisioning/
provisioning_autorun="[ -f ~/ubuntu-provisioning/provisioning.py ] && sudo ~/ubuntu-provisioning/provisioning.py"
if [grep -qx "$provisioning_autorun" ~/.profile];
then
    echo ".profile already patched"
else
    echo "patching .profile"
    echo "$provisioning_autorun" >> ~/.profile
fi
./ubuntu-provisioning/provisioning.py
