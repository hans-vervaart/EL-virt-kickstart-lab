# EL-virt-kickstart-lab

## Replay EL compatible anaconda-ks.cfg files with virt-install

For several years I am using simple scripting to install VM's on my EL Linux PC.

`lab_ks VMNAME KICKSTART` Creates VMNAME from KICKSTART file.

This scripting simplyfies the 'replay' of the `anaconda-ks.cfg` file left in
the `/root` dir after an installation of a VM using
`virt-install` / `virt-manager`

By installing the `lab_ks.cgi` script in apache's `/var/www/cgi-bin`, creating
a dir `/var/www/html/ks-files` to store the `anaconda-ks.cfg` files and
download the desired iso images and store them in `/var/share/ISO`, VM's can
be kickstarted with `sudo lab_ks` or `lab_ks` (with `sudowrapper` installed).

```
LICENSE                   # GPLv3

lab_ks.cgi                # Install this in /var/www/cgi-bin
lab_ks                    # kickstart a new VM

lab_setup                 # Setup admin post install script

lab_add_disk              # Add a disk to a VM
lab_add_net               # Add a network to a VM
lab_extend_disk           # Extend a disk
lab_net                   # Setup a domain
lab_remove_kvm            # remove a VM
lab_update_etc_hosts      # IPs of VM in /etc/hosts will be updated
lab_wait_for_kvm_shutdown # Helper to wait for VMs to be shutdown
lab_wait_for_kvm_startup  # Helper to wait for VMs to be started
lab_webmount              # Mount ISO images for kisckstart
_option_processor         # insource for all scripts
sudowrapper               # script to run scripts from sudo
```

Move the example directory `ks-files/` (including `.post/`) to `/var/www/html`

```
ro85-serial-console       # Needs Rocky-8.5-x86_64-dvd1.iso in /var/share/ISO
al95-serial-console       # Needs AlmaLinux-9.5-x86_64-dvd.iso in /var/share/ISO
rh97-serial-console       # Needs rhel-9.7-x86_64-dvd.iso in /var/share/ISO 
```

Check out the comments section on top, the variables are providing the settings
required to kickstart without the need for more questions.
Only the hostname and kickstart-name are required (`lab_ks HOSTNAME KICKSTART`)

```
al95-serial-console:rootpw AlmaLinux
rh97-serial-console:rootpw RedHatLinux
ro85-serial-console:rootpw RockyLinux
```

## sudowrapper takes care of sudo

Install `sudowrapper`, `_option_processor`, `lab_wait_for_kvm_shutdown` and 
`lab_wait_for_kvm_startup` in the `/usr/local/bin`. Install the rest in the
`/usr/local/sbin` and setup cross-over symlinks like this:

The `/usr/local/bin` content:
```
lab_add_disk -> /usr/local/bin/sudowrapper
lab_add_net -> /usr/local/bin/sudowrapper
lab_extend_disk -> /usr/local/bin/sudowrapper
lab_ks -> /usr/local/bin/sudowrapper
lab_net -> /usr/local/bin/sudowrapper
lab_remove_kvm -> /usr/local/bin/sudowrapper
lab_update_etc_hosts -> /usr/local/bin/sudowrapper
lab_setup -> /usr/local/bin/sudowrapper
lab_wait_for_kvm_shutdown
lab_wait_for_kvm_startup
lab_webmount -> /usr/local/bin/sudowrapper
_option_processor
```

The `/usr/local/sbin` content:
```
lab_add_disk
lab_add_net
lab_extend_disk
lab_ks
lab_net
lab_remove_kvm
lab_setup
lab_wait_for_kvm_shutdown -> ../bin/lab_wait_for_kvm_shutdown
lab_wait_for_kvm_startup -> ../bin/lab_wait_for_kvm_startup
lab_webmount
_option_processor -> ../bin/_option_processor
```

All symlinks in `/usr/local/bin` pointing to sudowrapper, will run sudo first.

Interesting extra sudowrapper symlinks in `/usr/local/bin`:

```
virsh -> /usr/local/bin/sudowrapper
virt-manager -> /usr/local/bin/sudowrapper
```

For virt-manager sudowrapper provides X support from this extra file:

```
$ ls -l /etc/sudowrapper/virt-manager
-rw-r--r--. 1 root root 215 Apr 13  2020 /etc/sudowrapper/virt-manager
$
```

The content:

```
$ cat /etc/sudowrapper/virt-manager
NO_TTY='skip-sudo'
if   xhost 2> /dev/null | grep -q "^SI:localuser:$USER" && \
   ! xhost 2> /dev/null | grep -q "^SI:localuser:root"
then
   echo "Allow root to access the X server"
   xhost +SI:localuser:root
fi
$
```

### Quick lab setup

- Copy the desired `.iso` files into `/var/share/ISO`
- Copy the `ks-files/` (including the `.post/`) dir into `/var/www/html/`
- Create ssh keys (run `ssh-keygen`)
- Run `lab_setup admin-user $USER` (see `/var/www/html/ks-files/.post/admin-*`)

HaVe fun

Hans Vervaart

__GPLv3__ see _LICENCE_ file

