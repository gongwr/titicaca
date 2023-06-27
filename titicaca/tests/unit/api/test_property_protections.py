# Copyright 2013 OpenStack Foundation
# All Rights Reserved.
# Copyright (c) 2023 WenRui Gong
# All rights reserved.

from titicaca.api import policy
from titicaca.api import property_protections
from titicaca.common import exception
from titicaca.common import property_utils
import titicaca.domain
from titicaca.tests import utils


TENANT1 = '6838eb7b-6ded-434a-882c-b344c77fe8df'
TENANT2 = '2c014f32-55eb-467d-8fcb-4bd706012f81'


class TestProtectedImageRepoProxy(utils.BaseTestCase):

    class ImageRepoStub(object):
        def __init__(self, fixtures):
            self.fixtures = fixtures

        def get(self, image_id):
            for f in self.fixtures:
                if f.image_id == image_id:
                    return f
            else:
                raise ValueError(image_id)

        def list(self, *args, **kwargs):
            return self.fixtures

        def add(self, image):
            self.fixtures.append(image)

    def setUp(self):
        super(TestProtectedImageRepoProxy, self).setUp()
        self.set_property_protections()
        self.policy = policy.Enforcer(suppress_deprecation_warnings=True)
        self.property_rules = property_utils.PropertyRules(self.policy)
        self.image_factory = titicaca.domain.ImageFactory()
        extra_props = {'spl_create_prop': 'c',
                       'spl_read_prop': 'r',
                       'spl_update_prop': 'u',
                       'spl_delete_prop': 'd',
                       'forbidden': 'prop'}
        extra_props_2 = {'spl_read_prop': 'r', 'forbidden': 'prop'}
        self.fixtures = [
            self.image_factory.new_image(image_id='1', owner=TENANT1,
                                         extra_properties=extra_props),
            self.image_factory.new_image(owner=TENANT2, visibility='public'),
            self.image_factory.new_image(image_id='3', owner=TENANT1,
                                         extra_properties=extra_props_2),
        ]
        self.context = titicaca.context.RequestContext(roles=['spl_role'])
        image_repo = self.ImageRepoStub(self.fixtures)
        self.image_repo = property_protections.ProtectedImageRepoProxy(
            image_repo, self.context, self.property_rules)

    def test_get_image(self):
        image_id = '1'
        result_image = self.image_repo.get(image_id)
        result_extra_props = result_image.extra_properties
        self.assertEqual('c', result_extra_props['spl_create_prop'])
        self.assertEqual('r', result_extra_props['spl_read_prop'])
        self.assertEqual('u', result_extra_props['spl_update_prop'])
        self.assertEqual('d', result_extra_props['spl_delete_prop'])
        self.assertNotIn('forbidden', result_extra_props.keys())

    def test_list_image(self):
        result_images = self.image_repo.list()
        self.assertEqual(3, len(result_images))
        result_extra_props = result_images[0].extra_properties
        self.assertEqual('c', result_extra_props['spl_create_prop'])
        self.assertEqual('r', result_extra_props['spl_read_prop'])
        self.assertEqual('u', result_extra_props['spl_update_prop'])
        self.assertEqual('d', result_extra_props['spl_delete_prop'])
        self.assertNotIn('forbidden', result_extra_props.keys())

        result_extra_props = result_images[1].extra_properties
        self.assertEqual({}, result_extra_props)

        result_extra_props = result_images[2].extra_properties
        self.assertEqual('r', result_extra_props['spl_read_prop'])
        self.assertNotIn('forbidden', result_extra_props.keys())


class TestProtectedImageProxy(utils.BaseTestCase):

    def setUp(self):
        super(TestProtectedImageProxy, self).setUp()
        self.set_property_protections()
        self.policy = policy.Enforcer(suppress_deprecation_warnings=True)
        self.property_rules = property_utils.PropertyRules(self.policy)

    class ImageStub(object):
        def __init__(self, extra_prop):
            self.extra_properties = extra_prop

    def test_read_image_with_extra_prop(self):
        context = titicaca.context.RequestContext(roles=['spl_role'])
        extra_prop = {'spl_read_prop': 'read', 'spl_fake_prop': 'prop'}
        image = self.ImageStub(extra_prop)
        result_image = property_protections.ProtectedImageProxy(
            image, context, self.property_rules)
        result_extra_props = result_image.extra_properties
        self.assertEqual('read', result_extra_props['spl_read_prop'])
        self.assertNotIn('spl_fake_prop', result_extra_props.keys())


class TestExtraPropertiesProxy(utils.BaseTestCase):

    def setUp(self):
        super(TestExtraPropertiesProxy, self).setUp()
        self.set_property_protections()
        self.policy = policy.Enforcer(suppress_deprecation_warnings=True)
        self.property_rules = property_utils.PropertyRules(self.policy)

    def test_read_extra_property_as_admin_role(self):
        extra_properties = {'foo': 'bar', 'ping': 'pong'}
        context = titicaca.context.RequestContext(roles=['admin'])
        extra_prop_proxy = property_protections.ExtraPropertiesProxy(
            context, extra_properties, self.property_rules)
        test_result = extra_prop_proxy['foo']
        self.assertEqual('bar', test_result)

    def test_read_extra_property_as_unpermitted_role(self):
        extra_properties = {'foo': 'bar', 'ping': 'pong'}
        context = titicaca.context.RequestContext(roles=['unpermitted_role'])
        extra_prop_proxy = property_protections.ExtraPropertiesProxy(
            context, extra_properties, self.property_rules)
        self.assertRaises(KeyError, extra_prop_proxy.__getitem__, 'foo')

    def test_update_extra_property_as_permitted_role_after_read(self):
        extra_properties = {'foo': 'bar', 'ping': 'pong'}
        context = titicaca.context.RequestContext(roles=['admin'])
        extra_prop_proxy = property_protections.ExtraPropertiesProxy(
            context, extra_properties, self.property_rules)
        extra_prop_proxy['foo'] = 'par'
        self.assertEqual('par', extra_prop_proxy['foo'])

    def test_update_extra_property_as_unpermitted_role_after_read(self):
        extra_properties = {'spl_read_prop': 'bar'}
        context = titicaca.context.RequestContext(roles=['spl_role'])
        extra_prop_proxy = property_protections.ExtraPropertiesProxy(
            context, extra_properties, self.property_rules)
        self.assertRaises(exception.ReservedProperty,
                          extra_prop_proxy.__setitem__,
                          'spl_read_prop', 'par')

    def test_update_reserved_extra_property(self):
        extra_properties = {'spl_create_prop': 'bar'}
        context = titicaca.context.RequestContext(roles=['spl_role'])
        extra_prop_proxy = property_protections.ExtraPropertiesProxy(
            context, extra_properties, self.property_rules)
        self.assertRaises(exception.ReservedProperty,
                          extra_prop_proxy.__setitem__, 'spl_create_prop',
                          'par')

    def test_update_empty_extra_property(self):
        extra_properties = {'foo': ''}
        context = titicaca.context.RequestContext(roles=['admin'])
        extra_prop_proxy = property_protections.ExtraPropertiesProxy(
            context, extra_properties, self.property_rules)
        extra_prop_proxy['foo'] = 'bar'
        self.assertEqual('bar', extra_prop_proxy['foo'])

    def test_create_extra_property_admin(self):
        extra_properties = {}
        context = titicaca.context.RequestContext(roles=['admin'])
        extra_prop_proxy = property_protections.ExtraPropertiesProxy(
            context, extra_properties, self.property_rules)
        extra_prop_proxy['boo'] = 'doo'
        self.assertEqual('doo', extra_prop_proxy['boo'])

    def test_create_reserved_extra_property(self):
        extra_properties = {}
        context = titicaca.context.RequestContext(roles=['spl_role'])
        extra_prop_proxy = property_protections.ExtraPropertiesProxy(
            context, extra_properties, self.property_rules)
        self.assertRaises(exception.ReservedProperty,
                          extra_prop_proxy.__setitem__, 'boo',
                          'doo')

    def test_delete_extra_property_as_admin_role(self):
        extra_properties = {'foo': 'bar'}
        context = titicaca.context.RequestContext(roles=['admin'])
        extra_prop_proxy = property_protections.ExtraPropertiesProxy(
            context, extra_properties, self.property_rules)
        del extra_prop_proxy['foo']
        self.assertRaises(KeyError, extra_prop_proxy.__getitem__, 'foo')

    def test_delete_nonexistant_extra_property_as_admin_role(self):
        extra_properties = {}
        context = titicaca.context.RequestContext(roles=['admin'])
        extra_prop_proxy = property_protections.ExtraPropertiesProxy(
            context, extra_properties, self.property_rules)
        self.assertRaises(KeyError, extra_prop_proxy.__delitem__, 'foo')

    def test_delete_reserved_extra_property(self):
        extra_properties = {'spl_read_prop': 'r'}
        context = titicaca.context.RequestContext(roles=['spl_role'])
        extra_prop_proxy = property_protections.ExtraPropertiesProxy(
            context, extra_properties, self.property_rules)
        # Ensure property has been created and can be read
        self.assertEqual('r', extra_prop_proxy['spl_read_prop'])
        self.assertRaises(exception.ReservedProperty,
                          extra_prop_proxy.__delitem__, 'spl_read_prop')

    def test_delete_nonexistant_extra_property(self):
        extra_properties = {}
        roles = ['spl_role']
        extra_prop_proxy = property_protections.ExtraPropertiesProxy(
            roles, extra_properties, self.property_rules)
        self.assertRaises(KeyError,
                          extra_prop_proxy.__delitem__, 'spl_read_prop')

    def test_delete_empty_extra_property(self):
        extra_properties = {'foo': ''}
        context = titicaca.context.RequestContext(roles=['admin'])
        extra_prop_proxy = property_protections.ExtraPropertiesProxy(
            context, extra_properties, self.property_rules)
        del extra_prop_proxy['foo']
        self.assertNotIn('foo', extra_prop_proxy)


class TestProtectedImageFactoryProxy(utils.BaseTestCase):
    def setUp(self):
        super(TestProtectedImageFactoryProxy, self).setUp()
        self.set_property_protections()
        self.policy = policy.Enforcer(suppress_deprecation_warnings=True)
        self.property_rules = property_utils.PropertyRules(self.policy)
        self.factory = titicaca.domain.ImageFactory()

    def test_create_image_no_extra_prop(self):
        self.context = titicaca.context.RequestContext(tenant=TENANT1,
                                                     roles=['spl_role'])
        self.image_factory = property_protections.ProtectedImageFactoryProxy(
            self.factory, self.context,
            self.property_rules)
        extra_props = {}
        image = self.image_factory.new_image(extra_properties=extra_props)
        expected_extra_props = {}
        self.assertEqual(expected_extra_props, image.extra_properties)

    def test_create_image_extra_prop(self):
        self.context = titicaca.context.RequestContext(tenant=TENANT1,
                                                     roles=['spl_role'])
        self.image_factory = property_protections.ProtectedImageFactoryProxy(
            self.factory, self.context,
            self.property_rules)
        extra_props = {'spl_create_prop': 'c'}
        image = self.image_factory.new_image(extra_properties=extra_props)
        expected_extra_props = {'spl_create_prop': 'c'}
        self.assertEqual(expected_extra_props, image.extra_properties)

    def test_create_image_extra_prop_reserved_property(self):
        self.context = titicaca.context.RequestContext(tenant=TENANT1,
                                                     roles=['spl_role'])
        self.image_factory = property_protections.ProtectedImageFactoryProxy(
            self.factory, self.context,
            self.property_rules)
        extra_props = {'foo': 'bar', 'spl_create_prop': 'c'}
        # no reg ex for property 'foo' is mentioned for spl_role in config
        self.assertRaises(exception.ReservedProperty,
                          self.image_factory.new_image,
                          extra_properties=extra_props)

    def test_create_image_extra_prop_admin(self):
        self.context = titicaca.context.RequestContext(tenant=TENANT1,
                                                     roles=['admin'])
        self.image_factory = property_protections.ProtectedImageFactoryProxy(
            self.factory, self.context,
            self.property_rules)
        extra_props = {'foo': 'bar', 'spl_create_prop': 'c'}
        image = self.image_factory.new_image(extra_properties=extra_props)
        expected_extra_props = {'foo': 'bar', 'spl_create_prop': 'c'}
        self.assertEqual(expected_extra_props, image.extra_properties)

    def test_create_image_extra_prop_invalid_role(self):
        self.context = titicaca.context.RequestContext(tenant=TENANT1,
                                                     roles=['imaginary-role'])
        self.image_factory = property_protections.ProtectedImageFactoryProxy(
            self.factory, self.context,
            self.property_rules)
        extra_props = {'foo': 'bar', 'spl_create_prop': 'c'}
        self.assertRaises(exception.ReservedProperty,
                          self.image_factory.new_image,
                          extra_properties=extra_props)
