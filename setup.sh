apt-get install python3-dialog
sed -i '/preserve_hostname: false/c\preserve_hostname: true' /etc/cloud/cloud.cfg
