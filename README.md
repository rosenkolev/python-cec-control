# CEC Control

Uses cec-ctl and cec-compliance to control PC

## Setup with virtual env

```shell
python3 -m venv .venv
.venv/bin/pip install python-uinput
.venv/bin/pip install cec

.venv/bin/python3 -m cec_control -d 1
```

## Run

```shell
.venv/bin/python3 -m cec_control -d 1
```

## Setup daemon

```
sudo mkdir /usr/lib/python-cec-control/

sudo cp -a ./.venv/. /usr/lib/python-cec-control/.venv/
sudo cp -a ./cec_control/. /usr/lib/python-cec-control/cec_control/
sudo cp ./cec.sh /usr/lib/python-cec-control/cec.sh
sudo cp ./cec_control.service /etc/systemd/system/cec_control.service

sudo systemctl daemon-reload && systemctl start cec_control && systemctl enable cec_control
```

### Check service

```shell
sudo systemctl status cec_control
```
