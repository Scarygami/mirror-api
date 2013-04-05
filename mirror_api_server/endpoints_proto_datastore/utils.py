# Copyright 2012 Google Inc. All Rights Reserved.

"""Utility module for converting properties to ProtoRPC messages/fields.

The methods here are not specific to NDB or DB (the datastore APIs) and can
be used by utility methods in the datastore API specific code.
"""

__all__ = ['GeoPtMessage', 'MessageFieldsSchema', 'UserMessage',
           'method', 'positional', 'query_method']


import datetime

from protorpc import messages
from protorpc import util as protorpc_util

from google.appengine.api import users


ALLOWED_DECORATOR_NAME = frozenset(['method', 'query_method'])
DATETIME_STRING_FORMAT = '%Y-%m-%dT%H:%M:%S.%f'
DATE_STRING_FORMAT = '%Y-%m-%d'
TIME_STRING_FORMAT = '%H:%M:%S.%f'

positional = protorpc_util.positional


def IsSubclass(candidate, parent_class):
  """Calls issubclass without raising an exception.

  Args:
    candidate: A candidate to check if a subclass.
    parent_class: A class or tuple of classes representing a potential parent.

  Returns:
    A boolean indicating whether or not candidate is a subclass of parent_class.
  """
  try:
    return issubclass(candidate, parent_class)
  except TypeError:
    return False


def IsSimpleField(property_type):
  """Checks if a property type is a "simple" ProtoRPC field.

  We consider "simple" ProtoRPC fields to be ones which are not message/enum
  fields, since those depend on extra data when defined.

  Args:
    property_type: A ProtoRPC field.

  Returns:
    A boolean indicating whether or not the passed in property type is a
        simple field.
  """
  if IsSubclass(property_type, messages.Field):
    return property_type not in (messages.EnumField, messages.MessageField)

  return False


def CheckValidPropertyType(property_type, raise_invalid=True):
  """Checks if a property type is a valid class.

  Here "valid" means the property type is either a simple field, a ProtoRPC
  enum class which can be used to define an EnumField or a ProtoRPC message
  class that can be used to define a MessageField.

  Args:
    property_type: A ProtoRPC field, message class or enum class that
        describes the output of the alias property.
    raise_invalid: Boolean indicating whether or not an exception should be
        raised if the given property is not valid. Defaults to True.

  Returns:
    A boolean indicating whether or not the passed in property type is valid.
        NOTE: Only returns if raise_invalid is False.

  Raises:
    TypeError: If raise_invalid is True and the passed in property is not valid.
  """
  is_valid = IsSimpleField(property_type)
  if not is_valid:
    is_valid = IsSubclass(property_type, (messages.Enum, messages.Message))

  if not is_valid and raise_invalid:
    error_msg = ('Property field must be either a subclass of a simple '
                 'ProtoRPC field, a ProtoRPC enum class or a ProtoRPC message '
                 'class. Received %r.' % (property_type,))
    raise TypeError(error_msg)

  return is_valid


def _DictToTuple(to_sort):
  """Converts a dictionary into a tuple of keys sorted by values.

  Args:
    to_sort: A dictionary like object that has a callable items method.

  Returns:
    A tuple containing the dictionary keys, sorted by value.
  """
  items = to_sort.items()
  items.sort(key=lambda pair: pair[1])
  return tuple(pair[0] for pair in items)


class MessageFieldsSchema(object):
  """A custom dictionary which is hashable.

  Intended to be used so either dictionaries or lists can be used to define
  field index orderings of a ProtoRPC message classes. Since hashable, we can
  cache these ProtoRPC message class definitions using the fields schema
  as a key.

  These objects can be used as if they were dictionaries in many contexts and
  can be compared for equality by hash.
  """

  def __init__(self, fields, name=None, collection_name=None, basename=''):
    """Save list/tuple or convert dictionary a list based on value ordering.

    Attributes:
      name: A name for the fields schema.
      collection_name: A name for collections using the fields schema.
      _data: The underlying dictionary holding the data for the instance.

    Args:
      fields: A dictionary or ordered iterable which defines an index ordering
          for fields in a ProtoRPC message class
      name: A name for the fields schema, defaults to None. If None, uses the
          names in the fields in the order they appear. If the fields schema
          passed in is an instance of MessageFieldsSchema, this is ignored.
      collection_name: A name for collections containing the fields schema,
          defaults to None. If None, uses the name and appends the string
          'Collection'.
      basename: A basename for the default fields schema name, defaults to the
          empty string. If the fields passed in is an instance of
          MessageFieldsSchema, this is ignored.

    Raises:
      TypeError: if the fields passed in are not a dictionary, tuple, list or
          existing MessageFieldsSchema instance.
    """
    if isinstance(fields, MessageFieldsSchema):
      self._data = fields._data
      name = fields.name
      collection_name = fields.collection_name
    elif isinstance(fields, dict):
      self._data = _DictToTuple(fields)
    elif isinstance(fields, (list, tuple)):
      self._data = tuple(fields)
    else:
      error_msg = ('Can\'t create MessageFieldsSchema from object of type %s. '
                   'Must be a dictionary or iterable.' % (fields.__class__,))
      raise TypeError(error_msg)

    self.name = name or self._DefaultName(basename=basename)
    self.collection_name = collection_name or (self.name + 'Collection')

  def _DefaultName(self, basename=''):
    """The default name of the fields schema.

    Can potentially use a basename at the front, but otherwise uses the instance
    fields and joins all the values together using an underscore.

    Args:
      basename: An optional string, defaults to the empty string. If not empty,
          is used at the front of the default name.

    Returns:
      A string containing the default name of the fields schema.
    """
    name_parts = []
    if basename:
      name_parts.append(basename)
    name_parts.extend(self._data)
    return '_'.join(name_parts)

  def __ne__(self, other):
    """Not equals comparison that uses the definition of equality."""
    return not self.__eq__(other)

  def __eq__(self, other):
    """Comparison for equality that uses the hash of the object."""
    if not isinstance(other, self.__class__):
      return False
    return self.__hash__() == other.__hash__()

  def __hash__(self):
    """Unique and idempotent hash.

    Uses a the property list (_data) which is uniquely defined by its elements
    and their sort order, the name of the fields schema and the collection name
    of the fields schema.

    Returns:
      Integer hash value.
    """
    return hash((self._data, self.name, self.collection_name))

  def __iter__(self):
    """Iterator for loop expressions."""
    return iter(self._data)


class GeoPtMessage(messages.Message):
  """ProtoRPC container for GeoPt instances.

  Attributes:
    lat: Float; The latitude of the point.
    lon: Float; The longitude of the point.
  """
  # TODO(dhermes): This behavior should be regulated more directly.
  #                This is to make sure the schema name in the discovery
  #                document is GeoPtMessage rather than
  #                EndpointsProtoDatastoreGeoPtMessage.
  __module__ = ''

  lat = messages.FloatField(1, required=True)
  lon = messages.FloatField(2, required=True)


class UserMessage(messages.Message):
  """ProtoRPC container for users.User objects.

  Attributes:
    email: String; The email of the user.
    auth_domain: String; The auth domain of the user.
    user_id: String; The user ID.
    federated_identity: String; The federated identity of the user.
  """
  # TODO(dhermes): This behavior should be regulated more directly.
  #                This is to make sure the schema name in the discovery
  #                document is UserMessage rather than
  #                EndpointsProtoDatastoreUserMessage.
  __module__ = ''

  email = messages.StringField(1, required=True)
  auth_domain = messages.StringField(2, required=True)
  user_id = messages.StringField(3)
  federated_identity = messages.StringField(4)


def UserMessageFromUser(user):
  """Converts a native users.User object to a UserMessage.

  Args:
    user: An instance of users.User.

  Returns:
    A UserMessage with attributes set from the user.
  """
  return UserMessage(email=user.email(),
                     auth_domain=user.auth_domain(),
                     user_id=user.user_id(),
                     federated_identity=user.federated_identity())


def UserMessageToUser(message):
  """Converts a UserMessage to a native users.User object.

  Args:
    message: The message to be converted.

  Returns:
    An instance of users.User with attributes set from the message.
  """
  return users.User(email=message.email,
                    _auth_domain=message.auth_domain,
                    _user_id=message.user_id,
                    federated_identity=message.federated_identity)


def DatetimeValueToString(value):
  """Converts a datetime value to a string.

  Args:
    value: The value to be converted to a string.

  Returns:
    A string containing the serialized value of the datetime stamp.

  Raises:
    TypeError: if the value is not an instance of one of the three
        datetime types.
  """
  if isinstance(value, datetime.time):
    return value.strftime(TIME_STRING_FORMAT)
  # Order is important, datetime.datetime is a subclass of datetime.date
  elif isinstance(value, datetime.datetime):
    return value.strftime(DATETIME_STRING_FORMAT)
  elif isinstance(value, datetime.date):
    return value.strftime(DATE_STRING_FORMAT)
  else:
    raise TypeError('Could not serialize timestamp: %s.' % (value,))


def DatetimeValueFromString(value):
  """Converts a serialized datetime string to the native type.

  Args:
    value: The string value to be deserialized.

  Returns:
    A datetime.datetime/date/time object that was deserialized from the string.

  Raises:
    TypeError: if the value can not be deserialized to one of the three
        datetime types.
  """
  try:
    return datetime.datetime.strptime(value, TIME_STRING_FORMAT).time()
  except ValueError:
    pass

  try:
    return datetime.datetime.strptime(value, DATE_STRING_FORMAT).date()
  except ValueError:
    pass

  try:
    return datetime.datetime.strptime(value, DATETIME_STRING_FORMAT)
  except ValueError:
    pass

  raise TypeError('Could not deserialize timestamp: %s.' % (value,))


def RaiseNotImplementedMethod(property_class, explanation=None):
  """Wrapper method that returns a method which always fails.

  Args:
    property_class: A property class
    explanation: An optional argument explaining why the given property
        has not been implemented

  Returns:
    A method which will always raise NotImplementedError. If explanation is
        included, it will be raised as part of the exception, otherwise, a
        simple explanation will be provided that uses the name of the property
        class.
  """
  if explanation is None:
    explanation = ('The property %s can\'t be used to define an '
                   'EndpointsModel.' % (property_class.__name__,))

  def RaiseNotImplemented(unused_prop, unused_index):
    """Dummy method that will always raise NotImplementedError.

    Raises:
      NotImplementedError: always
    """
    raise NotImplementedError(explanation)
  return RaiseNotImplemented


def _GetEndpointsMethodDecorator(decorator_name, modelclass, **kwargs):
  """Decorate a ProtoRPC method for use by the endpoints model passed in.

  Requires exactly two positional arguments and passes the rest of the keyword
  arguments to the classmethod method at the decorator name on the given class.

  Args:
    decorator_name: The name of the attribute on the model containing the
       function which will produce the decorator.
    modelclass: An Endpoints model class.

  Returns:
    A decorator that will use the endpoint metadata to decorate an endpoints
        method.
  """
  if decorator_name not in ALLOWED_DECORATOR_NAME:
    raise TypeError('Decorator %s not allowed.' % (decorator_name,))

  # Import here to avoid circular imports
  from .ndb import model
  if IsSubclass(modelclass, model.EndpointsModel):
    return getattr(modelclass, decorator_name)(**kwargs)

  raise TypeError('Model class %s not a valid Endpoints model.' % (modelclass,))


@positional(1)
def method(modelclass, **kwargs):
  """Decorate a ProtoRPC method for use by the endpoints model passed in.

  Requires exactly one positional argument and passes the rest of the keyword
  arguments to the classmethod "method" on the given class.

  Args:
    modelclass: An Endpoints model class that can create a method.

  Returns:
    A decorator that will use the endpoint metadata to decorate an endpoints
        method.
  """
  return _GetEndpointsMethodDecorator('method', modelclass, **kwargs)


@positional(1)
def query_method(modelclass, **kwargs):
  """Decorate a ProtoRPC method intended for queries

  For use by the endpoints model passed in. Requires exactly one positional
  argument and passes the rest of the keyword arguments to the classmethod
  "query_method" on the given class.

  Args:
    modelclass: An Endpoints model class that can create a query method.

  Returns:
    A decorator that will use the endpoint metadata to decorate an endpoints
        query method.
  """
  return _GetEndpointsMethodDecorator('query_method', modelclass, **kwargs)
