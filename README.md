# DomoTricks
DomoTricks is a domotic application to handle 433MHz assets.

[![Build Status](https://travis-ci.org/nbeguier/DomoTricks.svg?branch=master)](https://travis-ci.org/nbeguier/DomoTricks) [![Python 3.7-3.8](https://img.shields.io/badge/python-3.7|3.8-green.svg)](https://www.python.org/)

## Prerequisites

```bash
$ pip3 install -r requirements.txt
$ cp settings.py.sample settings.py
```

## Usage

### RFX reader

```bash
$ python domotricks.py -v -d /dev/ttyUSB0 -l -D
```

### Web server

```bash
# Debug mode
$ python server.py

# gunicorn mode
$ gunicorn server:APP -b 127.0.0.1:8080 --access-logfile /var/log/DomoTricks.log --error-logfile /var/log/DomoTricks-error.log
```

### Time alerting

```bash
$ cat /etc/cron.d/domotricks
* * * * * root <path>/DomoTricks/venv/bin/python <path>/DomoTricks/time_alerting.py 2>&1 | logger -t domotricks_time_alerting
```

### Manipulate database

```sql
-- Add new asset
INSERT INTO my_assets (assetkey,packettype,packettypeid,subtype,nickname) VALUES ('11_00_01c5a9da_10', 'Lighting2', '11', '00', 'Front door');

-- Add device alerting, triggered at every event: "debug" and "door_during_holidays"
INSERT INTO device_alerting (assetkey,functions) VALUES ('11_00_01c5a9da_10', 'debug|door_during_holidays');

-- Add time alerting, triggered by the CRON
INSERT INTO time_alerting (assetkey,functions) VALUES ('52_02_d503', 'report_temperature:08:00');
```

## License
Licensed under the [GPL](https://github.com/nbeguier/DomoTricks/blob/master/LICENSE).

## Copyright
Copyright 2021 Nicolas Béguier; ([nbeguier](https://beguier.eu/nicolas/) - nicolas_beguier[at]hotmail[dot]com)
