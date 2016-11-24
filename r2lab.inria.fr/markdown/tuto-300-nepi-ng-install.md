title: Installing nepi-ng
tab: tutorial
skip_header: True

<script src="/assets/r2lab/open_tab.js"></script>
<script src="/assets/js/diff.js"></script>
<script src="/assets/r2lab/r2lab-diff.js"></script>
<style>@import url("/assets/r2lab/r2lab-diff.css")</style>

<ul class="nav nav-tabs">
  <li class="active"> <a href="#INSTALL">INSTALL</a> </li>
  <li> <a href="#SSHAGENT">SSH AGENT</a></li>

  << include r2lab/tutos-index.html >>
</ul>

<div id="contents" class="tab-content" markdown="1">

<!------------ INSTALL ------------>
<div id="INSTALL" class="tab-pane fade in active" markdown="1">

The commands that we have seen in the previous tutorial are useful for
making quick changes on the testbed.

However once you are set up, it is much more convenient to control
experiments right from your own laptop, and to this end we provide a
set of tools that we collectively refer to as `nepi-ng`. This page
gives you detailed instructions for installing these.

## Terminal-based

All the tools that we will write will run in a terminal, we assume you are familiar with dealing with such interfaces.

## Requires python-3.5

`nepi-ng` is a set of python libraries; these use [the `asyncio` library](https://docs.python.org/3/library/asyncio.html), 
and as such require python-3.5 (as we use the latest `async def` and `await` syntax, that won't work under python-3.4).
Please refer to the python documentation for installing that version of python on your laptop.
You can check that this requirement is fulfilled by running

    $ python3 --version
    Python 3.5.1

## Installing `asynciojobs` and `apssh`


You need to install these libraries, the recommended way is through
`pip3` like this (if you're not using `virtualenv` or ` anaconda`, you
might need to run these commands under `sudo`)

    pip3 install asynciojobs apssh

Note that for upgrading to the latest release published on `pypi.org`, you need to run

    pip3 install --upgrade asynciojobs apssh

You can check the installed versions like this

    $ python3 -c 'from asynciojobs import version; print(version.version)'
    0.2.3
    $ python3 -c 'from apssh import version; print(version.version)'
    0.2.17

</div>

<!------------ SSHAGENT ------------>
<div id="SSHAGENT" class="tab-pane fade" markdown="1">

## Note on ssh and ssh-agent

`nepi-ng` **does not require** a native ssh client to be installed on
your laptop, as it uses the great `asyncssh` library instead. However,
it is recommended to have one installed, if only for running an ssh
agent, as using ssh repeatedly is almost impossible without an
ssh-agent.

You will see that in all the code of these tutorials, there is no
option to specify an alternate key. This is because all the examples
in this tutorial use **the set of keys known to your ssh agent**.

You can inspect and manage this set of keys using the `ssh-add`
command - at least on unix-based systems.

    ~/.ssh $ ssh-add -l
    1024 SHA256:KNm0U4SgFV9bY957hJAIRR68n5AZHQ6e1gbiXrGHuOA onelab.private (RSA)
    ~/.ssh $ ssh-add onelab.private
    Enter passphrase for onelab.private:
    Identity added: onelab.private (onelab.private)
    ~/.ssh $ ssh-add -l
    1024 SHA256:KNm0U4SgFV9bY957hJAIRR68n5AZHQ6e1gbiXrGHuOA /Users/parmentelat/.ssh/id_rsa (RSA)
    2048 SHA256:WvCdpP+FHBTnkwbkqYl43GVgwEK2iYdwRaNm+fCc+Xg onelab.private (RSA)

</div>

</div> <!-- end div contents -->