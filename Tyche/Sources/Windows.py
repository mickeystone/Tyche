
# Sources/windows.py
# Entropy on Windows systems

from __future__ import with_statement

from Tyche.Sources.egd import EGD

import subprocess
import os
import socket

sources_windows = []
sources_kernel = []


def CryptGenRandom16():
    # avoid 128-KiB bug on old systems - making it slow on vista+
    assert len(os.urandom(128*1024)) == 128*1024
    out = os.urandom(16)  # calls CryptGenRandom - ultimate here
    assert len(os.urandom(128*1024)) == 128*1024
    return out


class EGDW(EGD):
    def __init__(self, port=708):
        try:
            self._egdw = subprocess.Popen(
                "powershell Start-Process " +
                os.path.join(os.path.dirname(__file__),
                             "egdw.exe") +
                " --port="+str(int(port)) +
                " -Verb runAs", shell=True)
        except:
            self._egdw = subprocess.Popen("egdw.exe "
                                          "--port="+str(int(port)),
                                          shell=True)
        if self._egdw.poll() is not None:
            # Already running - can't start a new one
            try:  # possible bad now...
                with open(os.path.join(os.environ['WINDIR'],
                                       "egd.port")) as egdport:
                    port = int(egdport.read().replace("\n", ""))
            except:
                assert 0
            else:
                self.need_shutdown = False
        else:
            self.need_shutdown = True
        EGD.__init__(self, port)

    def shutdown(self):
        EGD.shutdown(self)
        if self.need_shutdown:
            os.startfile("egdw.exe --close", "runas")
try:
    _egdw_service = EGDW()
except (AssertionError, socket.error, WindowsError):
    "Continue - ignore it"
else:
    egdw_random = lambda: _egdw_service.gen_random(16)
    egdw_random.__name__ = "<lambda: egdw_random>"
    sources_windows.append(egdw_random)
try:
    import win32api
except ImportError:
    "Do nothing."
else:
    class MouseEntroWindows(object):
        def __init__(self):
            self.last = ""

        def get_mouse_data(self):
            try:
                out = struct.pack("HH", *win32api.GetCursorPos())
            except Exception:
                out = ""
            m = out
            if out == self.last:
                out = ""
            self.last = m
            return out

    sources_windows.append(MouseEntroWindows().get_mouse_data)

sources_kernel.append(CryptGenRandom16)