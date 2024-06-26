import attr
import time

from ..factory import target_factory
from ..protocol import ConsoleProtocol
from .powerdriver import PowerResetMixin, PowerProtocol
from .common import Driver

@target_factory.reg_driver
@attr.s(eq=False)
class ChromiumEcPowerDriver(Driver, PowerResetMixin, PowerProtocol):
    """ChromiumEcDriver - Driver to use power management provided by a
    microcontroller running ChromiumOS Embedded Controller software (Legacy)
    https://chromium.googlesource.com/chromiumos/platform/ec/
    
    ChromiumEcDriver binds on top of a ConsoleProtocol.
    """
    bindings = {"console": {ConsoleProtocol}, }
    # priorities = {"SerialDriver2": 10, "SerialDriver": -10, }
    priorities = {"ConsoleProtocol": -10, }
    # on_timeout = attr.ib(default=1, validator=attr.validators.instance_of(int))
    delay = attr.ib(default=5, validator=attr.validators.instance_of(int))
    cycle_mode = attr.ib(default="", validator=attr.validators.instance_of(str))

    def __attrs_post_init__(self):
        super().__attrs_post_init__()
        self.default_timeout = 1
        self.on_timeout = 1

    def on(self):
        self.console.sendline("powerbtn")
        time.sleep(self.on_timeout)
        self.console.sendline("powerinfo")
        self.console.expect("power state 3 = S0", self.default_timeout)

    def off(self):
        self.console.sendline("apshutdown")
        time.sleep(self.on_timeout)
        self.console.sendline("powerinfo")
        self.console.expect("power state 0 = G3", self.default_timeout)
        time.sleep(11)
        self.console.sendline("powerinfo")
        self.console.expect("power state 0 = G3", self.default_timeout)

    def _cycle_reboot(self):
        self.console.sendline("reboot")
        self.console.expect("UART initialized after reboot", self.default_timeout)
        self.console.expect("Reset cause: reset-pin soft", self.default_timeout)
        if not self.reboot_autostart:
            self.console.sendline("powerbtn")
            time.sleep(self.on_timeout)
        self.console.expect("power state 4 = G3->S5", self.default_timeout)
        self.console.expect("power state 3 = S0", timeout=self.on_timeout)

    def _cycle_apreset(self):
        self.console.sendline("apreset")
        self.console.expect("chipset_reset", timeout=self.on_timeout)
        self.console.expect("power state 3 = S0", timeout=self.on_timeout)

    def cycle(self):
        if self.cycle_mode == "reboot":
            self._cycle_reboot()
        elif self.cycle_mode == "apreset":
            self._cycle_apreset()
        else:
            self.off()
            time.sleep(self.delay)
            self.on()
