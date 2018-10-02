add-apt-repository universe
apt-get update
apt-get install --yes python3-dialog
sed -i '/preserve_hostname: false/c\preserve_hostname: true' /etc/cloud/cloud.cfg
