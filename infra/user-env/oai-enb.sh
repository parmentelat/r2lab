#!/bin/bash

source $(dirname $(readlink -f $BASH_SOURCE))/nodes.sh

doc-nodes-sep "#################### For managing an OAI enodeb"

source $(dirname $(readlink -f $BASH_SOURCE))/oai-common.sh

run_dir=/root/openairinterface5g/cmake_targets/lte_build_oai/build
lte_log="$run_dir/softmodem.log"
add-to-logs $lte_log
lte_pcap="$run_dir/softmodem.pcap"
add-to-datas $lte_pcap
conf_dir=/root/openairinterface5g/targets/PROJECTS/GENERIC-LTE-EPC/CONF/
#template=enb.band7.tm1.usrpb210.epc.remote.conf
template=enb.band7.tm1.usrpb210.conf
config=r2lab.conf
add-to-configs $conf_dir/$config

#requires_chmod_x="/root/openairinterface5g/targets/RT/USER/init_b200.sh"

doc-nodes dumpvars "list environment variables"
function dumpvars() {
    echo "oai_role=${oai_role}"
    echo "oai_ifname=${oai_ifname}"
    echo "oai_realm=${oai_realm}"
    echo "run_dir=$run_dir"
    echo "conf_dir=$conf_dir"
    echo "template=$template"
    [[ -z "$@" ]] && return
    echo "_configs=\"$(get-configs)\""
    echo "_logs=\"$(get-logs)\""
    echo "_datas=\"$(get-datas)\""
    echo "_locks=\"$(get-locks)\""
}

####################
doc-nodes image "the entry point for nightly image builds"
function image() {
    deps_arg="$1"; shift
    dumpvars
    base
    deps "$deps_arg"
    build
}

####################
# would make sense to add more stuff in the base image - see the NEWS file
base_packages="git subversion libboost-all-dev libusb-1.0-0-dev python-mako doxygen python-docutils cmake build-essential libffi-dev
texlive-base texlive-latex-base ghostscript gnuplot-x11 dh-apparmor graphviz gsfonts imagemagick-common 
 gdb ruby flex bison gfortran xterm mysql-common python-pip python-numpy qtcore4-l10n tcl tk xorg-sgml-doctools
 i7z
"

doc-nodes base "the script to install base software on top of a raw image" 
function base() {

    git-pull-r2lab
    git-pull-oai

    # apt-get requirements
    apt-get update
    apt-get install -y $base_packages

    # 
    git-ssl-turn-off-verification
##   No need to clone openair-cn for eNB
##    echo "========== Running git clone for openair-cn and r2lab and openinterface5g"
    echo "========== Running git clone for r2lab and openinterface5g"
    cd
##    [ -d openair-cn ] || git clone https://gitlab.eurecom.fr/oai/openair-cn.git
    [ -d openairinterface5g ] || git clone https://gitlab.eurecom.fr/oai/openairinterface5g.git
    [ -d /root/r2lab ] || git clone https://github.com/parmentelat/r2lab.git

##    Following is now done in the ubuntu-lowlatency image as it requires a reboot to be active
##
#    echo "========== Setting up cpufrequtils"
#    apt-get install -y cpufrequtils
#    echo 'GOVERNOR="performance"' > /etc/default/cpufrequtils
#    update-rc.d ondemand disable
#    /etc/init.d/cpufrequtils restart
#    # this seems to be purely informative ?
#    cd
#    cpufreq-info > cpufreq.info
#
#    # xxx turning off hyperthreading : adding noht to the line below does not seem to work
#    sed -i -e 's|GRUB_CMDLINE_LINUX_DEFAULT.*|GRUB_CMDLINE_LINUX_DEFAULT="quiet intel_pstate=disable processor.max_cstate=1 intel_idle.max_cstate=0 idle=poll"|' /etc/default/grub
#    update-grub

}

## Following is no more useful as uhd must be installed within OAI build
##
#doc-nodes deps "builds uhd for an oai image"
#function deps() {
#    # arg1 should be uhd-ettus or uhd-oai
#    
#    git-pull-r2lab
#    git-pull-oai
#    case $1 in
#	uhd-ettus)
#	    echo Building UHD with ETTUS recipe
#	    build-uhd-ettus ;;
#	uhd-oai)
#	    echo Building UHD with OAI recipe
#	    build-uhd-oai ;;
#	*)
#	    echo unkwown argument $1 to deps
#	    exit 1 ;;
#    esac
#}
# xxx Rohit says this is WRONG - use oai recipe instead
#doc-nodes build-uhd-ettus "builds UHD from github.com/EttusResearch/uhd.git"
#function build-uhd-ettus() {
#    cd
#    echo "========== Building UHD from ettus git repo"
#    if [ -d uhd ]; then
#	cd uhd; git pull
#    else
#	git clone git://github.com/EttusResearch/uhd.git
#	cd uhd
#    fi
#    mkdir -p build
#    cd build
#    cmake ../host
#    make
#    make test
#    make install
#}
#
#doc-nodes build-uhd-oai "build UHD using the OAI recipe" 
#function build-uhd-oai() {
#    git-pull-r2lab
#    git-pull-oai
#    cd /root/openairinterface5g/cmake_targets
##    run-in-log build-uhd.log ./build_oai -I --install-optional-packages -w USRP
#    run-in-log build-uhd.log ./build_oai -I -w USRP
#}

doc-nodes build "builds oai5g for an oai image"
function build() {

    git-pull-r2lab
    git-pull-oai

    cd
    echo Building OAI5G - see $HOME/build-oai5g.log
    build-oai5g -x >& build-oai5g.log

}

doc-nodes build-oai5g "builds oai5g - run with -x for building with software oscilloscope" 
function build-oai5g() {

    oscillo=""
    if [ -n "$1" ]; then
	case $1 in
	    -x) oscillo="-x" ;;
	    *) echo "usage: build-oai5g [-x]"; return 1 ;;
	esac
    fi

##   It is better to source directly OAI configuration file to get possible future changes from them
    cd /root/openairinterface5g
    source oaienv
#    OPENAIR_HOME=/root/openairinterface5g
#    # don't do this twice
#    grep -q OPENAIR ~/.bashrc >& /dev/null || cat >> $HOME/.bashrc <<EOF
#export OPENAIR_HOME=$OPENAIR_HOME
#export OPENAIR1_DIR=$OPENAIR_HOME/openair1
#export OPENAIR2_DIR=$OPENAIR_HOME/openair2
#export OPENAIR3_DIR=$OPENAIR_HOME/openair3
#export OPENAIRCN_DIR=$OPENAIR_HOME/openair-cn
#export OPENAIR_TARGETS=$OPENAIR_HOME/targets
#alias oairoot='cd $OPENAIR_HOME'
#alias oai0='cd $OPENAIR0_DIR'
#alias oai1='cd $OPENAIR1_DIR'
#alias oai2='cd $OPENAIR2_DIR'
#alias oai3='cd $OPENAIR3_DIR'
#alias oait='cd $OPENAIR_TARGETS'
#alias oaiu='cd $OPENAIR2_DIR/UTIL'
#alias oais='cd $OPENAIR_TARGETS/SIMU/USER'
#alias oaiex='cd $OPENAIR_TARGETS/SIMU/EXAMPLES'
#EOF
    source $HOME/.bashrc

    cd $OPENAIR_HOME/cmake_targets/

    echo Building in $(pwd) - see 'build*log'
#    run-in-log build-oai-1.log ./build_oai -I -w USRP
#    run-in-log build-oai-2.log ./build_oai --eNB -c -w USRP $oscillo
    run-in-log build-oai-1.log ./build_oai -I --eNB $oscillo --install-system-files -w USRP
    run-in-log build-oai-2.log ./build_oai -w USRP $oscillo -c --eNB
#    [ -n "$oscillo" ] && run-in-log build-oai-3.log ./build_oai -x

}

########################################
# end of image
########################################

# entry point for global orchestration
doc-nodes run-enb "run-enb 23: does init/configure/start with epc running on node 23"
function run-enb() {
    peer=$1; shift
    # pass exactly 'False' to skip usrp-reset
    reset_usrp=$1; shift
    oai_role=enb
    stop
    status
    init
# following should be configure str(int($peer))
    configure 03
    if [ "$reset_usrp" == "False" ]; then
	echo "SKIPPING USRP reset"
    else
	usrp-reset
    fi
    start-tcpdump-data ${oai_role}
    start
    status
    return 0
}

# the output of start-tcpdump-data
add-to-datas "/root/data-${oai_role}.pcap"

####################
doc-nodes init "initializes clock after NTP, and tweaks MTU's"
function init() {

    git-pull-r2lab   # calls to git-pull-oai should be explicit from the caller if desired
    # clock
    init-ntp-clock
    # data interface if relevant
    [ "$oai_ifname" == data ] && echo Checking interface is up : $(turn-on-data)
#    echo "========== turning on offload negociations on ${oai_ifname}"
#    offload-on ${oai_ifname}
    echo "========== setting mtu to 9000 on interface ${oai_ifname}"
## To check if following is still useful today with new GTP
    ip link set dev ${oai_ifname} mtu 9000
}

####################
function configure() {
    configure-enb "$@"
}
doc-nodes configure "function"

doc-nodes configure "configure eNodeB (requires define-peer)"
function configure-enb() {

    # pass peer id on the command line, or define it it with define-peer
    gw_id=$1; shift
    [ -z "$gw_id" ] && gw_id=$(get-peer)
    [ -z "$gw_id" ] && { echo "configure-enb: no peer defined - exiting"; return; }
    gw_id=$(printf %d $gw_id)
    echo "ENB: Using gateway (EPC) on $gw_id"

    git-pull-r2lab   # calls to git-pull-oai should be explicit from the caller if desired
    id=$(r2lab-id)
    fitid=fit$id
    cd $conf_dir
    ### xxx TMP : we use eth1 instead of data
    # note that this requires changes in
    # /etc/network/interfaces as well
    # /etc/udev/rules.d/70..blabla as well
    # xxx on his printed stabyloed configs, Thierry T
    # had also changed this
    #s|eNB_name[ 	]*=.*|eNB_name = "softmodem_$fitid";|
    # but I suspect it actually causes this
    # r2lab.conf, mismatch between 1 active eNBs and 0 corresponding defined eNBs !
    cat <<EOF > oai-enb.sed
s|pdsch_referenceSignalPower[ 	]*=.*|pdsch_referenceSignalPower = -24;|
s|mobile_network_code[ 	]*=.*|mobile_network_code = "95";|
s|mme_ip_address[ 	]*=.*|mme_ip_address = ( { ipv4 = "192.168.${oai_subnet}.$gw_id";|
s|ENB_INTERFACE_NAME_FOR_S1_MME[ 	]*=.*|ENB_INTERFACE_NAME_FOR_S1_MME = "${oai_ifname}";|
s|ENB_INTERFACE_NAME_FOR_S1U[ 	]*=.*|ENB_INTERFACE_NAME_FOR_S1U = "${oai_ifname}";|
s|ENB_IPV4_ADDRESS_FOR_S1_MME[ 	]*=.*|ENB_IPV4_ADDRESS_FOR_S1_MME = "192.168.${oai_subnet}.$id/24";|
s|ENB_IPV4_ADDRESS_FOR_S1U[ 	]*=.*|ENB_IPV4_ADDRESS_FOR_S1U = "192.168.${oai_subnet}.$id/24";|
EOF
# s,tx_gain.*,tx_gain = 80;,
# s,rx_gain.*,rx_gain = 80;,
    echo in $(pwd)
    sed -f oai-enb.sed < $template > $config
    echo "Overwrote $config in $(pwd)"
    cd - >& /dev/null
}

####################
doc-nodes start "starts lte-softmodem - run with -d to turn on soft oscilloscope" 
function start() {

    oscillo=""
    if [ -n "$1" ]; then
	case $1 in
	    -d) oscillo="-d" ;;
	    *) echo "usage: start [-d]"; return 1 ;;
	esac
    fi

cd $run_dir
#    echo "In $(pwd)"
    echo "Running lte-softmodem in background"
    ./lte-softmodem -P softmodem.pcap --ulsch-max-errors 100 -O $conf_dir/$config $oscillo >& $lte_log &
    cd - >& /dev/null
}

doc-nodes status "displays the status of the softmodem-related processes"
doc-nodes stop "stops the softmodem-related processes"

function -list-processes() {
    pids="$(pgrep lte-softmodem)"
    echo $pids
}

########################################
define-main "$0" "$BASH_SOURCE"
main "$@"
