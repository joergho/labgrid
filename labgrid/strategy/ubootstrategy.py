import enum

import attr

from pexpect import EOF

from ..factory import target_factory
from .common import Strategy, StrategyError


class Status(enum.Enum):
    unknown = 0
    off = 1
    uboot = 2
    shell = 3
    reboot = 4
    poweroff = 5


@target_factory.reg_driver
@attr.s(eq=False)
class UBootStrategy(Strategy):
    """UbootStrategy - Strategy to switch to uboot or shell"""
    bindings = {
        "power": "PowerProtocol",
        "console": "ConsoleProtocol",
        "uboot": "UBootDriver",
        "shell": "ShellDriver",
    }

    status = attr.ib(default=Status.unknown)
    systemd_timeout = attr.ib(
        default=30,
        validator=attr.validators.optional(attr.validators.instance_of(int))
    )

    def __attrs_post_init__(self):
        super().__attrs_post_init__()

    def transition(self, status):
        if not isinstance(status, Status):
            status = Status[status]
        if status == Status.unknown:
            raise StrategyError(f"can not transition to {status}")
        elif status == self.status:
            return # nothing to do
        elif status == Status.off:
            self.target.deactivate(self.console)
            self.target.activate(self.power)
            self.power.off()
        elif status == Status.uboot:
            if self.status != Status.reboot:
                # switch off
                self.transition(Status.off)
            self.target.activate(self.console)
            if self.status != Status.reboot:
                # cycle power
                self.power.cycle()
            # interrupt uboot
            self.target.activate(self.uboot)
        elif status == Status.shell:
            # transition to uboot
            self.transition(Status.uboot)
            self.uboot.boot("")
            self.uboot.await_boot()
            self.target.activate(self.shell)
            self.shell.run("systemctl is-system-running --wait", timeout=self.systemd_timeout)
        elif status == Status.reboot:
            # transition to shell if not already in this state
            if self.status != Status.shell:
                self.transition(Status.shell)
            self.target.activate(self.console)
            self.console.sendline("reboot")
            self.console.expect(["reboot: Restarting system", EOF], 300)
        elif status == Status.poweroff:
            # transition to shell if not already in this state
            if self.status != Status.shell:
                self.transition(Status.shell)
            self.target.activate(self.console)
            self.console.sendline("poweroff")
            self.console.expect(["reboot: Power down", EOF], 300)
        else:
            raise StrategyError(f"no transition found from {self.status} to {status}")
        self.status = status

    def force(self, status):
        if not isinstance(status, Status):
            status = Status[status]
        if status == Status.off:
            self.target.activate(self.power)
        elif status == Status.uboot:
            self.target.activate(self.uboot)
        elif status == Status.shell:
            self.target.activate(self.shell)
        else:
            raise StrategyError("can not force state {}".format(status))
        self.status = status
