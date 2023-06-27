# Copyright 2014 IBM Corp.
# All Rights Reserved.
# Copyright (c) 2023 WenRui Gong
# All rights reserved.

"""Image location order based location strategy module"""


def get_strategy_name():
    """Return strategy module name."""
    return 'location_order'


def init():
    """Initialize strategy module."""
    pass


def get_ordered_locations(locations, **kwargs):
    """
    Order image location list.

    :param locations: The original image location list.
    :returns: The image location list with original natural order.
    """
    return locations
