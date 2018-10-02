#! /usr/bin/env python3

import os
import locale
import subprocess
import sys
import shutil
import urllib.request

from dialog import Dialog

locale.setlocale(locale.LC_ALL, '')

def shell(cmd):
    """runs a shell command and returns the exit code"""
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
    for line in proc.stdout:
        print(line.decode())
    proc.communicate()
    return proc.returncode

def shell_get_output(cmd):
    """runs a shell command and returns the stdout of the command"""
    return subprocess.check_output(cmd, shell=True).decode()

def set_hostname(hostname):
    shell('hostnamectl set-hostname {}'.format(hostname))

def get_hostname():
    return shell_get_output('hostname').strip()

def logname():
    return shell_get_output('logname').strip()

def home_dir(user):
    return shell_get_output('eval echo ~{}'.format(user)).strip('\n')

def ssh_reset():
    cmd = '/bin/rm -v /etc/ssh/ssh_host_*'
    if shell(cmd) != 0:
        error('Error resetting SSH keys! (removing old keys)')

    cmd = '/usr/sbin/dpkg-reconfigure openssh-server'
    if shell(cmd) != 0:
        error('Error resetting SSH keys! (generating new keys)')

def patch_sudoers():
    with open('/etc/sudoers', 'r') as f:
        contents = f.read()
    if not '%admin ALL=(ALL) NOPASSWD: ALL' in contents:
        with open('/etc/sudoers', 'a') as f:
            f.write('\n#Allow members of the admin group to execute commands WITHOUT A PASSWORD!\n%admin ALL=(ALL) NOPASSWD: ALL\n')

def enable_autologin():
    config = ['[Service]', 'ExecStart=', 'ExecStart=-/sbin/agetty --autologin $USER --noclear %I $TERM']
    # ensure config directory exists
    shell('mkdir -p /etc/systemd/system/getty1@tty1.service.d/')
    with open('/etc/systemd/system/getty@tty1.service.d/override.conf', 'w') as f:
        f.write('\n'.join([line.replace('$USER', logname()) for line in config]))

def add_user_to_group(user, group):
    shell('usermod -a -G {} {}'.format(group, user))

def groupadd(group):
    shell('groupadd {}'.format(group))

def fix_sshd_config():
    commands = ['sed -i "s/.*PubkeyAuthentication.*/PubkeyAuthentication yes/g" /etc/ssh/sshd_config',
                'sed -i "s/.*PasswordAuthentication.*/PasswordAuthentication no/g" /etc/ssh/sshd_config',
                'sed -i "s/.*PermitRootLogin.*/PermitRootLogin no/g" /etc/ssh/sshd_config']
    exit_codes = [shell(command) for command in commands]

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

    if d.yesno("Allow passwordless sudo for admin group?") == d.OK:
        patch_sudoers()

    if d.yesno("Add user '{}' to admin group now?".format(logname())) == d.OK:
        groupadd('admin')
        add_user_to_group(logname(), 'admin')

    if d.yesno("Add Github keys to authorized_hosts?") == d.OK:
        code, user = d.inputbox('Github Username')
        if code == Dialog.OK:
            keys = urllib.request.urlopen('https://github.com/{}.keys'.format(user)).read().decode()
        if d.yesno("Are you sure to add these keys to user {}?\n\n{}".format(logname(), keys)) == d.OK:
            ssh_dir = os.path.join(home_dir(logname()), '.ssh')
            shell('mkdir -p {}'.format(ssh_dir))
            authorized_keys = os.path.join(ssh_dir, 'authorized_keys')
            with open(authorized_keys, 'a+') as f:
                f.write(keys)
            shell('chmod 644 {}'.format(authorized_keys))
            shell('chown {} {}'.format(logname(), authorized_keys))

    if d.yesno('Fix SSHD config to NOT permit password logins (public keys only)?') == d.OK:
        fix_sshd_config()

    if d.yesno("Enable tty autologin for user '{}'? This will reset existing tty1 configuration.".format(logname())) == d.OK:
        enable_autologin()

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
