from StringIO import StringIO
from opslib.icsutils.configobj.configobj import ConfigObj
from opslib.icsutils import utils
from unit.mocker import MockerTestCase
from unit import unittest


class TestTimezone(MockerTestCase):

    def setUp(self):
        super(TestTimezone, self).setUp()
        self.new_root = self.makeDir(prefix="test_timezone_")

    def test_set_timezone_sles(self):

        cfg = {
            'timezone': 'Tatooine/Bestine',
        }

        # Create a dummy timezone file
        dummy_contents = '0123456789abcdefgh'
        zone_file = "/".join([self.new_root, cfg['timezone']])
        utils.write_file(zone_file, dummy_contents)

        clock_conf = self.new_root + "/etc/sysconfig/clock"
        local_tz = self.new_root + "/etc/localtime"
        utils.set_timezone(tz=cfg['timezone'],
                           tz_zone_dir=self.new_root,
                           clock_conf_fn=clock_conf,
                           tz_local_fn=local_tz)

        contents = utils.load_file(clock_conf)
        n_cfg = ConfigObj(StringIO(contents))
        self.assertEquals({'ZONE': cfg['timezone']}, dict(n_cfg))

        contents = utils.load_file(local_tz)
        self.assertEquals(dummy_contents, contents.strip())
