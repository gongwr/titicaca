# Copyright (c) 2014 Hewlett-Packard Development Company, L.P.
# Copyright (c) 2023 WenRui Gong
# All rights reserved.


from oslo_db import exception as db_exc
from oslo_log import log as logging
from sqlalchemy import func
import sqlalchemy.orm as sa_orm

from titicaca.common import exception as exc
from titicaca.db.sqlalchemy.metadef_api import namespace as namespace_api
from titicaca.db.sqlalchemy.metadef_api import utils as metadef_utils
from titicaca.db.sqlalchemy import models_metadef as models
from titicaca.i18n import _

LOG = logging.getLogger(__name__)


def _get(context, property_id, session):

    try:
        query = session.query(models.MetadefProperty).filter_by(id=property_id)
        property_rec = query.one()

    except sa_orm.exc.NoResultFound:
        msg = (_("Metadata definition property not found for id=%s")
               % property_id)
        LOG.warning(msg)
        raise exc.MetadefPropertyNotFound(msg)

    return property_rec


def _get_by_name(context, namespace_name, name, session):
    """get a property; raise if ns not found/visible or property not found"""

    namespace = namespace_api.get(context, namespace_name, session)
    try:
        query = session.query(models.MetadefProperty).filter_by(
            name=name, namespace_id=namespace['id'])
        property_rec = query.one()

    except sa_orm.exc.NoResultFound:
        LOG.debug("The metadata definition property with name=%(name)s"
                  " was not found in namespace=%(namespace_name)s.",
                  {'name': name, 'namespace_name': namespace_name})
        raise exc.MetadefPropertyNotFound(property_name=name,
                                          namespace_name=namespace_name)

    return property_rec


def get(context, namespace_name, name, session):
    """get a property; raise if ns not found/visible or property not found"""

    property_rec = _get_by_name(context, namespace_name, name, session)
    return property_rec.to_dict()


def get_all(context, namespace_name, session):
    namespace = namespace_api.get(context, namespace_name, session)
    query = session.query(models.MetadefProperty).filter_by(
        namespace_id=namespace['id'])
    properties = query.all()

    properties_list = []
    for prop in properties:
        properties_list.append(prop.to_dict())
    return properties_list


def create(context, namespace_name, values, session):
    namespace = namespace_api.get(context, namespace_name, session)
    values.update({'namespace_id': namespace['id']})

    property_rec = models.MetadefProperty()
    metadef_utils.drop_protected_attrs(models.MetadefProperty, values)
    property_rec.update(values.copy())

    try:
        property_rec.save(session=session)
    except db_exc.DBDuplicateEntry:
        LOG.debug("Can not create metadata definition property. A property"
                  " with name=%(name)s already exists in"
                  " namespace=%(namespace_name)s.",
                  {'name': property_rec.name,
                   'namespace_name': namespace_name})
        raise exc.MetadefDuplicateProperty(
            property_name=property_rec.name,
            namespace_name=namespace_name)

    return property_rec.to_dict()


def update(context, namespace_name, property_id, values, session):
    """Update a property, raise if ns not found/visible or duplicate result"""

    namespace_api.get(context, namespace_name, session)
    property_rec = _get(context, property_id, session)
    metadef_utils.drop_protected_attrs(models.MetadefProperty, values)
    # values['updated_at'] = timeutils.utcnow() - done by TS mixin
    try:
        property_rec.update(values.copy())
        property_rec.save(session=session)
    except db_exc.DBDuplicateEntry:
        LOG.debug("Invalid update. It would result in a duplicate"
                  " metadata definition property with the same name=%(name)s"
                  " in namespace=%(namespace_name)s.",
                  {'name': property_rec.name,
                   'namespace_name': namespace_name})
        emsg = (_("Invalid update. It would result in a duplicate"
                  " metadata definition property with the same name=%(name)s"
                  " in namespace=%(namespace_name)s.")
                % {'name': property_rec.name,
                   'namespace_name': namespace_name})
        raise exc.MetadefDuplicateProperty(emsg)

    return property_rec.to_dict()


def delete(context, namespace_name, property_name, session):
    property_rec = _get_by_name(
        context, namespace_name, property_name, session)
    if property_rec:
        session.delete(property_rec)
        session.flush()

    return property_rec.to_dict()


def delete_namespace_content(context, namespace_id, session):
    """Use this def only if the ns for the id has been verified as visible"""

    count = 0
    query = session.query(models.MetadefProperty).filter_by(
        namespace_id=namespace_id)
    count = query.delete(synchronize_session='fetch')
    return count


def delete_by_namespace_name(context, namespace_name, session):
    namespace = namespace_api.get(context, namespace_name, session)
    return delete_namespace_content(context, namespace['id'], session)


def count(context, namespace_name, session):
    """Get the count of properties for a namespace, raise if ns not found"""

    namespace = namespace_api.get(context, namespace_name, session)

    query = session.query(func.count(models.MetadefProperty.id)).filter_by(
        namespace_id=namespace['id'])
    return query.scalar()
