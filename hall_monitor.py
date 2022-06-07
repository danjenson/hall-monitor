#!/usr/bin/env python3
import argparse
import json
import logging
import socket
import sys
import time
from collections import defaultdict
from logging.handlers import RotatingFileHandler

import psutil
import requests
import yaml


def usage_by_user():
    """Collects usage stats by user."""
    d = defaultdict(lambda: defaultdict(float))
    logged_in_users = set([u.name for u in psutil.users()])
    for p in psutil.process_iter():
        server_username = p.username()
        if server_username not in logged_in_users:
            continue
        usage = d[server_username]
        usage['cpu'] += p.cpu_percent()
        usage['memory'] += p.memory_percent()
        usage['fds'] += p.num_fds()
        ioc = p.io_counters()
        usage['io_read_bytes'] += ioc.read_bytes
        usage['io_write_bytes'] += ioc.write_bytes
    return d


def monitor(
        thresholds,
        username_map,
        usage_func=usage_by_user,
        alert_func=lambda msg: print(msg),
):
    """Monitors usage and sends an alert when there is a voilation."""
    now = int(time.time())
    usage = usage_func()
    # NOTE: no-op if logging is not setup
    logging.info(json.dumps({'unixtime': now, 'usage': usage}))
    for username, user_usage in usage.items():
        for k, v in user_usage.items():
            threshold = thresholds[k]
            if v > threshold:
                name = username_map[username]
                msg = build_alert_message(name, k, v, threshold)
                alert_func(msg)


def build_alert_message(name, k, v, threshold):
    box = socket.gethostname()
    k_fmt = {
        'cpu': 'CPU usage',
        'memory': 'memory usage',
        'fds': 'number of files descriptors',
        'io_read_bytes': 'number of read bytes',
        'io_write_bytes': 'number of written bytes',
    }
    v_fmt_func = {
        'cpu': lambda v: f'{v:.0f}%',
        'memory': lambda v: f'{v:.0f}%',
        'fds': lambda v: f'{int(v)}',
        'io_read_bytes': lambda v: f'{bytes_to_gb(v):.2f} GB',
        'io_write_bytes': lambda v: f'{bytes_to_gb(v):.2f} GB',
    }
    v_fmt = v_fmt_func.get(k, lambda v: v)
    v = v_fmt(v)
    t = v_fmt(threshold)
    msg = f'@{name} your total {k_fmt.get(k, k)} on '
    msg += f'{box} is at {v}, please keep it below {t}.'
    return msg


def build_slack_alert_func(slack_webhook_url):

    def slack_alert(msg):
        data = json.dumps({
            "username":
            "Hall Monitor",
            "icon_emoji":
            ":red-flag:",
            "channel":
            "#cluster",
            "attachments": [{
                "fields": [{
                    "title": "Usage Violation",
                    "value": msg,
                    "short": "false",
                }]
            }]
        })
        byte_length = str(sys.getsizeof(data))
        headers = {
            'Content-Type': "application/json",
            'Content-Length': byte_length
        }
        # TODO(danj): check for post request failures
        requests.post(slack_webhook_url, data=data, headers=headers)

    return slack_alert


def bytes_to_gb(n_bytes):
    return n_bytes / (1024**3)


def gb_to_bytes(n_gb):
    return n_gb * 1024**3


def load_yaml(path):
    with open(path) as f:
        return yaml.safe_load(f)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog=sys.argv[0],
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        '-w',
        '--slack_webhook_url',
        help='if present, will send alerts to slack webhook url',
    )
    parser.add_argument(
        '-i',
        '--interval',
        default=10 * 60,
        type=float,
        help='number of seconds between hall monitoring checks',
    )
    parser.add_argument(
        '-t',
        '--thresholds_yaml',
        help='yaml file containing usage limits for alerts',
        default='/etc/hall-monitor/thresholds.yaml',
    )
    parser.add_argument(
        '-u',
        '--username_map_yaml',
        help='yaml file that maps server to target, e.g. slack, usernames',
        default='/etc/hall-monitor/username_map.yaml',
    )
    parser.add_argument(
        '-l',
        '--log_file',
        help='where to log output for each interval',
        default='/tmp/hall-monitor.log',
    )
    parser.add_argument(
        '-m',
        '--log_file_max_mb',
        default=100,
        type=int,
        help='maximum number of MB for log file',
    )
    args = parser.parse_args(sys.argv[1:])
    alert_func = lambda msg: print(msg)
    if args.slack_webhook_url:
        alert_func = build_slack_alert_func(args.slack_webhook_url)
    thresholds = load_yaml(args.thresholds_yaml)
    username_map = load_yaml(args.username_map_yaml)
    rfh = RotatingFileHandler(
        filename=args.log_file,
        mode='a',
        maxBytes=1024 * 1024 * args.log_file_max_mb,
        backupCount=2,
        encoding='utf-8',
    )
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        handlers=[rfh],
    )
    now = lambda: time.time()
    start = now()
    while True:
        monitor(thresholds, username_map, alert_func=alert_func)
        time.sleep(args.interval - ((now() - start) % args.interval))
