# Copyright (c) 2023 WenRui Gong
# All rights reserved.


from titicaca.common import resource_options
from titicaca.common.resource_options import options

PROJECT_OPTIONS_REGISTRY = resource_options.ResourceOptionRegistry('PROJECT')


# NOTE(morgan): wrap this in a function for testing purposes.
# This is called on import by design.
def register_role_options():
    for opt in [
        options.IMMUTABLE_OPT,
    ]:
        PROJECT_OPTIONS_REGISTRY.register_option(opt)


register_role_options()
