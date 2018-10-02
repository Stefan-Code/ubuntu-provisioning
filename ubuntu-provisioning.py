#! /usr/bin/env python3

import os
import locale
import subprocess
import sys
import shutil

from dialog import Dialog

locale.setlocale(locale.LC_ALL, '')

def shell(cmd):
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
    for line in proc.stdout:
        print(line.decode())
    proc.communicate()
    return proc.returncode


def set_hostname(hostname):
    with open('/etc/hostname', 'w+') as f:
        f.write(hostname)

def get_hostname():
    with open('/etc/hostname', 'r') as f:
        return f.readline().strip()

def ssh_reset():
    cmd = '/bin/rm -v /etc/ssh/ssh_host_*'
    if shell(cmd) != 0:
        error('Error resetting SSH keys! (removing old keys)')

    cmd = '/usr/sbin/dpkg-reconfigure openssh-server'
    if shell(cmd) != 0:
        error('Error resetting SSH keys! (generating new keys)')
    
def update():
    cmd = 'apt-get update --yes && apt-get upgrade --yes'
    if shell(cmd) != 0:
        error('Error updating: {} !'.format(proc.returncode), exit=False)

def error(message, exit=True, clear=True):
    d = Dialog(dialog='dialog')
    d.set_background_title('An error occured!')
    d.msgbox(message)
    if exit:
        if clear:
            os.system('clear')
        sys.exit(1)

def abort(message='Abort!', code=1, clear=True):
    if clear:
        os.system('clear')
    print(message)
    sys.exit(code)

def destroy_self():
    shutil.copy('.profile.original', '.profile')
    os.remove('.profile.original')
    os.remove(sys.argv[0])

def reboot():
    cmd = 'shutdown -r now'
    shell(cmd)
    sys.exit(0)

if __name__ == '__main__':
    d = Dialog(dialog='dialog',)
    d.set_background_title('Ubuntu VM provisioning')
    if d.yesno('This VM is built from a template and needs some work in order to be used safely!' +
               '\nDo you want to do that now?') != d.OK:
        abort()

    if os.geteuid() != 0:
        abort('You are not root!', clear=False)
    
    if d.yesno('Do you want to update the system?') == d.OK:
        print('Performing update')
        update()
    else:
        print('NOT performing update')

    code, hostname = d.inputbox('Set Hostname', init=get_hostname())

    if code == Dialog.OK:
        print('setting hostname to "{}"'.format(hostname))
        set_hostname(hostname)
    else:
        print('NOT setting hostname')

    if d.yesno("Reset SSH keys?") == d.OK:
        print("Resetting SSH keys")
        ssh_reset()
    else:
        print("NOT resetting SSH keys")
    if d.yesno('Remove this script?') == d.OK:
        print('destroying script', sys.argv[0])
        destroy_self()
    else:
        print('leaving provisioning script in place')
    
    if d.yesno('Reboot?') == d.OK:
        print('Rebooting!')
        reboot()
    else:
        print('NOT rebooting')

    d.msgbox('Done')
    os.system('clear')
