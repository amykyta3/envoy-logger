# Run as a System Service (on Linux) Instructions

This guide may be used to setup a service account and run `envoy_logger` (with
auto-restart) on a modern Linux system.

See the [setup instructions](https://github.com/amykyta3/envoy-logger/blob/main/docs/Setup-Instructions.md)
for an overall guide.

*** WARNING ***

Your Enlighten username and password as well as an API token that can be used to
access your Envoy/Gateway will be stored in plain text in files in the home
directory of the service account created in this guide.  Do not use this method
on shared servers, servers exposed to the Internet, or otherwise in environments
where access to the server is not well controlled.

Additionally, it would be a good idea to setup a second Enlighten account and
grant access to it instead of using your "Owner" account.

https://support.enphase.com/s/article/How-can-I-add-users-to-my-Enlighten-account

## 1. Prepare Python

Generally speaking, the more Python modules you can install via your OS package
manager, the better.  Modules installed via your OS package manager will
automatically be updated as you update your OS.

The list of modules required by `envoy_logger` can by found in the top-level
[setup.py](https://github.com/amykyta3/envoy-logger/blob/main/setup.py) file.

Your OS may not supply all required modules, and that's okay.  On a Rocky Linux
9 server with the EPEL repository enabled, most required modules can be
installed via:

    sudo dnf install \
        python3-pip \
        python3-reactivex \
        python3-certifi \
        python3-influxdb \
        python3-appdirs

At a minimum, ensure that at least PIP is installed.

## 2. Create Service Account

Create a dedicated user account (service account) under which the `envoy_logger`
service will run.  The username doesn't matter - just remember what you chose
and substitute as appropriate.

    sudo useradd -c 'Envoy Logger' envoylog

Restrict access to the service account home directory.

    sudo chmod 700 ~envoylog

`~envoylog` is a shortcut to the home directory of the `envoylog` user.  Be
careful that you don't accidentally put a space between the `~` and user name
(`~` on its own is a shortcut to the current user's home directory).

## 3. Install and Configure `envoy_logger` Under the Service Account

The remaining Python modules, including `envoy_logger` itself, will be installed
locally in the service account's home directory.  Become the service account,
then install the remaining software.

    sudo -u envoylog -i
    pip3 install --user git+https://github.com/amykyta3/envoy-logger

While still logged in as the service account, create a `config.yml` file using
[the example configuration](https://github.com/amykyta3/envoy-logger/blob/main/docs/examples/cfg.yaml)
as a base.

The name of the file doesn't matter - just remember what you chose and
substitute as appropriate.  Once done, you can exit from the service account
login session.

## 3. Configure Systemd

Create a new Systemd service by running:

    sudo systemctl edit --force --full envoy-logger.service

The name of the service (in the example above, `envoy-logger`) doesn't matter -
just remember what you chose and substitute as appropriate.  When the editor
opens, paste the following text:

    [Unit]
    Description=Envoy Logger
    After=multi-user.target

    [Service]
    User=envoylog
    Group=envoylog
    RestartSec=5
    Restart=always
    ExecStart=python3 -m envoy_logger /home/envoylog/config.yml

    [Install]
    WantedBy=multi-user.target

Save/exit from the editor.

Finally, enable the service to start at boot time and start it:

    sudo systemctl enable --now envoy-logger

You can view status with:

    sudo systemctl status envoy-logger

You can view logs with:

    sudo journalctl -u envoy-logger

(add a `-f` if you want to tail the logs)
