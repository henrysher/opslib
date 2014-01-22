"""
Utils: Library for Utils
------------------------

+------------------------+----------+
| This is the Utils common library. |
+------------------------+----------+
"""
from StringIO import StringIO

import errno
import glob
import os
import os.path
import platform
import pwd
import random
import shutil
import sys
import time
import logging

from opslib.icsutils.sysconf import SysConf
from opslib import __version__


log = logging.getLogger(__name__)


def system_info():
    return {
        'platform': platform.platform(),
        'release': platform.release(),
        'python': platform.python_version(),
        'uname': platform.uname(),
        'dist': platform.linux_distribution(),
    }


def time_rfc2822():
    try:
        ts = time.strftime("%a, %d %b %Y %H:%M:%S %z", time.gmtime())
    except:
        ts = "??"
    return ts


def make_header(comment_char="#", base='created'):
    ci_ver = __version__
    header = str(comment_char)
    header += " %s by opslib v. %s" % (base.title(), ci_ver)
    header += " on %s" % time_rfc2822()
    return header


def find_modules(root_dir):
    entries = dict()
    for fname in glob.glob(os.path.join(root_dir, "*.py")):
        if not os.path.isfile(fname):
            continue
        modname = os.path.basename(fname)[0:-3]
        modname = modname.strip()
        if modname and modname.find(".") == -1:
            entries[fname] = modname
    return entries


def import_module(module_name):
    __import__(module_name)
    return sys.modules[module_name]


def find_module(base_name, search_paths, required_attrs=None):
    found_places = []
    if not required_attrs:
        required_attrs = []
    # NOTE(harlowja): translate the search paths to include the base name.
    real_paths = []
    for path in search_paths:
        real_path = []
        if path:
            real_path.extend(path.split("."))
        real_path.append(base_name)
        full_path = '.'.join(real_path)
        real_paths.append(full_path)
    log.debug("Looking for modules %s that have attributes %s",
              real_paths, required_attrs)
    for full_path in real_paths:
        mod = None
        try:
            mod = import_module(full_path)
        except ImportError as e:
            log.debug("Failed at attempted import of '%s' due to: %s",
                      full_path, e)
        if not mod:
            continue
        found_attrs = 0
        for attr in required_attrs:
            if hasattr(mod, attr):
                found_attrs += 1
        if found_attrs == len(required_attrs):
            found_places.append(full_path)
    log.debug("Found %s with attributes %s in %s", base_name,
              required_attrs, found_places)
    return found_places


def sym_link(source, link):
    log.debug("Creating symbolic link from %r => %r" % (link, source))
    os.symlink(source, link)


def del_file(path):
    log.debug("Attempting to remove %s", path)
    try:
        os.unlink(path)
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise e


def copy(src, dest):
    log.debug("Copying %s to %s", src, dest)
    shutil.copy(src, dest)


def chmod(path, mode):
    real_mode = safe_int(mode)
    if path and real_mode:
        with SeLinuxGuard(path):
            os.chmod(path, real_mode)


def ensure_dir(path, mode=None):
    if not os.path.isdir(path):
        # Make the dir and adjust the mode
        # FIXME: no consideration on SELinux
        os.makedirs(path)
        chmod(path, mode)
    else:
        # Just adjust the mode
        chmod(path, mode)


def safe_int(possible_int):
    try:
        return int(possible_int)
    except (ValueError, TypeError):
        return None


def chmod(path, mode):
    real_mode = safe_int(mode)
    if path and real_mode:
        # FIXME: no consideration on SELinux
        os.chmod(path, real_mode)


def pipe_in_out(in_fh, out_fh, chunk_size=1024, chunk_cb=None):
    bytes_piped = 0
    while True:
        data = in_fh.read(chunk_size)
        if data == '':
            break
        else:
            out_fh.write(data)
            bytes_piped += len(data)
            if chunk_cb:
                chunk_cb(bytes_piped)
    out_fh.flush()
    return bytes_piped


def load_file(fname, read_cb=None, quiet=False):
    log.debug("Reading from %s (quiet=%s)", fname, quiet)
    ofh = StringIO()
    try:
        with open(fname, 'rb') as ifh:
            pipe_in_out(ifh, ofh, chunk_cb=read_cb)
    except IOError as e:
        if not quiet:
            raise
        if e.errno != errno.ENOENT:
            raise
    contents = ofh.getvalue()
    log.debug("Read %s bytes from %s", len(contents), fname)
    return contents


def write_file(filename, content, mode=0644, omode="wb"):
    """
    Writes a file with the given content and sets the file mode as specified.
    Resotres the SELinux context if possible.

    @param filename: The full path of the file to write.
    @param content: The content to write to the file.
    @param mode: The filesystem mode to set on the file.
    @param omode: The open mode used when opening the file (r, rb, a, etc.)
    """
    ensure_dir(os.path.dirname(filename))
    log.debug("Writing to %s - %s: [%s] %s bytes",
              filename, omode, mode, len(content))
    # FIXME: no consideration on SELinux
    with open(filename, omode) as fh:
        fh.write(content)
        fh.flush()
    chmod(filename, mode)


# Helper function to update a RHEL/SUSE /etc/sysconfig/* file
def update_sysconfig_file(fn, adjustments, allow_empty=False):
    if not adjustments:
        return
    (exists, contents) = read_sysconfig_file(fn)
    updated_am = 0
    for (k, v) in adjustments.items():
        if v is None:
            continue
        v = str(v)
        if len(v) == 0 and not allow_empty:
            continue
        contents[k] = v
        updated_am += 1
    if updated_am:
        lines = [
            str(contents),
        ]
        if not exists:
            lines.insert(0, make_header())
        write_file(fn, "\n".join(lines) + "\n", 0644)


# Helper function to read a RHEL/SUSE /etc/sysconfig/* file
def read_sysconfig_file(fn):
    exists = False
    try:
        contents = load_file(fn).splitlines()
        exists = True
    except IOError:
        contents = []
    return (exists, SysConf(contents))


tz_zone_dir = "/usr/share/zoneinfo"
clock_conf_fn = "/etc/sysconfig/clock"
tz_local_fn = "/etc/localtime"


def dist_uses_systemd():
    # Fedora 18 and RHEL 7 were the first adopters in their series
    (dist, vers) = system_info()['dist'][:2]
    major = (int)(vers.split('.')[0])
    return ((dist.startswith('Red Hat Enterprise Linux') and major >= 7)
            or (dist.startswith('Fedora') and major >= 18)
            or (dist.startswith('CentOS') and major >= 6))


def find_tz_file(tz):
    tz_file = os.path.join(tz_zone_dir, str(tz))
    if not os.path.isfile(tz_file):
        raise IOError(("Invalid timezone %s,"
                       " no file found at %s") % (tz, tz_file))
    return tz_file


def set_timezone(tz):
    tz_file = find_tz_file(tz)
    if dist_uses_systemd():
        # Currently, timedatectl complains if invoked during startup
        # so for compatibility, create the link manually.
        del_file(tz_local_fn)
        sym_link(tz_file, tz_local_fn)
    else:
        # Adjust the sysconfig clock zone setting
        clock_cfg = {
            'ZONE': str(tz),
        }
        update_sysconfig_file(clock_conf_fn, clock_cfg)
        # This ensures that the correct tz will be used for the system
        copy(tz_file, tz_local_fn)

# vim: tabstop=4 shiftwidth=4 softtabstop=4
