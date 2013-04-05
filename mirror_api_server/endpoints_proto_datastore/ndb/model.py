# Copyright 2012 Google Inc. All Rights Reserved.

"""EndpointsModel definition and accompanying definitions.

This model can be used to replace an existing NDB model and allow simple
conversion of model classes into ProtoRPC message classes. These classes can be
used to simplify endpoints API methods so that only entities need be used rather
than converting between ProtoRPC messages and entities and then back again.
"""

import functools
import itertools
try:
  import json
except ImportError:
  import simplejson as json
import pickle

from . import properties
from . import utils as ndb_utils
from .. import utils

from protorpc import messages

from google.appengine.api import datastore_types
from google.appengine.datastore import datastore_query
from google.appengine.ext import endpoints
from google.appengine.ext import ndb


__all__ = ['EndpointsModel']


QUERY_LIMIT_DEFAULT = 10
QUERY_LIMIT_MAX = 100
QUERY_MAX_EXCEEDED_TEMPLATE = '%s results requested. Exceeds limit of %s.'
PROPERTY_COLLISION_TEMPLATE = ('Name conflict: %s set as an NDB property and '
                               'an Endpoints alias property.')
BAD_FIELDS_SCHEMA_TEMPLATE = (
    'Model %s has bad message fields schema type: %s. Only a '
    'list, tuple, dictionary or MessageFieldsSchema are allowed.')
NO_MSG_FIELD_TEMPLATE = ('Tried to use a ProtoRPC message field: %s. Only '
                         'simple fields can be used when allow message fields '
                         'is turned off.')
REQUEST_MESSAGE = 'request_message'
RESPONSE_MESSAGE = 'response_message'
HTTP_METHOD = 'http_method'
QUERY_HTTP_METHOD = 'GET'
# This global will be updated after EndpointsModel is defined and is used by
# the metaclass EndpointsMetaModel
BASE_MODEL_CLASS = None

EndpointsAliasProperty = properties.EndpointsAliasProperty
MessageFieldsSchema = utils.MessageFieldsSchema


def _VerifyProperty(modelclass, attr_name):
  """Return a property if set on a model class, otherwise raises an exception.

  Args:
    modelclass: A subclass of EndpointsModel which has a
        _GetEndpointsProperty method.
    attr_name: String; the name of the property.

  Returns:
    The property set at the attribute name.

  Raises:
    AttributeError: if the property is not set on the class.
  """
  prop = modelclass._GetEndpointsProperty(attr_name)
  if prop is None:
    error_msg = ('The attribute %s is not an accepted field. Accepted fields '
                 'are limited to NDB properties and Endpoints alias '
                 'properties.' % (attr_name,))
    raise AttributeError(error_msg)

  return prop


def ToValue(prop, value):
  """Serializes a value from a property to a ProtoRPC message type.

  Args:
    prop: The NDB or alias property to be converted.
    value: The value to be serialized.

  Returns:
    The serialized version of the value to be set on a ProtoRPC message.
  """
  if value is None:
    return value
  elif isinstance(value, EndpointsModel):
    return value.ToMessage()
  elif hasattr(prop, 'ToValue') and callable(prop.ToValue):
    return prop.ToValue(value)
  elif isinstance(prop, ndb.JsonProperty):
    return json.dumps(value)
  elif isinstance(prop, ndb.PickleProperty):
    return pickle.dumps(value)
  elif isinstance(prop, ndb.UserProperty):
    return utils.UserMessageFromUser(value)
  elif isinstance(prop, ndb.GeoPtProperty):
    return utils.GeoPtMessage(lat=value.lat, lon=value.lon)
  elif isinstance(prop, ndb.KeyProperty):
    return value.urlsafe()
  elif isinstance(prop, ndb.BlobKeyProperty):
    return str(value)
  elif isinstance(prop, (ndb.TimeProperty,
                         ndb.DateProperty,
                         ndb.DateTimeProperty)):
    return utils.DatetimeValueToString(value)
  else:
    return value


def FromValue(prop, value):
  """Deserializes a value from a ProtoRPC message type to a property value.

  Args:
    prop: The NDB or alias property to be set.
    value: The value to be deserialized.

  Returns:
    The deserialized version of the ProtoRPC value to be set on a property.

  Raises:
    TypeError: if a StructuredProperty has a model class that is not an
        EndpointsModel.
  """
  if value is None:
    return value

  if isinstance(prop, (ndb.StructuredProperty, ndb.LocalStructuredProperty)):
    modelclass = prop._modelclass
    if not utils.IsSubclass(modelclass, EndpointsModel):
      error_msg = ('Structured properties should refer to models which '
                   'inherit from EndpointsModel. Received an instance '
                   'of %s.' % (modelclass.__class__.__name__,))
      raise TypeError(error_msg)
    return modelclass.FromMessage(value)

  if hasattr(prop, 'FromValue') and callable(prop.FromValue):
    return prop.FromValue(value)
  elif isinstance(prop, ndb.JsonProperty):
    return json.loads(value)
  elif isinstance(prop, ndb.PickleProperty):
    return pickle.loads(value)
  elif isinstance(prop, ndb.UserProperty):
    return utils.UserMessageToUser(value)
  elif isinstance(prop, ndb.GeoPtProperty):
    return datastore_types.GeoPt(lat=value.lat, lon=value.lon)
  elif isinstance(prop, ndb.KeyProperty):
    return ndb.Key(urlsafe=value)
  elif isinstance(prop, ndb.BlobKeyProperty):
    return datastore_types.BlobKey(value)
  elif isinstance(prop, (ndb.TimeProperty,
                         ndb.DateProperty,
                         ndb.DateTimeProperty)):
    return utils.DatetimeValueFromString(value)
  else:
    return value


class _EndpointsQueryInfo(object):
  """A custom container for query information.

  This will be set on an EndpointsModel (or subclass) instance, and can be used
  in conjunction with alias properties to store query information, simple
  filters, ordering and ancestor.

  Uses an entity to construct simple filters, to validate ordering, to validate
  ancestor and finally to construct a query from these filters, ordering and/or
  ancestor.

  Attributes:
    _entity: An instance of EndpointsModel or a subclass. The values from this
        will be used to create filters for a query.
    _filters: A set of simple equality filters (ndb.FilterNode). Utilizes the
        fact that FilterNodes are hashable and respect equality.
    _ancestor: An ndb Key to be used as an ancestor for a query.
    _cursor: A datastore_query.Cursor, to be used for resuming a query.
    _limit: A positive integer, to be used in a fetch.
    _order: String; comma separated list of property names or property names
        preceded by a minus sign. Used to define an order of query results.
    _order_attrs: The attributes (or negation of attributes) parsed from
        _order. If these can't be parsed from the attributes in _entity, will
        throw an exception.
    _query_final: A final query created using the orders (_order_attrs), filters
        (_filters) and class definition (_entity) in the query info. If this is
        not null, setting attributes on the query info object will fail.
  """

  def __init__(self, entity):
    """Sets all internal variables to the default values and verifies entity.

    Args:
      entity: An instance of EndpointsModel or a subclass.

    Raises:
      TypeError: if entity is not an instance of EndpointsModel or a subclass.
    """
    if not isinstance(entity, EndpointsModel):
      raise TypeError('Query info can only be used with an instance of an '
                      'EndpointsModel subclass. Received: instance of %s.' %
                      (entity.__class__.__name__,))
    self._entity = entity

    self._filters = set()
    self._ancestor = None
    self._cursor = None
    self._limit = None
    self._order = None
    self._order_attrs = ()

    self._query_final = None

  def _PopulateFilters(self):
    """Populates filters in query info by using values set on the entity."""
    entity = self._entity
    for prop in entity._properties.itervalues():
      # The name of the attr on the model/object, may differ from the name
      # of the NDB property in the datastore
      attr_name = prop._code_name
      current_value = getattr(entity, attr_name)

      if prop._repeated:
        if current_value != []:
          raise ValueError('No queries on repeated values are allowed.')
        continue

      # Only filter for non-null values
      if current_value is not None:
        self._AddFilter(prop == current_value)

  def SetQuery(self):
    """Sets the final query on the query info object.

    Uses the filters and orders in the query info to refine the query. If the
    final query is already set, does nothing.
    """
    if self._query_final is not None:
      return

    self._PopulateFilters()

    # _entity.query calls the classmethod for the entity
    if self.ancestor is not None:
      query = self._entity.query(ancestor=self.ancestor)
    else:
      query = self._entity.query()

    for simple_filter in self._filters:
      query = query.filter(simple_filter)
    for order_attr in self._order_attrs:
      query = query.order(order_attr)

    self._query_final = query

  def _AddFilter(self, candidate_filter):
    """Checks a filter and sets it in the filter set.

    Args:
      candidate_filter: An NDB filter which may be added to the query info.

    Raises:
      AttributeError: if query on the object is already final.
      TypeError: if the filter is not a simple filter (FilterNode).
      ValueError: if the operator symbol in the filter is not equality.
    """
    if self._query_final is not None:
      raise AttributeError('Can\'t add more filters. Query info is final.')

    if not isinstance(candidate_filter, ndb.FilterNode):
      raise TypeError('Only simple filters can be used. Received: %s.' %
                      (candidate_filter,))
    opsymbol = candidate_filter._FilterNode__opsymbol
    if opsymbol != '=':
      raise ValueError('Only equality filters allowed. Received: %s.' %
                       (opsymbol,))

    self._filters.add(candidate_filter)

  @property
  def query(self):
    """Public getter for the final query on query info."""
    return self._query_final

  def _GetAncestor(self):
    """Getter to be used for public ancestor property on query info."""
    return self._ancestor

  def _SetAncestor(self, value):
    """Setter to be used for public ancestor property on query info.

    Args:
      value: A potential value for an ancestor.

    Raises:
      AttributeError: if query on the object is already final.
      AttributeError: if the ancestor has already been set.
      TypeError: if the value to be set is not an instance of ndb.Key.
    """
    if self._query_final is not None:
      raise AttributeError('Can\'t set ancestor. Query info is final.')

    if self._ancestor is not None:
      raise AttributeError('Ancestor can\'t be set twice.')
    if not isinstance(value, ndb.Key):
      raise TypeError('Ancestor must be an instance of ndb.Key.')
    self._ancestor = value

  ancestor = property(fget=_GetAncestor, fset=_SetAncestor)

  def _GetCursor(self):
    """Getter to be used for public cursor property on query info."""
    return self._cursor

  def _SetCursor(self, value):
    """Setter to be used for public cursor property on query info.

    Args:
      value: A potential value for a cursor.

    Raises:
      AttributeError: if query on the object is already final.
      AttributeError: if the cursor has already been set.
      TypeError: if the value to be set is not an instance of
          datastore_query.Cursor.
    """
    if self._query_final is not None:
      raise AttributeError('Can\'t set cursor. Query info is final.')

    if self._cursor is not None:
      raise AttributeError('Cursor can\'t be set twice.')
    if not isinstance(value, datastore_query.Cursor):
      raise TypeError('Cursor must be an instance of datastore_query.Cursor.')
    self._cursor = value

  cursor = property(fget=_GetCursor, fset=_SetCursor)

  def _GetLimit(self):
    """Getter to be used for public limit property on query info."""
    return self._limit

  def _SetLimit(self, value):
    """Setter to be used for public limit property on query info.

    Args:
      value: A potential value for a limit.

    Raises:
      AttributeError: if query on the object is already final.
      AttributeError: if the limit has already been set.
      TypeError: if the value to be set is not a positive integer.
    """
    if self._query_final is not None:
      raise AttributeError('Can\'t set limit. Query info is final.')

    if self._limit is not None:
      raise AttributeError('Limit can\'t be set twice.')
    if not isinstance(value, (int, long)) or value < 1:
      raise TypeError('Limit must be a positive integer.')
    self._limit = value

  limit = property(fget=_GetLimit, fset=_SetLimit)

  def _GetOrder(self):
    """Getter to be used for public order property on query info."""
    return self._order

  def _SetOrderAttrs(self):
    """Helper method to set _order_attrs using the value of _order.

    If _order is not set, simply returns, else splits _order by commas and then
    looks up each value (or its negation) in the _properties of the entity on
    the query info object.

    We look up directly in _properties rather than using the attribute names
    on the object since only NDB property names will be used for field names.

    Raises:
      AttributeError: if one of the attributes in the order is not a property
          on the entity.
    """
    if self._order is None:
      return

    unclean_attr_names = self._order.strip().split(',')
    result = []
    for attr_name in unclean_attr_names:
      ascending = True
      if attr_name.startswith('-'):
        ascending = False
        attr_name = attr_name[1:]

      attr = self._entity._properties.get(attr_name)
      if attr is None:
        raise AttributeError('Order attribute %s not defined.' % (attr_name,))

      if ascending:
        result.append(+attr)
      else:
        result.append(-attr)

    self._order_attrs = tuple(result)

  def _SetOrder(self, value):
    """Setter to be used for public order property on query info.

    Sets the value of _order and attempts to set _order_attrs as well
    by valling _SetOrderAttrs, which uses the value of _order.

    If the passed in value is None, but the query is not final and the
    order has not already been set, the method will return without any
    errors or data changed.

    Args:
      value: A potential value for an order.

    Raises:
      AttributeError: if query on the object is already final.
      AttributeError: if the order has already been set.
      TypeError: if the order to be set is not a string.
    """
    if self._query_final is not None:
      raise AttributeError('Can\'t set order. Query info is final.')

    if self._order is not None:
      raise AttributeError('Order can\'t be set twice.')

    if value is None:
      return
    elif not isinstance(value, basestring):
      raise TypeError('Order must be a string.')

    self._order = value
    self._SetOrderAttrs()

  order = property(fget=_GetOrder, fset=_SetOrder)


class EndpointsMetaModel(ndb.MetaModel):
  """Metaclass for EndpointsModel.

  This exists to create new instances of the mutable class attributes for
  subclasses and to verify ProtoRPC specific properties.
  """

  def __init__(cls, name, bases, classdict):
    """Verifies additional ProtoRPC properties on an NDB model."""
    super(EndpointsMetaModel, cls).__init__(name, bases, classdict)

    cls._alias_properties = {}
    cls._proto_models = {}
    cls._proto_collections = {}
    cls._property_to_proto = ndb_utils.NDB_PROPERTY_TO_PROTO.copy()

    cls._FixUpAliasProperties()

    cls._VerifyMessageFieldsSchema()
    cls._VerifyProtoMapping()

  def _FixUpAliasProperties(cls):
    """Updates the alias properties map and verifies each alias property.

    Raises:
      AttributeError: if an alias property is defined beginning with
          an underscore.
      AttributeError: if an alias property is defined that conflicts with
          an NDB property.
    """
    for attr_name in dir(cls):
      prop = getattr(cls, attr_name, None)
      if isinstance(prop, EndpointsAliasProperty):
        if attr_name.startswith('_'):
          raise AttributeError('EndpointsAliasProperty %s cannot begin with an '
                               'underscore character.' % (attr_name,))
        if attr_name in cls._properties:
          raise AttributeError(PROPERTY_COLLISION_TEMPLATE % (attr_name,))
        prop._FixUp(attr_name)
        cls._alias_properties[prop._name] = prop

  def _VerifyMessageFieldsSchema(cls):
    """Verifies that the preset message fields correspond to actual properties.

    If no message fields schema was set on the class, sets the schema using the
    default fields determing by the NDB properties and alias properties defined.

    In either case, converts the passed in fields to an instance of
       MessageFieldsSchema and sets that as the value of _message_fields_schema
       on the class.

    Raises:
      TypeError: if a message fields schema was set on the class that is not a
          list, tuple, dictionary, or MessageFieldsSchema instance.
    """
    message_fields_schema = getattr(cls, '_message_fields_schema', None)
    # Also need to check we aren't re-using from EndpointsModel
    base_schema = getattr(BASE_MODEL_CLASS, '_message_fields_schema', None)
    if message_fields_schema is None or message_fields_schema == base_schema:
      message_fields_schema = cls._DefaultFields()
    elif not isinstance(message_fields_schema,
                        (list, tuple, dict, MessageFieldsSchema)):
      raise TypeError(BAD_FIELDS_SCHEMA_TEMPLATE %
                      (cls.__name__, message_fields_schema.__class__.__name__))
    else:
      for attr in message_fields_schema:
        _VerifyProperty(cls, attr)

    cls._message_fields_schema = MessageFieldsSchema(message_fields_schema,
                                                     name=cls.__name__)

  def _VerifyProtoMapping(cls):
    """Verifies that each property on the class has an associated proto mapping.

    First checks if there is a _custom_property_to_proto dictionary present and
    then overrides the class to proto mapping found in _property_to_proto.

    Then, for each property (NDB or alias), tries to add a mapping first by
    checking for a message field attribute, and then by trying to infer based
    on property subclass.

    Raises:
      TypeError: if a key from _custom_property_to_proto is not a valid NBD
          property. (We don't allow EndpointsAliasProperty here because it
          is not meant to be subclassed and defines a message_field).
      TypeError: if after checking _custom_property_to_proto, message_field and
          inference from a superclass, no appropriate mapping is found in
          _property_to_proto.
    """
    custom_property_to_proto = getattr(cls, '_custom_property_to_proto', None)
    if isinstance(custom_property_to_proto, dict):
      for key, value in custom_property_to_proto.iteritems():
        if not utils.IsSubclass(key, ndb.Property):
          raise TypeError('Invalid property class: %s.' % (key,))
        cls._property_to_proto[key] = value

    for prop in cls._EndpointsPropertyItervalues():
      property_class = prop.__class__
      cls._TryAddMessageField(property_class)
      cls._TryInferSuperclass(property_class)

      if property_class not in cls._property_to_proto:
        raise TypeError('No converter present for property %s' %
                        (property_class.__name__,))

  # TODO(dhermes): Consider renaming this optional property attr from
  #                "message_field" to something more generic. It can either be
  #                a field or it can be a method with the signature
  #                (property instance, integer index)
  def _TryAddMessageField(cls, property_class):
    """Tries to add a proto mapping for a property class using a message field.

    If the property class is already in the proto mapping, does nothing.

    Args:
      property_class: The class of a property from a model.
    """
    if property_class in cls._property_to_proto:
      return

    message_field = getattr(property_class, 'message_field', None)
    if message_field is not None:
      cls._property_to_proto[property_class] = message_field

  def _TryInferSuperclass(cls, property_class):
    """Tries to add a proto mapping for a property class by using a base class.

    If the property class is already in the proto mapping, does nothing.
    Descends up the class hierarchy until an ancestor class has more than one
    base class or until ndb.Property is reached. If any class up the hierarchy
    is already in the proto mapping, the method/field for the superclass is also
    set for the propert class in question.

    Args:
      property_class: The class of a property from a model.
    """
    if (property_class in cls._property_to_proto or
        utils.IsSubclass(property_class, EndpointsAliasProperty)):
      return

    bases = property_class.__bases__
    while len(bases) == 1 and bases[0] != ndb.Property:
      base = bases[0]
      if base in cls._property_to_proto:
        cls._property_to_proto[property_class] = cls._property_to_proto[base]
        return
      else:
        bases = base.__bases__


class EndpointsModel(ndb.Model):
  """Subclass of NDB model that enables translation to ProtoRPC message classes.

  Also uses a subclass of ndb.MetaModel as the metaclass, to allow for custom
  behavior (particularly property verification) on class creation. Two types of
  properties are allowed, the standard NDB property, which ends up in a
  _properties dictionary and {EndpointsAliasProperty}s, which end up in an
  _alias_properties dictionary. They can be accessed simultaneously through
  _GetEndpointsProperty.

  As with NDB, you cannot use the same property object to describe multiple
  properties -- you must create separate property objects for each property.

  In addition to _alias_properties, there are several other class variables that
  can be used to augment the default NDB model behavior:
      _property_to_proto: This is a mapping from properties to ProtoRPC message
          fields or methods which can take a property and an index and convert
          them to a message field. It starts out as a copy of the global
          NDB_PROPERTY_TO_PROTO from ndb_utils and can be augmented by your
          class and/or property definitions
      _custom_property_to_proto: if set as a dictionary, allows default mappings
          from NDB properties to ProtoRPC fields in _property_to_proto to be
          overridden.

  The metaclass ensures each property (alias properties included) can be
  converted to a ProtoRPC message field before the class can be created. Due to
  this, a ProtoRPC message class can be created using any subset of the model
  properties in any order, or a collection containing multiple messages of the
  same class. Once created, these ProtoRPC message classes are cached in the
  class variables _proto_models and _proto_collections.

  Endpoints models also have two class methods which can be used as decorators
  for Cloud Endpoints API methods: method and query_method. These methods use
  the endpoints.api decorator but tailor the behavior to the specific model
  class.

  Where a method decorated with the endpoints.api expects a ProtoRPC
  message class for the response and request type, a method decorated with the
  "method" decorator provided by a model class expects an instance of that class
  both as input and output. In order to deserialize the ProtoRPC input to an
  entity and serialize the entity returned by the decorated method back to
  ProtoRPC, request and response fields can be specified which the Endpoints
  model class can use to create (and cache) corresponding ProtoRPC message
  classes.

  Similarly, a method decorated with the query_method decorator expects a query
  for the EndpointsModel subclass both as input and output. Instead of
  specifying request/response fields for entities, a query and collection fields
  list can be used.

  When no fields are provided, the default fields from the class are used. This
  can be overridden by setting the class variable _message_fields_schema to a
  dictionary, list, tuple or MessageFieldsSchema of your choice. If none is
  provided, the default will include all NDB properties and all Endpoints Alias
  properties.
  """

  __metaclass__ = EndpointsMetaModel

  _custom_property_to_proto = None
  _message_fields_schema = None

  # A new instance of each of these will be created by the metaclass
  # every time a subclass is declared
  _alias_properties = None
  _proto_models = None
  _proto_collections = None
  _property_to_proto = None

  def __init__(self, *args, **kwargs):
    """Initializes NDB model and adds a query info object.

    Attributes:
      _endpoints_query_info: An _EndpointsQueryInfo instance, directly tied to
          the current instance that can be used to form queries using properties
          provided by the instance and can be augmented by alias properties to
          allow custom queries.
    """
    super(EndpointsModel, self).__init__(*args, **kwargs)
    self._endpoints_query_info = _EndpointsQueryInfo(self)
    self._from_datastore = False

  @property
  def from_datastore(self):
    """Property accessor that represents if the entity is from the datastore."""
    return self._from_datastore

  @classmethod
  def _DefaultFields(cls):
    """The default fields for the class.

    Uses all NDB properties and alias properties which are different from the
    alias properties defined on the parent class EndpointsModel.
    """
    fields = cls._properties.keys()
    # Only include Alias properties not defined on the base class
    for prop_name, prop in cls._alias_properties.iteritems():
      base_alias_props = getattr(BASE_MODEL_CLASS, '_alias_properties', {})
      base_prop = base_alias_props.get(prop_name)
      if base_prop != prop:
        fields.append(prop_name)
    return fields

  def _CopyFromEntity(self, entity):
    """Copies properties from another entity to the current one.

    Only sets properties on the current entity that are not already set.

    Args:
      entity: A model instance to be copied from.

    Raises:
      TypeError: if the entity passed in is not the exact same type as the
          current entity.
    """
    if entity.__class__ != self.__class__:
      raise TypeError('Can only copy from entities of the exact type %s. '
                      'Received an instance of %s.' %
                      (self.__class__.__name__, entity.__class__.__name__))

    for prop in entity._EndpointsPropertyItervalues():
      # The name of the attr on the model/object, may differ
      # from the name of the property
      attr_name = prop._code_name

      value = getattr(entity, attr_name)
      if value is not None:
        # Only overwrite null values
        current_value = getattr(self, attr_name)
        if current_value is None:
          setattr(self, attr_name, value)

  def UpdateFromKey(self, key):
    """Attempts to get current entity for key and update the unset properties.

    Only does anything if there is a corresponding entity in the datastore.
    Calls _CopyFromEntity to merge the current entity with the one that was
    retrieved. If one was retrieved, sets _from_datastore to True to signal that
    an entity was retrieved.

    Args:
      key: An NDB key used to retrieve an entity.
    """
    self._key = key
    entity = self._key.get()
    if entity is not None:
      self._CopyFromEntity(entity)
      self._from_datastore = True

  def IdSet(self, value):
    """Setter to be used for default id EndpointsAliasProperty.

    Sets the key on the current entity using the value passed in as the ID.
    Using this key, attempts to retrieve the entity from the datastore and
    update the unset properties of the current entity with those from the
    retrieved entity.

    Args:
      value: An integer ID value for a simple key.

    Raises:
      TypeError: if the value to be set is not an integer. (Though if outside of
          a given range, the get call will also throw an exception.)
    """
    if not isinstance(value, (int, long)):
      raise TypeError('ID must be an integer.')
    self.UpdateFromKey(ndb.Key(self.__class__, value))

  @EndpointsAliasProperty(setter=IdSet, property_type=messages.IntegerField)
  def id(self):
    """Getter to be used for default id EndpointsAliasProperty.

    Specifies that the ProtoRPC property_type is IntegerField, though simple
    string IDs or more complex IDs that use ancestors could also be used.

    Returns:
      The integer ID of the entity key, if the key is not null and the integer
          ID is not null, else returns None.
    """
    if self._key is not None:
      return self._key.integer_id()

  def EntityKeySet(self, value):
    """Setter to be used for default entityKey EndpointsAliasProperty.

    Sets the key on the current entity using the urlsafe entity key string.
    Using the key set on the entity, attempts to retrieve the entity from the
    datastore and update the unset properties of the current entity with those
    from the retrieved entity.

    Args:
      value: String; A urlsafe entity key for an object.

    Raises:
      TypeError: if the value to be set is not a string. (Though if the string
          is not valid base64 or not properly encoded, the key creation will
          also throw an exception.)
    """
    if not isinstance(value, basestring):
      raise TypeError('entityKey must be a string.')
    self.UpdateFromKey(ndb.Key(urlsafe=value))

  @EndpointsAliasProperty(setter=EntityKeySet)
  def entityKey(self):
    """Getter to be used for default entityKey EndpointsAliasProperty.

    Uses the default ProtoRPC property_type StringField.

    Returns:
      The urlsafe string produced by the entity key, if the key is not null,
          else returns None.
    """
    if self._key is not None:
      return self._key.urlsafe()

  def LimitSet(self, value):
    """Setter to be used for default limit EndpointsAliasProperty.

    Simply sets the limit on the entity's query info object, and the query
    info object handles validation.

    Args:
      value: The limit value to be set.
    """
    self._endpoints_query_info.limit = value

  @EndpointsAliasProperty(setter=LimitSet, property_type=messages.IntegerField)
  def limit(self):
    """Getter to be used for default limit EndpointsAliasProperty.

    Uses the ProtoRPC property_type IntegerField since a limit.

    Returns:
      The integer (or null) limit from the query info on the entity.
    """
    return self._endpoints_query_info.limit

  def OrderSet(self, value):
    """Setter to be used for default order EndpointsAliasProperty.

    Simply sets the order on the entity's query info object, and the query
    info object handles validation.

    Args:
      value: The order value to be set.
    """
    self._endpoints_query_info.order = value

  @EndpointsAliasProperty(setter=OrderSet)
  def order(self):
    """Getter to be used for default order EndpointsAliasProperty.

    Uses the default ProtoRPC property_type StringField.

    Returns:
      The string (or null) order from the query info on the entity.
    """
    return self._endpoints_query_info.order

  def PageTokenSet(self, value):
    """Setter to be used for default pageToken EndpointsAliasProperty.

    Tries to use Cursor.from_websafe_string to convert the value to a cursor
    and then sets the cursor on the entity's query info object, and the query
    info object handles validation.

    Args:
      value: The websafe string version of a cursor.
    """
    cursor = datastore_query.Cursor.from_websafe_string(value)
    self._endpoints_query_info.cursor = cursor

  @EndpointsAliasProperty(setter=PageTokenSet)
  def pageToken(self):
    """Getter to be used for default pageToken EndpointsAliasProperty.

    Uses the default ProtoRPC property_type StringField.

    Returns:
      The websafe string from the cursor on the entity's query info object, or
          None if the cursor is null.
    """
    cursor = self._endpoints_query_info.cursor
    if cursor is not None:
      return cursor.to_websafe_string()

  @classmethod
  def _GetEndpointsProperty(cls, attr_name):
    """Return a property if set on a model class.

    Attempts to retrieve both the NDB and alias version of the property, makes
    sure at most one is not null and then returns that one.

    Args:
      attr_name: String; the name of the property.

    Returns:
      The property set at the attribute name.

    Raises:
      AttributeError: if the property is both an NDB and alias property.
    """
    property_value = cls._properties.get(attr_name)
    alias_value = cls._alias_properties.get(attr_name)
    if property_value is not None and alias_value is not None:
      raise AttributeError(PROPERTY_COLLISION_TEMPLATE % (attr_name,))

    return property_value or alias_value

  @classmethod
  def _EndpointsPropertyItervalues(cls):
    """Iterator containing both NDB and alias property instances for class."""
    property_values = cls._properties.itervalues()
    alias_values = cls._alias_properties.itervalues()
    return itertools.chain(property_values, alias_values)

  @classmethod
  def ProtoModel(cls, fields=None, allow_message_fields=True):
    """Creates a ProtoRPC message class using a subset of the class properties.

    Creates a MessageFieldsSchema from the passed in fields (may cause exception
    if not valid). If this MessageFieldsSchema is already in the cache of
    models, returns the cached value.

    If not, verifies that each property is valid (may cause exception) and then
    uses the proto mapping to create the corresponding ProtoRPC field. Using the
    created fields and the name from the MessageFieldsSchema, creates a new
    ProtoRPC message class by calling the type() constructor.

    Before returning it, it caches the newly created ProtoRPC message class.

    Args:
      fields: Optional fields, defaults to None. If None, the default from
          the class is used. If specified, will be converted to a
          MessageFieldsSchema object (and verified as such).
      allow_message_fields: An optional boolean; defaults to True. If True, does
          nothing. If False, stops ProtoRPC message classes that have one or
          more ProtoRPC {MessageField}s from being created.

    Returns:
      The cached or created ProtoRPC message class specified by the fields.

    Raises:
      AttributeError: if a verified property has no proto mapping registered.
          This is a serious error and should not occur due to what happens in
          the metaclass.
      TypeError: if a value from the proto mapping is not a ProtoRPC field or a
          callable method (which takes a property and an index).
      TypeError: if a proto mapping results in a ProtoRPC MessageField while
          message fields are explicitly disallowed by having
          allow_message_fields set to False.
    """
    if fields is None:
      fields = cls._message_fields_schema
    # If fields is None, either the module user manaully removed the default
    # value or some bug has occurred in the library
    message_fields_schema = MessageFieldsSchema(fields,
                                                basename=cls.__name__ + 'Proto')

    if message_fields_schema in cls._proto_models:
      cached_model = cls._proto_models[message_fields_schema]
      if not allow_message_fields:
        for field in cached_model.all_fields():
          if isinstance(field, messages.MessageField):
            error_msg = NO_MSG_FIELD_TEMPLATE % (field.__class__.__name__,)
            raise TypeError(error_msg)
      return cached_model

    message_fields = {}
    for index, name in enumerate(message_fields_schema):
      field_index = index + 1
      prop = _VerifyProperty(cls, name)
      to_proto = cls._property_to_proto.get(prop.__class__)

      if to_proto is None:
        raise AttributeError('%s does not have a proto mapping for %s.' %
                             (cls.__name__, prop.__class__.__name__))

      if utils.IsSimpleField(to_proto):
        proto_attr = ndb_utils.MessageFromSimpleField(to_proto, prop,
                                                      field_index)
      elif callable(to_proto):
        proto_attr = to_proto(prop, field_index)
      else:
        raise TypeError('Proto mapping for %s was invalid. Received %s, which '
                        'was neither a ProtoRPC field, nor a callable object.' %
                        (name, to_proto))

      if not allow_message_fields:
        if isinstance(proto_attr, messages.MessageField):
          error_msg = NO_MSG_FIELD_TEMPLATE % (proto_attr.__class__.__name__,)
          raise TypeError(error_msg)

      message_fields[name] = proto_attr

    # TODO(dhermes): This behavior should be regulated more directly.
    #                This is to make sure the schema name in the discovery
    #                document is message_fields_schema.name rather than
    #                EndpointsProtoDatastoreNdbModel{message_fields_schema.name}
    message_fields['__module__'] = ''
    message_class = type(message_fields_schema.name,
                         (messages.Message,),
                         message_fields)

    cls._proto_models[message_fields_schema] = message_class
    return message_class

  @classmethod
  def ProtoCollection(cls, collection_fields=None):
    """Creates a ProtoRPC message class using a subset of the class properties.

    In contrast to ProtoModel, this creates a collection with only two fields:
    items and nextPageToken. The field nextPageToken is used for paging through
    result sets, while the field items is a repeated ProtoRPC MessageField used
    to hold the query results. The fields passed in are used to specify the
    ProtoRPC message class set on the MessageField.

    As with ProtoModel, creates a MessageFieldsSchema from the passed in fields,
    checks if this MessageFieldsSchema is already in the cache of collections,
    and returns the cached value if it exists.

    If not, will call ProtoModel with the collection_fields passed in to set
    the ProtoRPC message class on the items MessageField.

    Before returning it, it caches the newly created ProtoRPC message class in a
    cache of collections.

    Args:
      collection_fields: Optional fields, defaults to None. If None, the
          default from the class is used. If specified, will be converted to a
          MessageFieldsSchema object (and verified as such).

    Returns:
      The cached or created ProtoRPC (collection) message class specified by
          the fields.
    """
    if collection_fields is None:
      collection_fields = cls._message_fields_schema
    message_fields_schema = MessageFieldsSchema(collection_fields,
                                                basename=cls.__name__ + 'Proto')

    if message_fields_schema in cls._proto_collections:
      return cls._proto_collections[message_fields_schema]

    proto_model = cls.ProtoModel(fields=message_fields_schema)

    message_fields = {
        'items': messages.MessageField(proto_model, 1, repeated=True),
        'nextPageToken': messages.StringField(2),
        # TODO(dhermes): This behavior should be regulated more directly.
        #                This is to make sure the schema name in the discovery
        #                document is message_fields_schema.collection_name
        '__module__': '',
    }
    collection_class = type(message_fields_schema.collection_name,
                            (messages.Message,),
                            message_fields)
    cls._proto_collections[message_fields_schema] = collection_class
    return collection_class

  def ToMessage(self, fields=None):
    """Converts an entity to an ProtoRPC message.

    Uses the fields list passed in to create a ProtoRPC message class and then
    converts the relevant fields from the entity using ToValue.

    Args:
      fields: Optional fields, defaults to None. Passed to ProtoModel to
          create a ProtoRPC message class for the message.

    Returns:
      The ProtoRPC message created using the values from the entity and the
          fields provided for the message class.

    Raises:
      TypeError: if a repeated field has a value which is not a tuple or list.
    """
    proto_model = self.ProtoModel(fields=fields)

    proto_args = {}
    for field in proto_model.all_fields():
      name = field.name
      value_property = _VerifyProperty(self.__class__, name)

      # Since we are using getattr rather than checking self._values, this will
      # also work for properties which have a default set
      value = getattr(self, value_property._code_name)
      if value is None:
        continue

      if field.repeated:
        if not isinstance(value, (list, tuple)):
          error_msg = ('Property %s is a repeated field and its value should '
                       'be a list or tuple. Received: %s' % (name, value))
          raise TypeError(error_msg)

        to_add = [ToValue(value_property, element) for element in value]
      else:
        to_add = ToValue(value_property, value)
      proto_args[name] = to_add

    return proto_model(**proto_args)

  @classmethod
  def FromMessage(cls, message):
    """Converts a ProtoRPC message to an entity of the model class.

    Makes sure the message being converted is an instance of a ProtoRPC message
    class we have already encountered and then converts the relevant field
    values to the entity values using FromValue.

    When collecting the values from the message for conversion to an entity, NDB
    and alias properties are treated differently. The NDB properties can just be
    passed in to the class constructor as kwargs, but the alias properties must
    be set after the fact, and may even throw exceptions if the message has
    fields corresponding to alias properties which don't define a setter.

    Args:
      message: A ProtoRPC message.

    Returns:
      The entity of the current class that was created using the
          message field values.

    Raises:
      TypeError: if a message class is encountered that has not been stored in
          the _proto_models cache on the class. This is a precaution against
          unkown ProtoRPC message classes.
      TypeError: if a repeated field has a value which is not a tuple or list.
    """
    message_class = message.__class__
    if message_class not in cls._proto_models.values():
      error_msg = ('The message is an instance of %s, which is a class this '
                   'EndpointsModel does not know how to process.' %
                   (message_class.__name__))
      raise TypeError(error_msg)

    entity_kwargs = {}
    alias_args = []

    for field in sorted(message_class.all_fields(),
                        key=lambda field: field.number):
      name = field.name
      value = getattr(message, name, None)
      if value is None:
        continue

      value_property = _VerifyProperty(cls, name)

      if field.repeated:
        if not isinstance(value, (list, tuple)):
          error_msg = ('Repeated attribute should be a list or tuple. '
                       'Received a %s.' % (value.__class__.__name__,))
          raise TypeError(error_msg)
        to_add = [FromValue(value_property, element) for element in value]
      else:
        to_add = FromValue(value_property, value)

      local_name = value_property._code_name
      if isinstance(value_property, EndpointsAliasProperty):
        alias_args.append((local_name, to_add))
      else:
        entity_kwargs[local_name] = to_add

    # Will not throw exception if a required property is not included. This
    # sort of exception is only thrown when attempting to put the entity.
    entity = cls(**entity_kwargs)

    # Set alias properties, will fail on an alias property if that
    # property was not defined with a setter
    for name, value in alias_args:
      setattr(entity, name, value)

    return entity

  @classmethod
  def ToMessageCollection(cls, items, collection_fields=None,
                          next_cursor=None):
    """Converts a list of entities and cursor to ProtoRPC (collection) message.

    Uses the fields list to create a ProtoRPC (collection) message class and
    then converts each item into a ProtoRPC message to be set as a list of
    items.

    If the cursor is not null, we convert it to a websafe string and set the
    nextPageToken field on the result message.

    Args:
      items: A list of entities of this model.
      collection_fields: Optional fields, defaults to None. Passed to
          ProtoCollection to create a ProtoRPC message class for for the
          collection of messages.
      next_cursor: An optional query cursor, defaults to None.

    Returns:
      The ProtoRPC message created using the entities and cursor provided,
          making sure that the entity message class matches collection_fields.
    """
    proto_model = cls.ProtoCollection(collection_fields=collection_fields)

    items_as_message = [item.ToMessage(fields=collection_fields)
                        for item in items]
    result = proto_model(items=items_as_message)

    if next_cursor is not None:
      result.nextPageToken = next_cursor.to_websafe_string()

    return result

  @classmethod
  @utils.positional(1)
  def method(cls,
             request_fields=None,
             response_fields=None,
             user_required=False,
             **kwargs):
    """Creates an API method decorator using provided metadata.

    Augments the endpoints.method decorator-producing function by allowing
    API methods to receive and return a class instance rather than having to
    worry with ProtoRPC messages (and message class definition). By specifying
    a list of ProtoRPC fields rather than defining the class, response and
    request classes can be defined on the fly.

    If there is any collision between request/response field lists and potential
    custom request/response message definitions that can be passed to the
    endpoints.method decorator, this call will fail.

    All other arguments will be passed directly to the endpoints.method
    decorator-producing function. If request/response field lists are used to
    define custom classes, the newly defined classes will also be passed to
    endpoints.method as the keyword arguments request_message/response_message.

    If a custom request message class is passed in, the resulting decorator will
    not attempt to convert the ProtoRPC message it receives into an
    EndpointsModel entity before passing it to the decorated method. Similarly,
    if a custom response message class is passed in, no attempt will be made to
    convert the object (returned by the decorated method) in the opposite
    direction.

    NOTE: Using utils.positional(1), we ensure the class instance will be the
    only positional argument hence won't have leaking/collision between the
    endpoints.method decorator function that we mean to pass metadata to.

    Args:
      request_fields: An (optional) list, tuple, dictionary or
          MessageFieldsSchema that defines a field ordering in a ProtoRPC
          message class. Defaults to None.
      response_fields: An (optional) list, tuple, dictionary or
          MessageFieldsSchema that defines a field ordering in a ProtoRPC
          message class. Defaults to None.
      user_required: Boolean; indicates whether or not a user is required on any
          incoming request.

    Returns:
      A decorator that takes the metadata passed in and augments an API method.

    Raises:
      TypeError: if there is a collision (either request or response) of
          field list and custom message definition.
    """
    request_message = kwargs.get(REQUEST_MESSAGE)
    if request_fields is not None and request_message is not None:
      raise TypeError('Received both a request message class and a field list '
                      'for creating a request message class.')
    if request_message is None:
      kwargs[REQUEST_MESSAGE] = cls.ProtoModel(fields=request_fields)

    response_message = kwargs.get(RESPONSE_MESSAGE)
    if response_fields is not None and response_message is not None:
      raise TypeError('Received both a response message class and a field list '
                      'for creating a response message class.')
    if response_message is None:
      kwargs[RESPONSE_MESSAGE] = cls.ProtoModel(fields=response_fields)

    apiserving_method_decorator = endpoints.method(**kwargs)

    def RequestToEntityDecorator(api_method):
      """A decorator that uses the metadata passed to the enclosing method.

      Args:
        api_method: A method to be decorated. Expected signature is two
            positional arguments, an instance object of an API service and a
            variable containing a deserialized API request object, most likely
            as a ProtoRPC message or as an instance of the current
            EndpointsModel class.

      Returns:
        A decorated method that uses the metadata of the enclosing method to
            verify the service instance, convert the arguments to ones that can
            be consumed by the decorated method and serialize the method output
            back to a ProtoRPC message.
      """

      @functools.wraps(api_method)
      def EntityToRequestMethod(service_instance, request):
        """Stub method to be decorated.

        After creation, will be passed to the standard endpoints.method
        decorator to preserve the necessary method attributes needed for
        endpoints API methods.

        Args:
          service_instance: A ProtoRPC remove service instance.
          request: A ProtoRPC message.

        Returns:
          A ProtoRPC message, potentially serialized after being returned from a
              method which returns a class instance.

        Raises:
          endpoints.UnauthorizedException: if the user required boolean from
             the metadata is True and if there is no current endpoints user.
        """
        if user_required and endpoints.get_current_user() is None:
          raise endpoints.UnauthorizedException('Invalid token.')

        if request_message is None:
          # If we are using a fields list, we can convert the message to an
          # instance of the current class
          request = cls.FromMessage(request)

        # If developers are using request_fields to create a request message
        # class for them, their method should expect to receive an instance of
        # the current EndpointsModel class, and if it fails for some reason
        # their API users will receive a 503 from an uncaught exception.
        response = api_method(service_instance, request)

        if response_message is None:
          # If developers using a custom request message class with
          # response_fields to create a response message class for them, it is
          # up to them to return an instance of the current EndpointsModel
          # class. If not, their API users will receive a 503 from an uncaught
          # exception.
          response = response.ToMessage(fields=response_fields)

        return response

      return apiserving_method_decorator(EntityToRequestMethod)

    return RequestToEntityDecorator

  @classmethod
  @utils.positional(1)
  def query_method(cls,
                   query_fields=(),
                   collection_fields=None,
                   limit_default=QUERY_LIMIT_DEFAULT,
                   limit_max=QUERY_LIMIT_MAX,
                   user_required=False,
                   use_projection=False,
                   **kwargs):
    """Creates an API query method decorator using provided metadata.

    This will produce a decorator which is solely intended to decorate functions
    which receive queries and expect them to be decorated. Augments the
    endpoints.method decorator-producing function by allowing API methods to
    receive and return a query object.

    Query data will be stored in an entity using the same (de)serialization
    methods used by the classmethod "method". Once there, the query info
    object on the entity will allow conversion into a query and the decorator
    will execute this query.

    Rather than request/response fields (as in "method"), we require that
    callers specify query fields -- which will produce the entity before it
    is converted to a query -- and collection fields -- which will be passed
    to ProtoCollection to create a container class for items returned by the
    query.

    In contrast to "method", no custom request/response message classes can be
    passed in, the queries and collection responses can only be specified by the
    query/collection fields. THIS IS SUBJECT TO CHANGE.

    All other arguments will be passed directly to the endpoints.method
    decorator-producing function. The custom classes defined by the
    query/collection fields will also be passed to endpoints.method as the
    keyword arguments request_message/response_message.

    Custom {EndpointsAliasProperty}s have been defined that allow for
    customizing queries:
      limit: allows a limit to be passed in and augment the query info on the
          deserialized entity.
      order: allows an order to be passed in and augment the query info on the
          deserialized entity.
      pageToken: allows a websafe string value to be converted to a cursor and
          set on the query info of the deserialized entity.

    NOTE: Using utils.positional(1), we ensure the class instance will be the
    only positional argument hence won't have leaking/collision between the
    endpoints.method decorator function that we mean to pass metadata to.

    Args:
      query_fields: An (optional) list, tuple, dictionary or MessageFieldsSchema
          that define a field ordering in a ProtoRPC message class. Defaults to
          an empty tuple, which results in a simple datastore query of the kind.
      collection_fields: An (optional) list, tuple, dictionary or
          MessageFieldsSchema that define a field ordering in a ProtoRPC
          message class. Defaults to None.
      limit_default: An (optional) default value for the amount of items to
          fetch in a query. Defaults to the global QUERY_LIMIT_DEFAULT.
      limit_max: An (optional) max value for the amount of items to
          fetch in a query. Defaults to the global QUERY_LIMIT_MAX.
      user_required: Boolean; indicates whether or not a user is required on any
          incoming request. Defaults to False.
      use_projection: Boolean; indicates whether or the query should retrieve
          entire entities or just a projection using the collection fields.
          Defaults to False. If used, all properties in a projection must be
          indexed, so this should be used with care. However, when used
          correctly, this will speed up queries, reduce payload size and even
          reduce cost at times.

    Returns:
      A decorator that takes the metadata passed in and augments an API query
          method. The decorator will perform the fetching, the decorated method
          simply need return the augmented query object.

    Raises:
      TypeError: if there is a custom request or response message class was
          passed in.
      TypeError: if a http_method other than 'GET' is passed in.
    """
    if REQUEST_MESSAGE in kwargs:
      raise TypeError('Received a request message class on a method intended '
                      'for queries. This is explicitly not allowed. Only '
                      'query_fields can be specified.')
    kwargs[REQUEST_MESSAGE] = cls.ProtoModel(fields=query_fields,
                                             allow_message_fields=False)

    if RESPONSE_MESSAGE in kwargs:
      raise TypeError('Received a response message class on a method intended '
                      'for queries. This is explicitly not allowed. Only '
                      'collection_fields can be specified.')
    kwargs[RESPONSE_MESSAGE] = cls.ProtoCollection(
        collection_fields=collection_fields)

    # Only allow GET for queries
    if HTTP_METHOD in kwargs:
      if kwargs[HTTP_METHOD] != QUERY_HTTP_METHOD:
        raise TypeError('Query requests must use the HTTP GET methods. '
                        'Received %s.' % (kwargs[HTTP_METHOD],))
    kwargs[HTTP_METHOD] = QUERY_HTTP_METHOD

    apiserving_method_decorator = endpoints.method(**kwargs)

    def RequestToQueryDecorator(api_method):
      """A decorator that uses the metadata passed to the enclosing method.

      Args:
        api_method: A method to be decorated. Expected signature is two
            positional arguments, an instance object of an API service and a
            variable containing a deserialized API request object, required here
            to be an NDB query object with kind set to the current
            EndpointsModel class.

      Returns:
        A decorated method that uses the metadata of the enclosing method to
            verify the service instance, convert the arguments to ones that can
            be consumed by the decorated method and serialize the method output
            back to a ProtoRPC (collection) message.
      """

      @functools.wraps(api_method)
      def QueryFromRequestMethod(service_instance, request):
        """Stub method to be decorated.

        After creation, will be passed to the standard endpoints.method
        decorator to preserve the necessary method attributes needed for
        endpoints API methods.

        Args:
          service_instance: A ProtoRPC remove service instance.
          request: A ProtoRPC message.

        Returns:
          A ProtoRPC (collection) message, serialized after being returned from
              an NDB query and containing the cursor if there are more results
              and a cursor was returned.

        Raises:
          endpoints.UnauthorizedException: if the user required boolean from
             the metadata is True and if there is no current endpoints user.
          endpoints.ForbiddenException: if the limit passed in through the
             request exceeds the maximum allowed.
        """
        if user_required and endpoints.get_current_user() is None:
          raise endpoints.UnauthorizedException('Invalid token.')

        request_entity = cls.FromMessage(request)
        query_info = request_entity._endpoints_query_info
        query_info.SetQuery()

        # Allow the caller to update the query
        query = api_method(service_instance, query_info.query)

        # Use limit on query info or default if none was set
        request_limit = query_info.limit or limit_default
        if request_limit > limit_max:
          raise endpoints.ForbiddenException(
              QUERY_MAX_EXCEEDED_TEMPLATE % (request_limit, limit_max))

        query_options = {'start_cursor': query_info.cursor}
        if use_projection:
          projection = [value for value in collection_fields
                        if value in cls._properties]
          query_options['projection'] = projection
        items, next_cursor, more_results = query.fetch_page(
            request_limit, **query_options)

        # Don't pass a cursor if there are no more results
        if not more_results:
          next_cursor = None

        return cls.ToMessageCollection(items,
                                       collection_fields=collection_fields,
                                       next_cursor=next_cursor)

      return apiserving_method_decorator(QueryFromRequestMethod)

    return RequestToQueryDecorator
# Update base class global so EndpointsMetaModel can check subclasses against it
BASE_MODEL_CLASS = EndpointsModel
