# tweaks of /etc/ssh/sshd_config
# xxx not implemented yet

# tweaks in /etc/hosts (replace actual hostname for loopback address)
# xxx not implemented yet

rm /etc/hostname

###
passwd --delete root
userdel --remove ubuntu
rm /etc/hostname

packages="iw ethtool
rsync make git
emacs24-nox
gcc make tcpdump wireshark bridge-utils
"

apt-get -y install $packages

####################
# udev
#
# see insightful doc in
# http://reactivated.net/writing_udev_rules.html 
#
# on ubuntu, to see data about a given device (udevinfo not available)
# udevadm info -q all -n /sys/class/net/p2p1
#  -- or --     (more simply)
# udevadm info /sys/class/net/p2p1
#  -- or --
# udevadm info --attribute-walk /sys/class/net/wlp1s0
# 
# create new udev rules for device names - hopefully fine on both distros ?
# 
# p2p1 = control = igb = enp3s0
# eth0 = data = e1000e = enp0s25

cat > /etc/udev/rules.d/70-persistent-net.rules <<EOF
# kernel name would be enp3s0
SUBSYSTEM=="net", ACTION=="add", DRIVERS=="igb", NAME="control"
# kernel name would be enp0s25
SUBSYSTEM=="net", ACTION=="add", DRIVERS=="e1000e", NAME="data"
EOF

# extra rules for fedora and wireless devices
# might work on ubuntu as well
# but was not used when doing the ubuntu15.04 image in the first place
cat > /etc/udev/rules.d/70-persistent-wireless.rules <<EOF
# this probably is the card connected through the PCI adapter
KERNELS=="0000:00:01.0", ACTION=="add", NAME="wlan0"
# and this likely is the one in the second miniPCI slot
KERNELS=="0000:04:00.0", ACTION=="add", NAME="wlan1"
EOF

# need to tweak /etc/sysconfig/network-scripts as well
# done manually:
# (*) renamed ifcfg-files
# renamed NAME= inside
# added DEVICE= inside


# need to tweak /etc/network/interfaces accordingly, of course
# turning on DHCP on the data interface cannot be tested on bemol (no data interface..)

cat > /etc/network/interfaces <<EOF
source /etc/network/interfaces.d/*

# The loopback network interface
auto lo
iface lo inet loopback

# the control network interface - required
auto control
iface control inet dhcp

# the data network interface - optional
auto data
#iface data inet dhcp
EOF

