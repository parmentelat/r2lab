SHELL=/bin/sh
HOME=/root
PATH=/root/bin:/bin:/usr/bin:/sbin:/usr/sbin:/usr/local/bin
python /root/r2lab/nightly/nightly.py -N all > /var/log/nightly.log 2>&1;