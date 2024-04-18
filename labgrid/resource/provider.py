import attr

from ..factory import target_factory
from .common import Resource


@attr.s(eq=False)
class BaseProvider(Resource):
    internal = attr.ib(validator=attr.validators.instance_of(str))
    external = attr.ib(validator=attr.validators.instance_of(str))
    use_symlink = attr.ib(default=True, validator=attr.validators.instance_of(bool))

    def __attrs_post_init__(self):
        self.host = "localhost"
        super().__attrs_post_init__()


@target_factory.reg_resource
@attr.s(eq=False)
class TFTPProvider(BaseProvider):
    pass


@target_factory.reg_resource
@attr.s(eq=False)
class NFSProvider(Resource):
    use_symlink = attr.ib(default=True, validator=attr.validators.instance_of(bool))

    def __attrs_post_init__(self):
        self.host = "localhost"
        super().__attrs_post_init__()


@target_factory.reg_resource
@attr.s(eq=False)
class HTTPProvider(BaseProvider):
    pass
