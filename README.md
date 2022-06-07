# Hall Monitor

Monitors CPU, memory, file descriptors, and I/O read/write by user and sends
notifications on Slack (given a webhook URL) when there is a violation.

# Usage

1. Create a slack webhook [here](https://slack.com/get-started#/create).
1. Create `thresholds.yaml` and `username_map.yaml` (see below) and put them in
   `/etc/hall-monitor/` or wherever makes sense; note that there must
   be a mapping from each server username to each target, e.g. Slack, username in
   `username_map.yaml`; users not present in this file will not get alerts.
1. Run Hall Monitor on any server you want to monitor.

```python
usage: ./hall_monitor.py [-h] [-w SLACK_WEBHOOK_URL] [-i INTERVAL] [-t THRESHOLDS_YAML] [-u USERNAME_MAP_YAML] [-l LOG_FILE]
                         [-m LOG_FILE_MAX_MB]

options:
  -h, --help            show this help message and exit
  -w SLACK_WEBHOOK_URL, --slack_webhook_url SLACK_WEBHOOK_URL
                        if present, will send alerts to slack webhook url (default: None)
  -i INTERVAL, --interval INTERVAL
                        number of seconds between hall monitoring checks (default: 600)
  -t THRESHOLDS_YAML, --thresholds_yaml THRESHOLDS_YAML
                        yaml file containing usage limits for alerts (default: /etc/hall-monitor/thresholds.yaml)
  -u USERNAME_MAP_YAML, --username_map_yaml USERNAME_MAP_YAML
                        yaml file that maps server to target, e.g. slack, usernames (default: /etc/hall-monitor/username_map.yaml)
  -l LOG_FILE, --log_file LOG_FILE
                        where to log output for each interval (default: /tmp/hall-monitor.log)
  -m LOG_FILE_MAX_MB, --log_file_max_mb LOG_FILE_MAX_MB
                        maximum number of MB for log file (default: 100)
```

Example `thresholds.yaml`:

```yaml
# The following are thresholds per interval per user.
---
# total cpu percent
cpu: 1000 # 10 CPUs all running at 100%
# total memory percent
memory: 20 # 20% of 1 TB is 200 GB
# total number of file descriptors
fds: 10000
# total number of read I/O bytes
io_read_bytes: 100000000000 # 100 GB
# total number of written I/O bytes
io_write_bytes: 100000000000 # 10 GB
```

Example `username_map.yaml`:

```yaml
# map from server username (left) to target, e.g. slack, username (right)
---
bob: bobby
```

# Log file

- located at `/tmp/hall-monitor.log` by default
- example of loading logs in python:

```python
with open('/tmp/hall-monitor.log') as f:
  usage = []
  for line in f:
    usage.append(json.loads(line))
```

what `usage` looks like:

```python
[{'unixtime': 1654558699.12,
  'usage': {'bob': {'cpu': 35.1,
    'memory': 20.17,
    'fds': 2881.0,
    'io_read_bytes': 881541632.0,
    'io_write_bytes': 170287104.0}}},
 {'unixtime': 1654558702.12,
  'usage': {'bob': {'cpu': 32.2,
    'memory': 20.17,
    'fds': 2876.0,
    'io_read_bytes': 881541632.0,
    'io_write_bytes': 170287104.0}}}]
```

# Testing

- `python -m unittest tests/test_hall_monitor.py`
