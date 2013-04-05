# Copyright 2012 Google Inc. All Rights Reserved.

"""Custom properties for hybrid NDB/ProtoRPC models.

Custom properties are defined to allow custom interactions with complex
types and custom serialization of these values into ProtoRPC fields.

Defined here:
  EndpointsAliasProperty:
    A local only property used for including custom properties in messages
    without having to persist these properties in the datastore and for creating
    custom setters based on values parsed from requests.
  EndpointsUserProperty:
    For getting the user the same way an endpoints method does.
  EndpointsDateTimeProperty,EndpointsDateProperty,EndpointsTimeProperty:
    For custom serialization of date and/or time stamps.
  EndpointsVariantIntegerProperty,EndpointsVariantFloatProperty:
    For allowing ProtoRPC type variants for fields which allow it, e.g. a 32-bit
    integer instead of the default 64-bit.
  EndpointsComputedProperty:
    a subclass of ndb.ComputedProperty; this property class is needed since one
    cannot readily determine the type desired of the output.
"""

import datetime
import warnings
warnings.simplefilter('default')  # To allow DeprecationWarning

from . import utils as ndb_utils
from .. import utils

from protorpc import messages

from google.appengine.ext import endpoints
from google.appengine.ext import ndb


__all__ = [
    'EndpointsAliasProperty', 'EndpointsUserProperty',
    'EndpointsDateTimeProperty', 'EndpointsDateProperty',
    'EndpointsTimeProperty', 'EndpointsVariantIntegerProperty',
    'EndpointsVariantFloatProperty', 'EndpointsComputedProperty',
]


DEFAULT_PROPERTY_TYPE = messages.StringField
DATETIME_STRING_FORMAT = utils.DATETIME_STRING_FORMAT
DATE_STRING_FORMAT = utils.DATE_STRING_FORMAT
TIME_STRING_FORMAT = utils.TIME_STRING_FORMAT


def ComputedPropertyToProto(prop, index):
  """Converts a computed property to the corresponding message field.

  Args:
    prop: The NDB property to be converted.
    index: The index of the property within the message.

  Returns:
    A ProtoRPC field. If the property_type of prop is a field, then a field of
        that type will be returned. If the property_type of prop is an enum
        class, then an enum field using that enum class is returned. If the
        property_type of prop is a message class, then a message field using
        that message class is returned.

  Raises:
    TypeError: if the property_type manages to pass CheckValidPropertyType
        without an exception but does not match any of the parent types
        messages.Field, messages.Enum or messages.Message. NOTE: This should
        not occur, given the behavior of CheckValidPropertyType.
  """
  kwargs = ndb_utils.GetKeywordArgs(prop)
  property_type = prop.property_type

  utils.CheckValidPropertyType(property_type)

  if utils.IsSubclass(property_type, messages.Field):
    return property_type(index, **kwargs)
  elif utils.IsSubclass(property_type, messages.Enum):
    return messages.EnumField(property_type, index, **kwargs)
  elif utils.IsSubclass(property_type, messages.Message):
    # No default for {MessageField}s
    kwargs.pop('default', None)
    return messages.MessageField(property_type, index, **kwargs)
  else:
    # Should never occur due to utils.CheckValidPropertyType.
    raise TypeError('Unexpected property type: %s.' % (property_type,))


class EndpointsAliasProperty(property):
  """A custom property that also considers the type of the response.

  Allows Python properties to be used in an EndpointsModel by also
  specifying a property type. These properties can be derived from the rest
  of the model and included in a ProtoRPC message definition, but will not need
  to be persisted in the datastore.

  This class can be used directly to define properties or as a decorator.

  Attributes:
    message_field: a value used to register the property in the property class
        to proto dictionary for any model class with this property. The method
        ComputedPropertyToProto is used here.
  """
  message_field = ComputedPropertyToProto

  @utils.positional(2)
  def __init__(self, func=None, setter=None, fdel=None, doc=None,
               repeated=False, required=False, default=None, name=None,
               variant=None, property_type=DEFAULT_PROPERTY_TYPE):
    """Constructor for property.

    Attributes:
      __saved_property_args: A dictionary that can be stored on the instance if
          used as a decorator rather than directly as a property.
      __initialized: A boolean corresponding to whether or not the instance has
          completed initialization or needs to continue when called as a
          decorator.
      _required: A boolean attribute for ProtoRPC conversion, denoting whether
          this property is required in a message class.
      _repeated: A boolean attribute for ProtoRPC conversion, denoting whether
          this property is repeated in a message class.
      _name: The true name of the property.
      _code_name: The attribute name of the property on the model that
          instantiated it.
      _variant: An optional variant that can be used for ProtoRPC conversion,
          since some ProtoRPC fields allow variants. Will not always be set on
          alias properties.
      property_type: A ProtoRPC field, message class or enum class that
          describes the output of the alias property.

    Args:
      func: The method that outputs the value of the property. If None,
          we use this as a signal the instance is being used as a decorator.
      setter: The (optional) method that will allow the property to be set.
          Passed to the property constructor as fset. Defaults to None.
      fdel: The (optional) method that will be called when the property is
          deleted. Passed to the property constructor as fdel. Defaults to None.
      doc: The (optional) docstring for the property. Defaults to None.
      repeated: Optional boolean, defaults to False. Indicates whether or not
          the ProtoRPC field is repeated.
      required: Optional boolean, defaults to False. Indicates whether or not
          the ProtoRPC field should be required.
      default: Optional default value for the property. Only set on the property
          instance if not None. Will be validated when a corresponding message
          field is created.
      name: A custom name that can be used to describe the property.
      variant: A variant of that can be used to augment the ProtoRPC field. Will
          be validated when a corresponding message field is created.
      property_type: A ProtoRPC field, message class or enum class that
          describes the output of the alias property.
    """
    self._required = required
    self._repeated = repeated
    self._name = name
    self._code_name = None

    if default is not None:
      self._default = default

    if variant is not None:
      self._variant = variant

    utils.CheckValidPropertyType(property_type)
    self.property_type = property_type

    property_args = {'fset': setter, 'fdel': fdel, 'doc': doc}
    if func is None:
      self.__initialized = False
      self.__saved_property_args = property_args
    else:
      self.__initialized = True
      super(EndpointsAliasProperty, self).__init__(func, **property_args)

  def __call__(self, func):
    """Callable method to be used when instance is used as a decorator.

    If called as a decorator, passes the saved keyword arguments and the func
    to the constructor to complete initialization.

    Args:
      func: The method that outputs the value of the property.

    Returns:
      The property instance.

    Raises:
      TypeError: if the instance has already been initialized, either directly
          as a property or as a decorator elsewhere.
    """
    if self.__initialized:
      raise TypeError('EndpointsAliasProperty is not callable.')

    super(EndpointsAliasProperty, self).__init__(func,
                                                 **self.__saved_property_args)
    del self.__saved_property_args

    # Return the property created
    return self

  def _FixUp(self, code_name):
    """Internal helper called to tell the property its name.

    Intended to allow a similar name interface as provided by NDB properties.
    Used during class creation in EndpointsMetaModel.

    Args:
      code_name: The attribute name of the property as set on a class.
    """
    self._code_name = code_name
    if self._name is None:
      self._name = self._code_name


class EndpointsUserProperty(ndb.UserProperty):
  """A custom user property for interacting with user ID tokens.

  Uses the tools provided in the endpoints module to detect the current user.
  In addition, has an optional parameter raise_unauthorized which will return
  a 401 to the endpoints API request if a user can't be detected.
  """

  def __init__(self, *args, **kwargs):
    """Constructor for User property.

    NOTE: Have to pop custom arguments from the keyword argument dictionary
    to avoid corrupting argument order when sent to the superclass.

    Attributes:
      _raise_unauthorized: An optional boolean, defaulting to False. If True,
         the property will return a 401 to the API request if a user can't
         be deteced.
    """
    self._raise_unauthorized = kwargs.pop('raise_unauthorized', False)
    super(EndpointsUserProperty, self).__init__(*args, **kwargs)

  def _set_value(self, entity, value):
    """Internal helper to set value on model entity.

    If the value to be set is null, will try to retrieve the current user and
    will return a 401 if a user can't be found and raise_unauthorized is True.

    Args:
      entity: An instance of some NDB model.
      value: The value of this property to be set on the instance.
    """
    if value is None:
      value = endpoints.get_current_user()
      if self._raise_unauthorized and value is None:
        raise endpoints.UnauthorizedException('Invalid token.')
    super(EndpointsUserProperty, self)._set_value(entity, value)

  def _fix_up(self, cls, code_name):
    """Internal helper called to register the property with the model class.

    Overrides the _set_attributes method on the model class to interject this
    attribute in to the keywords passed to it. Since the method _set_attributes
    is called by the model class constructor to set values, this -- in congress
    with the custom defined _set_value -- will make sure this property always
    gets set when an instance is created, even if not passed in.

    Args:
      cls: The model class that owns the property.
      code_name: The name of the attribute on the model class corresponding
          to the property.
    """
    original_set_attributes = cls._set_attributes

    def CustomSetAttributes(setattr_self, kwds):
      """Custom _set_attributes which makes sure this property is always set."""
      if self._code_name not in kwds:
        kwds[self._code_name] = None
      original_set_attributes(setattr_self, kwds)

    cls._set_attributes = CustomSetAttributes
    super(EndpointsUserProperty, self)._fix_up(cls, code_name)


class EndpointsDateTimeProperty(ndb.DateTimeProperty):
  """A custom datetime property.

  Allows custom serialization of a datetime.datetime stamp when used to create
  a message field.
  """

  def __init__(self, *args, **kwargs):
    """Constructor for datetime property.

    NOTE: Have to pop custom arguments from the keyword argument dictionary
    to avoid corrupting argument order when sent to the superclass.

    Attributes:
      _string_format: An optional string, defaulting to DATETIME_STRING_FORMAT.
         This is used to serialize using strftime and deserialize using strptime
         when the datetime stamp is turned into a message.
    """
    self._string_format = kwargs.pop('string_format', DATETIME_STRING_FORMAT)
    super(EndpointsDateTimeProperty, self).__init__(*args, **kwargs)

  def ToValue(self, value):
    """A custom method to override the typical ProtoRPC message serialization.

    Uses the string_format set on the property to serialize the datetime stamp.

    Args:
      value: A datetime stamp, the value of the property.

    Returns:
      The serialized string value of the datetime stamp.
    """
    return value.strftime(self._string_format)

  def FromValue(self, value):
    """A custom method to override the typical ProtoRPC message deserialization.

    Uses the string_format set on the property to deserialize the datetime
    stamp.

    Args:
      value: A serialized datetime stamp as a string.

    Returns:
      The deserialized datetime.datetime stamp.
    """
    return datetime.datetime.strptime(value, self._string_format)


class EndpointsDateProperty(ndb.DateProperty):
  """A custom date property.

  Allows custom serialization of a datetime.date stamp when used to create a
  message field.
  """

  def __init__(self, *args, **kwargs):
    """Constructor for date property.

    NOTE: Have to pop custom arguments from the keyword argument dictionary
    to avoid corrupting argument order when sent to the superclass.

    Attributes:
      _string_format: An optional string, defaulting to DATE_STRING_FORMAT. This
         is used to serialize using strftime and deserialize using strptime when
         the date stamp is turned into a message.
    """
    self._string_format = kwargs.pop('string_format', DATE_STRING_FORMAT)
    super(EndpointsDateProperty, self).__init__(*args, **kwargs)

  def ToValue(self, value):
    """A custom method to override the typical ProtoRPC message serialization.

    Uses the string_format set on the property to serialize the date stamp.

    Args:
      value: A date stamp, the value of the property.

    Returns:
      The serialized string value of the date stamp.
    """
    return value.strftime(self._string_format)

  def FromValue(self, value):
    """A custom method to override the typical ProtoRPC message deserialization.

    Uses the string_format set on the property to deserialize the date stamp.

    Args:
      value: A serialized date stamp as a string.

    Returns:
      The deserialized datetime.date stamp.
    """
    return datetime.datetime.strptime(value, self._string_format).date()


class EndpointsTimeProperty(ndb.TimeProperty):
  """A custom time property.

  Allows custom serialization of a datetime.time stamp when used to create a
  message field.
  """

  def __init__(self, *args, **kwargs):
    """Constructor for time property.

    NOTE: Have to pop custom arguments from the keyword argument dictionary
    to avoid corrupting argument order when sent to the superclass.

    Attributes:
      string_format: An optional string, defaulting to TIME_STRING_FORMAT. This
         is used to serialize using strftime and deserialize using strptime when
         the time stamp is turned into a message.
    """
    self._string_format = kwargs.pop('string_format', TIME_STRING_FORMAT)
    super(EndpointsTimeProperty, self).__init__(*args, **kwargs)

  def ToValue(self, value):
    """A custom method to override the typical ProtoRPC message serialization.

    Uses the string_format set on the property to serialize the date stamp.

    Args:
      value: A date stamp, the value of the property.

    Returns:
      The serialized string value of the time stamp.
    """
    return value.strftime(self._string_format)

  def FromValue(self, value):
    """A custom method to override the typical ProtoRPC message deserialization.

    Uses the string_format set on the property to deserialize the time stamp.

    Args:
      value: A serialized time stamp as a string.

    Returns:
      The deserialized datetime.time stamp.
    """
    return datetime.datetime.strptime(value, self._string_format).time()


class EndpointsVariantIntegerProperty(ndb.IntegerProperty):
  """A custom integer property.

  Allows custom serialization of a integers by allowing variant types when used
  to create a message field.
  """

  def __init__(self, *args, **kwargs):
    """Constructor for integer property.

    NOTE: Have to pop custom arguments from the keyword argument dictionary
    to avoid corrupting argument order when sent to the superclass.

    Attributes:
      variant: A variant of integer types, defaulting to the default variant for
          a ProtoRPC IntegerField.
    """
    # The value of variant will be verified when the message field is created
    self._variant = kwargs.pop('variant', messages.IntegerField.DEFAULT_VARIANT)
    super(EndpointsVariantIntegerProperty, self).__init__(*args, **kwargs)


class EndpointsVariantFloatProperty(ndb.FloatProperty):
  """A custom float property.

  Allows custom serialization of a float by allowing variant types when used
  to create a message field.
  """

  def __init__(self, *args, **kwargs):
    """Constructor for float property.

    NOTE: Have to pop custom arguments from the keyword argument dictionary
    to avoid corrupting argument order when sent to the superclass.

    Attributes:
      variant: A variant of float types, defaulting to the default variant for
          a ProtoRPC FloatField.
    """
    # The value of variant be verified when the message field is created
    self._variant = kwargs.pop('variant', messages.FloatField.DEFAULT_VARIANT)
    super(EndpointsVariantFloatProperty, self).__init__(*args, **kwargs)


class EndpointsComputedProperty(ndb.ComputedProperty):
  """A custom computed property that also considers the type of the response.

  Allows NDB computed properties to be used in an EndpointsModel by also
  specifying a property type.

  This class can be used directly to define properties or as a decorator.

  Attributes:
    message_field: a value used to register the property in the property class
        to proto dictionary for any model class with this property. The method
        ComputedPropertyToProto is used here.
  """
  message_field = ComputedPropertyToProto

  @utils.positional(2)
  def __init__(self, func=None, **kwargs):
    """Constructor for computed property.

    NOTE: Have to pop custom arguments from the keyword argument dictionary
    to avoid corrupting argument order when sent to the superclass.

    Attributes:
      _variant: A variant of that can be used to augment the ProtoRPC field.
      property_type: A ProtoRPC field, message class or enum class that
          describes the output of the alias property.
      __saved_kwargs: A dictionary that can be stored on the instance if used
          as a decorator rather than directly as a property.
      __initialized: A boolean corresponding to whether or not the instance has
          completed initialization or needs to continue when called as a
          decorator.

    Args:
      func: The method that outputs the value of the computed property. If None,
          we use this as a signal the instance is being used as a decorator.
    """
    variant = kwargs.pop('variant', None)
    # The value of variant will be verified when the message field is created
    if variant is not None:
      self._variant = variant

    property_type = kwargs.pop('property_type', DEFAULT_PROPERTY_TYPE)
    utils.CheckValidPropertyType(property_type)
    self.property_type = property_type

    if func is None:
      self.__initialized = False
      self.__saved_kwargs = kwargs
    else:
      self.__initialized = True
      super(EndpointsComputedProperty, self).__init__(func, **kwargs)

  def __call__(self, func):
    """Callable method to be used when instance is used as a decorator.

    If called as a decorator, passes the saved keyword arguments and the func
    to the constructor to complete initialization.

    Args:
      func: The method that outputs the value of the computed property.

    Returns:
      The property instance.

    Raises:
      TypeError: if the instance has already been initialized, either directly
          as a property or as a decorator elsewhere.
    """
    if self.__initialized:
      raise TypeError('EndpointsComputedProperty is not callable.')

    super(EndpointsComputedProperty, self).__init__(func, **self.__saved_kwargs)
    del self.__saved_kwargs

    # Return the property created
    return self

  def _set_value(self, unused_entity, unused_value):
    """Internal helper to set a value in an entity for a ComputedProperty.

    Typically, on a computed property, an ndb.model.ComputedPropertyError
    exception is raised when we try to set the property.

    In endpoints, since we will be deserializing messages to entities, we want
    to be able to call entity.some_computed_property_name = some_value without
    halting code, hence this will simply do nothing.
    """
    warnings.warn('Cannot assign to a ComputedProperty.', DeprecationWarning)
