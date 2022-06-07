import unittest

import hall_monitor as hm


class TestHallMonitor(unittest.TestCase):

    def setUp(self):
        self.thresholds = {
            'cpu': 10,
            'memory': 10,
            'fds': 10,
            'io_read_bytes': hm.gb_to_bytes(10),
            'io_write_bytes': hm.gb_to_bytes(10),
        }
        self.username_map = {'bob': 'bobby'}
        self.alerts = []
        self.alert_func = lambda msg: self.alerts.append(msg)

    def test_monitor(self):
        usage_func = lambda: dummy_usage(
            100,
            100,
            100,
            hm.gb_to_bytes(22),
            hm.gb_to_bytes(12),
        )
        hm.monitor(
            self.thresholds,
            self.username_map,
            usage_func,
            self.alert_func,
        )
        print(self.alerts)
        self.assertEqual(len(self.alerts), 5)


def dummy_usage(
    cpu=0,
    memory=0,
    fds=0,
    io_read_bytes=0,
    io_write_bytes=0,
    username='bob',
):
    return {
        username: {
            'cpu': cpu,
            'memory': memory,
            'fds': fds,
            'io_read_bytes': io_read_bytes,
            'io_write_bytes': io_write_bytes,
        }
    }


if __name__ == "__main__":
    unittest.main()
