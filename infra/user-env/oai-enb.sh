#!/bin/bash
# configuration was about editing this file
# /root/openairinterface5g/targets/PROJECTS/GENERIC-LTE-EPC/CONF/enb.band7.tm1.usrpb210.epc.remote.conf
# in which we have
#
# * changed this line (was 92)
#     mobile_network_code =  "95";
#
# * changed this section to denote the remote (i.e. epc+hss) IP
#     mme_ip_address      = ( {ipv4 = "192.168.2.16";
#                              ipv6="192:168:30::17";
#                              active="yes";
#                              preference="ipv4";});
#
# changed the local IP address and interface name here
#
#     NETWORK_INTERFACES :
#    {
#        ENB_INTERFACE_NAME_FOR_S1_MME            = "data";
#        ENB_IPV4_ADDRESS_FOR_S1_MME              = "192.168.2.11/24";
#
#        ENB_INTERFACE_NAME_FOR_S1U               = "data";
#        ENB_IPV4_ADDRESS_FOR_S1U                 = "192.168.2.11/24";
#        ENB_PORT_FOR_S1U                         = 2152; # Spec 2152
#    };
#
# 
#
# then to run the node we did
### cd /root/openairinterface5g/cmake_targets/lte_build_oai/build
### ./lte-softmodem -O /root/openairinterface5g/targets/PROJECTS/GENERIC-LTE-EPC/CONF/enb.band7.tm1.usrpb210.epc.remote.conf
### 
### # need to align these 
### 
### epc:          {MCC="208" ; MNC="95";  TAC = "1"; },                                  # YOUR TAI CONFIG HERE
### 
### with
### 
### enb:    tracking_area_code  =  "1";
### 
###

DIRNAME=$(dirname "$0")
#echo Loading $DIRNAME/nodes.sh  >&2-
source $DIRNAME/nodes.sh

doc-sep "oai subcommands; run e.g. oai start"

####################
run_dir=/root/openairinterface5g/cmake_targets/lte_build_oai/build
lte_log="$run_dir/softmodem.log"
logs="$lte_log"
conf_dir=/root/openairinterface5g/targets/PROJECTS/GENERIC-LTE-EPC/CONF/
template=enb.band7.tm1.usrpb210.epc.remote.conf
config=r2lab.conf

requires_chmod_x="/root/openairinterface5g/targets/RT/USER/init_b200.sh"

realm="r2lab.fr"
oai_ifname=control
oai_subnet=3


doc-fun showenv "list environment variables"
function showenv() {
    echo "run_dir=$run_dir"
    echo "conf_dir=$conf_dir"
    echo "template=$template"
    echo "config=$config"
    echo "logs=\"$logs\""
}

# would make sense to add more stuff in the base image - see the NEWS file
base_packages="git libboost-all-dev libusb-1.0-0-dev python-mako doxygen python-docutils cmake build-essential libffi-dev
texlive-base texlive-latex-base ghostscript gnuplot-x11 dh-apparmor graphviz gsfonts imagemagick-common 
 gdb ruby flex bison gfortran xterm mysql-common python-pip python-numpy qtcore4-l10n tcl tk xorg-sgml-doctools
"

####################
doc-fun base "\tthe script to install base software on top of a raw image" 
function base() {

    gitup

    # apt-get requirements
    apt-update
    apt-get install -y $base_packages

    # 
    echo "========== Running git clone for openair-cn and r2lab and openinterface5g"
    cd
    echo -n | \
	openssl s_client -showcerts -connect gitlab.eurecom.fr:443 2>/dev/null | \
	sed -ne '/-BEGIN CERTIFICATE-/,/-END CERTIFICATE-/p' >> \
	    /etc/ssl/certs/ca-certificates.crt
    git clone https://gitlab.eurecom.fr/oai/openair-cn.git
    git clone https://gitlab.eurecom.fr/oai/openairinterface5g.git
    # this is probably useless, but well
    git clone https://github.com/parmentelat/r2lab.git

    echo "========== Setting up cpufrequtils"
    apt-get install -y cpufrequtils
    echo 'GOVERNOR="performance"' > /etc/default/cpufrequtils
    update-rc.d ondemand disable
    /etc/init.d/cpufrequtils restart
    # this seems to be purely informative ?
    cd
    cpufreq-info > cpufreq.info

    echo "========== Done - save image in oai-enb-base"
}

doc-fun build-uhd "builds UHD from github.com/EttusResearch/uhd.git"
function build-uhd() {
    echo "========== Building UHD"
    cd
    git clone git://github.com/EttusResearch/uhd.git
    cd uhd
    mkdir build
    cd build
    cmake ../host
    make
    make test
    make install
}

doc-fun build-oai5g "builds oai5g" 
function build-oai5g() {
    OPENAIR_HOME=/root/openairinterface5g
    # don't do this twice
    grep -q OPENAIR ~/.bashrc >& /dev/null || cat >> $HOME/.bashrc <<EOF
export OPENAIR_HOME=$OPENAIR_HOME
export OPENAIR1_DIR=$OPENAIR_HOME/openair1
export OPENAIR2_DIR=$OPENAIR_HOME/openair2
export OPENAIR3_DIR=$OPENAIR_HOME/openair3
export OPENAIRCN_DIR=$OPENAIR_HOME/openair-cn
export OPENAIR_TARGETS=$OPENAIR_HOME/targets
alias oairoot='cd $OPENAIR_HOME'
alias oai0='cd $OPENAIR0_DIR'
alias oai1='cd $OPENAIR1_DIR'
alias oai2='cd $OPENAIR2_DIR'
alias oai3='cd $OPENAIR3_DIR'
alias oait='cd $OPENAIR_TARGETS'
alias oaiu='cd $OPENAIR2_DIR/UTIL'
alias oais='cd $OPENAIR_TARGETS/SIMU/USER'
alias oaiex='cd $OPENAIR_TARGETS/SIMU/EXAMPLES'
EOF

    source $HOME/.bashrc

    cd $HOME/openairinterface5g/cmake_targets/
    # xxx l'original avait une seule ligne :
    ./build_oai -I -w USRP 2>&1 | tee build_oai-1.log
    ./build_oai --eNB -c -w USRP 2>&1 | tee build_oai-2.log

    # from this point on, instructions are really unclear
    #cd $HOME/openairinterface5g/
    #sudo chmod +x ./targets/bin/init_nas_nos1
    # xxx ici à nouveau c'est pas clair
    #./targets/bin/init_nas_nos1
    # this appeared in the original instructions from T. Turletti
    # eNB # eNB ready to run

}

doc-fun builds "\truns both builds"
function builds() {

    gitup
    cd
    
    build-uhd >& build-uhd.log

    build-oai5g >& build-oai5g.log

    echo "========== Done - save image in oai-enb-builds"
}

doc-fun configure "configures eNodeB (requires define-gw)"
function configure() {

    gw_id=$(get-peer)
    [ -z "$gw_id" ] && { echo "no peer defined"; return; }

    echo "Using gateway $gw_id"

    gitup
    id=$(r2lab-id)
    fitid=fit$id
    cd $conf_dir
    ### xxx TMP : we use eth1 instead of data
    # note that this requires changes in
    # /etc/network/interfaces as well
    # /etc/udev/rules.d/70..blabla as well
    cat <<EOF > oai-enb.sed
s,mobile_network_code =.*,mobile_network_code = "95";,
s,192.168.12.170,192.168.${oai_subnet}.$gw_id,
s,eth4,${oai_ifname},
s,192.168.12.242/24,192.168.${oai_subnet}.$id/24,g
EOF
    echo in $(pwd)
    sed -f oai-enb.sed < $template > $config
    echo "Overwrote $config in $(pwd)"
    cd - >& /dev/null
}

doc-fun start "starts lte-softmodem" 
function start() {
    echo Turning on interface $(data-up)
    cd $run_dir
#    echo "In $(pwd)"
    echo "Running lte-softmodem in background"
    ./lte-softmodem -O $conf_dir/$config >& $lte_log &
    cd - >& /dev/null
}

function _manage() {
    # if $1 is 'stop' then the found processes are killed
    mode=$1; shift
    pids="$(pgrep lte-softmodem)"
    pids="$(echo $pids)"
    if [ -z "$pids" ]; then
	echo "========== No running process"
	return 1
    fi
    echo "========== Found processes"
    ps $pids
    if [ "$mode" == 'stop' ]; then
	echo "========== Killing $pids"
	kill $pids
	echo "========== Their status now"
	ps $pids
    fi
}

doc-fun status "displays the status of the lte-softmodem processes"
function status() { _manage; }
doc-fun stop "displays the status of the lte-softmodem processes"
function stop() { _manage stop; }

####################
define_main

########################################
main "$@"
