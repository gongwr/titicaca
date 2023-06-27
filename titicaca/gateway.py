# Copyright 2012 OpenStack Foundation
# Copyright 2013 IBM Corp.
# All Rights Reserved.
# Copyright (c) 2023 WenRui Gong
# All rights reserved.
import titicaca_store

from titicaca.api import authorization
from titicaca.api import policy
from titicaca.api import property_protections
from titicaca.common import property_utils
from titicaca.common import store_utils
import titicaca.db
import titicaca.domain
import titicaca.location
import titicaca.notifier
import titicaca.quota


class Gateway(object):
    def __init__(self, db_api=None, store_api=None, notifier=None,
                 policy_enforcer=None):
        self.db_api = db_api or titicaca.db.get_api()
        self.store_api = store_api or titicaca_store
        self.store_utils = store_utils
        self.notifier = notifier or titicaca.notifier.Notifier()
        self.policy = policy_enforcer or policy.Enforcer()

    def get_image_factory(self, context, authorization_layer=True):
        factory = titicaca.domain.ImageFactory()
        factory = titicaca.location.ImageFactoryProxy(
            factory, context, self.store_api, self.store_utils)
        factory = titicaca.quota.ImageFactoryProxy(
            factory, context, self.db_api, self.store_utils)
        if authorization_layer:
            factory = policy.ImageFactoryProxy(factory, context, self.policy)
        factory = titicaca.notifier.ImageFactoryProxy(
            factory, context, self.notifier)
        if property_utils.is_property_protection_enabled():
            property_rules = property_utils.PropertyRules(self.policy)
            factory = property_protections.ProtectedImageFactoryProxy(
                factory, context, property_rules)
        if authorization_layer:
            factory = authorization.ImageFactoryProxy(
                factory, context)
        return factory

    def get_image_member_factory(self, context, authorization_layer=True):
        factory = titicaca.domain.ImageMemberFactory()
        factory = titicaca.quota.ImageMemberFactoryProxy(
            factory, context, self.db_api, self.store_utils)
        if authorization_layer:
            factory = policy.ImageMemberFactoryProxy(
                factory, context, self.policy)
        if authorization_layer:
            factory = authorization.ImageMemberFactoryProxy(
                factory, context)
        return factory

    def get_repo(self, context, authorization_layer=True):
        """Get the layered ImageRepo model.

        This is where we construct the "the onion" by layering
        ImageRepo models on top of each other, starting with the DB at
        the bottom.

        NB: Code that has implemented policy checks fully above this
        layer should pass authorization_layer=False to ensure that no
        conflicts with old checks happen. Legacy code should continue
        passing True until legacy checks are no longer needed.

        :param context: The RequestContext
        :param authorization_layer: Controls whether or not we add the legacy
                                    titicaca.authorization and titicaca.policy
                                    layers.
        :returns: An ImageRepo-like object

        """
        repo = titicaca.db.ImageRepo(context, self.db_api)
        repo = titicaca.location.ImageRepoProxy(
            repo, context, self.store_api, self.store_utils)
        repo = titicaca.quota.ImageRepoProxy(
            repo, context, self.db_api, self.store_utils)
        if authorization_layer:
            repo = policy.ImageRepoProxy(repo, context, self.policy)
        repo = titicaca.notifier.ImageRepoProxy(
            repo, context, self.notifier)
        if property_utils.is_property_protection_enabled():
            property_rules = property_utils.PropertyRules(self.policy)
            repo = property_protections.ProtectedImageRepoProxy(
                repo, context, property_rules)
        if authorization_layer:
            repo = authorization.ImageRepoProxy(repo, context)

        return repo

    def get_member_repo(self, image, context, authorization_layer=True):
        repo = titicaca.db.ImageMemberRepo(
            context, self.db_api, image)
        repo = titicaca.location.ImageMemberRepoProxy(
            repo, image, context, self.store_api)
        if authorization_layer:
            repo = policy.ImageMemberRepoProxy(
                repo, image, context, self.policy)
        repo = titicaca.notifier.ImageMemberRepoProxy(
            repo, image, context, self.notifier)
        if authorization_layer:
            repo = authorization.ImageMemberRepoProxy(
                repo, image, context)

        return repo

    def get_task_factory(self, context, authorization_layer=True):
        factory = titicaca.domain.TaskFactory()
        if authorization_layer:
            factory = policy.TaskFactoryProxy(
                factory, context, self.policy)
        factory = titicaca.notifier.TaskFactoryProxy(
            factory, context, self.notifier)
        if authorization_layer:
            factory = authorization.TaskFactoryProxy(
                factory, context)
        return factory

    def get_task_repo(self, context, authorization_layer=True):
        repo = titicaca.db.TaskRepo(context, self.db_api)
        if authorization_layer:
            repo = policy.TaskRepoProxy(
                repo, context, self.policy)
        repo = titicaca.notifier.TaskRepoProxy(
            repo, context, self.notifier)
        if authorization_layer:
            repo = authorization.TaskRepoProxy(
                repo, context)
        return repo

    def get_task_stub_repo(self, context, authorization_layer=True):
        repo = titicaca.db.TaskRepo(context, self.db_api)
        if authorization_layer:
            repo = policy.TaskStubRepoProxy(
                repo, context, self.policy)
        repo = titicaca.notifier.TaskStubRepoProxy(
            repo, context, self.notifier)
        if authorization_layer:
            repo = authorization.TaskStubRepoProxy(
                repo, context)
        return repo

    def get_task_executor_factory(self, context, admin_context=None,
                                  authorization_layer=True):
        task_repo = self.get_task_repo(
            context, authorization_layer=authorization_layer)
        image_repo = self.get_repo(context,
                                   authorization_layer=authorization_layer)
        image_factory = self.get_image_factory(
            context, authorization_layer=authorization_layer)
        if admin_context:
            admin_repo = self.get_repo(admin_context,
                                       authorization_layer=authorization_layer)
        else:
            admin_repo = None
        return titicaca.domain.TaskExecutorFactory(task_repo,
                                                 image_repo,
                                                 image_factory,
                                                 admin_repo=admin_repo)

    def get_metadef_namespace_factory(self, context,
                                      authorization_layer=True):
        factory = titicaca.domain.MetadefNamespaceFactory()
        if authorization_layer:
            factory = policy.MetadefNamespaceFactoryProxy(
                factory, context, self.policy)
        factory = titicaca.notifier.MetadefNamespaceFactoryProxy(
            factory, context, self.notifier)
        if authorization_layer:
            factory = authorization.MetadefNamespaceFactoryProxy(
                factory, context)
        return factory

    def get_metadef_namespace_repo(self, context, authorization_layer=True):
        """Get the layered NamespaceRepo model.

        This is where we construct the "the onion" by layering
        NamespaceRepo models on top of each other, starting with the DB at
        the bottom.

        :param context: The RequestContext
        :param authorization_layer: Controls whether or not we add the legacy
                                    titicaca.authorization and titicaca.policy
                                    layers.
        :returns: An NamespaceRepo-like object
        """
        repo = titicaca.db.MetadefNamespaceRepo(context, self.db_api)
        if authorization_layer:
            repo = policy.MetadefNamespaceRepoProxy(
                repo, context, self.policy)
        repo = titicaca.notifier.MetadefNamespaceRepoProxy(
            repo, context, self.notifier)
        if authorization_layer:
            repo = authorization.MetadefNamespaceRepoProxy(
                repo, context)
        return repo

    def get_metadef_object_factory(self, context,
                                   authorization_layer=True):
        factory = titicaca.domain.MetadefObjectFactory()
        if authorization_layer:
            factory = policy.MetadefObjectFactoryProxy(
                factory, context, self.policy)
        factory = titicaca.notifier.MetadefObjectFactoryProxy(
            factory, context, self.notifier)
        if authorization_layer:
            factory = authorization.MetadefObjectFactoryProxy(
                factory, context)
        return factory

    def get_metadef_object_repo(self, context, authorization_layer=True):
        """Get the layered MetadefObjectRepo model.

        This is where we construct the "the onion" by layering
        MetadefObjectRepo models on top of each other, starting with the DB at
        the bottom.

        :param context: The RequestContext
        :param authorization_layer: Controls whether or not we add the legacy
                                    titicaca.authorization and titicaca.policy
                                    layers.
        :returns: An MetadefObjectRepo-like object
        """
        repo = titicaca.db.MetadefObjectRepo(context, self.db_api)
        if authorization_layer:
            repo = policy.MetadefObjectRepoProxy(
                repo, context, self.policy)
        repo = titicaca.notifier.MetadefObjectRepoProxy(
            repo, context, self.notifier)
        if authorization_layer:
            repo = authorization.MetadefObjectRepoProxy(
                repo, context)
        return repo

    def get_metadef_resource_type_factory(self, context,
                                          authorization_layer=True):
        factory = titicaca.domain.MetadefResourceTypeFactory()
        if authorization_layer:
            factory = policy.MetadefResourceTypeFactoryProxy(
                factory, context, self.policy)
        factory = titicaca.notifier.MetadefResourceTypeFactoryProxy(
            factory, context, self.notifier)
        if authorization_layer:
            factory = authorization.MetadefResourceTypeFactoryProxy(
                factory, context)
        return factory

    def get_metadef_resource_type_repo(self, context,
                                       authorization_layer=True):
        """Get the layered MetadefResourceTypeRepo model.

        This is where we construct the "the onion" by layering
        MetadefResourceTypeRepo models on top of each other, starting with
        the DB at the bottom.

        :param context: The RequestContext
        :param authorization_layer: Controls whether or not we add the legacy
                                    titicaca.authorization and titicaca.policy
                                    layers.
        :returns: An MetadefResourceTypeRepo-like object
        """
        repo = titicaca.db.MetadefResourceTypeRepo(
            context, self.db_api)
        if authorization_layer:
            repo = policy.MetadefResourceTypeRepoProxy(
                repo, context, self.policy)
        repo = titicaca.notifier.MetadefResourceTypeRepoProxy(
            repo, context, self.notifier)
        if authorization_layer:
            repo = authorization.MetadefResourceTypeRepoProxy(
                repo, context)
        return repo

    def get_metadef_property_factory(self, context,
                                     authorization_layer=True):
        factory = titicaca.domain.MetadefPropertyFactory()
        if authorization_layer:
            factory = policy.MetadefPropertyFactoryProxy(
                factory, context, self.policy)
        factory = titicaca.notifier.MetadefPropertyFactoryProxy(
            factory, context, self.notifier)
        if authorization_layer:
            factory = authorization.MetadefPropertyFactoryProxy(
                factory, context)
        return factory

    def get_metadef_property_repo(self, context, authorization_layer=True):
        """Get the layered MetadefPropertyRepo model.

        This is where we construct the "the onion" by layering
        MetadefPropertyRepo models on top of each other, starting with
        the DB at the bottom.

        :param context: The RequestContext
        :param authorization_layer: Controls whether or not we add the legacy
                                    titicaca.authorization and titicaca.policy
                                    layers.
        :returns: An MetadefPropertyRepo-like object
        """
        repo = titicaca.db.MetadefPropertyRepo(context, self.db_api)
        if authorization_layer:
            repo = policy.MetadefPropertyRepoProxy(
                repo, context, self.policy)
        repo = titicaca.notifier.MetadefPropertyRepoProxy(
            repo, context, self.notifier)
        if authorization_layer:
            repo = authorization.MetadefPropertyRepoProxy(
                repo, context)
        return repo

    def get_metadef_tag_factory(self, context,
                                authorization_layer=True):
        factory = titicaca.domain.MetadefTagFactory()
        if authorization_layer:
            factory = policy.MetadefTagFactoryProxy(
                factory, context, self.policy)
        factory = titicaca.notifier.MetadefTagFactoryProxy(
            factory, context, self.notifier)
        if authorization_layer:
            factory = authorization.MetadefTagFactoryProxy(
                factory, context)
        return factory

    def get_metadef_tag_repo(self, context, authorization_layer=True):
        """Get the layered MetadefTagRepo model.

        This is where we construct the "the onion" by layering
        MetadefTagRepo models on top of each other, starting with
        the DB at the bottom.

        :param context: The RequestContext
        :param authorization_layer: Controls whether or not we add the legacy
                                    titicaca.authorization and titicaca.policy
                                    layers.
        :returns: An MetadefTagRepo-like object
        """
        repo = titicaca.db.MetadefTagRepo(context, self.db_api)
        if authorization_layer:
            repo = policy.MetadefTagRepoProxy(
                repo, context, self.policy)
        repo = titicaca.notifier.MetadefTagRepoProxy(
            repo, context, self.notifier)
        if authorization_layer:
            repo = authorization.MetadefTagRepoProxy(
                repo, context)
        return repo
