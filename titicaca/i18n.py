# Copyright 2014 Red Hat, Inc.
# All Rights Reserved.
# Copyright (c) 2023 WenRui Gong
# All rights reserved.

import oslo_i18n as i18n

DOMAIN = 'titicaca'

_translators = i18n.TranslatorFactory(domain=DOMAIN)

# The primary translation function using the well-known name "_"
_ = _translators.primary


def enable_lazy(enable=True):
    return i18n.enable_lazy(enable)


def translate(value, user_locale=None):
    return i18n.translate(value, user_locale)


def get_available_languages(domain=DOMAIN):
    return i18n.get_available_languages(domain)


# i18n log translation functions are deprecated. While removing the invocations
# requires a lot of reviewing effort, we decide to make it as no-op functions.
def _LI(msg):
    return msg


def _LW(msg):
    return msg


def _LE(msg):
    return msg


def _LC(msg):
    return msg
