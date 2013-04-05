# Copyright 2012 Google Inc. All Rights Reserved.

"""Utility module for converting NDB properties to ProtoRPC messages/fields.

In the dictionary NDB_PROPERTY_TO_PROTO, each property defined by NDB is
registered. The registry values can either be a ProtoRPC field for simple
types/properties or a custom method for converting a property into a
ProtoRPC field.

Some properties have no corresponding implementation. These fields are
registered with a method that will raise a NotImplementedError. As of right now,
these are:
  Property -- this is the base property class and shouldn't be used
  GenericProperty -- this does not play nicely with strongly typed messages
  ModelKey -- this is only intended for the key of the instance, and doesn't
              make sense to send in messages
  ComputedProperty -- a variant of this class is needed to determine the type
                      desired of the output. Such a variant is provided in
                      properties
"""

from .. import utils

from protorpc import messages

from google.appengine.ext import ndb
from google.appengine.ext.ndb import msgprop


__all__ = []


GeoPtMessage = utils.GeoPtMessage
RaiseNotImplementedMethod = utils.RaiseNotImplementedMethod
UserMessage = utils.UserMessage

MODEL_KEY_EXPLANATION = (
    'A model key property can\'t be used to define an EndpointsModel. These '
    'are intended to be used as the lone key of an entity and all ModelKey '
    'properties on an entity will have the same value.')
COMPUTED_PROPERTY_EXPLANATION = (
    'A computed property can\'t be used to define an EndpointsModel. The type '
    'of the message field must be explicitly named; this can be done by using '
    'the property EndpointsComputedProperty.')

NDB_PROPERTY_TO_PROTO = {
    ndb.BlobKeyProperty: messages.StringField,
    ndb.BlobProperty: messages.BytesField,  # No concept of compressed here
    ndb.BooleanProperty: messages.BooleanField,
    ndb.ComputedProperty: RaiseNotImplementedMethod(
        ndb.ComputedProperty,
        explanation=COMPUTED_PROPERTY_EXPLANATION),
    ndb.DateProperty: messages.StringField,
    ndb.DateTimeProperty: messages.StringField,
    ndb.FloatProperty: messages.FloatField,
    ndb.GenericProperty: RaiseNotImplementedMethod(ndb.GenericProperty),
    ndb.IntegerProperty: messages.IntegerField,
    ndb.JsonProperty: messages.BytesField,
    ndb.KeyProperty: messages.StringField,
    ndb.ModelKey: RaiseNotImplementedMethod(
        ndb.ModelKey,
        explanation=MODEL_KEY_EXPLANATION),
    ndb.PickleProperty: messages.BytesField,
    ndb.Property: RaiseNotImplementedMethod(ndb.Property),
    ndb.StringProperty: messages.StringField,
    ndb.TextProperty: messages.BytesField,  # No concept of compressed here
    ndb.TimeProperty: messages.StringField,
}


def GetKeywordArgs(prop, include_default=True):
  """Captures attributes from an NDB property to be passed to a ProtoRPC field.

  Args:
    prop: The NDB property which will have its attributes captured.
    include_default: An optional boolean indicating whether or not the default
        value of the property should be included. Defaults to True, and is
        intended to be turned off for special ProtoRPC fields which don't take
        a default.

  Returns:
    A dictionary of attributes, intended to be passed to the constructor of a
        ProtoRPC field as keyword arguments.
  """
  kwargs = {
      'required': prop._required,
      'repeated': prop._repeated,
  }
  if include_default and hasattr(prop, '_default'):
    kwargs['default'] = prop._default
  if hasattr(prop, '_variant'):
    kwargs['variant'] = prop._variant
  return kwargs


def MessageFromSimpleField(field, prop, index):
  """Converts a property to the corresponding field of specified type.

  Assumes index is the only positional argument needed to create an instance
  of {field}, hence only simple fields will work and an EnumField or
  MessageField will fail.

  Args:
    field: A ProtoRPC field type.
    prop: The NDB property to be converted.
    index: The index of the property within the message.

  Returns:
    An instance of field with attributes corresponding to those in prop and
        index corresponding to that which was passed in.
  """
  return field(index, **GetKeywordArgs(prop))


def StructuredPropertyToProto(prop, index):
  """Converts a structured property to the corresponding message field.

  Args:
    prop: The NDB property to be converted.
    index: The index of the property within the message.

  Returns:
    A message field with attributes corresponding to those in prop, index
        corresponding to that which was passed in and with underlying message
        class equal to the message class produced by the model class, which
        should be a subclass of EndpointsModel.

  Raises:
    TypeError if the model class of the property does not have a callable
        ProtoModel method. This is because we expected a subclass of
        EndpointsModel set on the structured property.
  """
  modelclass = prop._modelclass
  try:
    property_proto_method = modelclass.ProtoModel
    property_proto = property_proto_method()
  except (AttributeError, TypeError):
    error_msg = ('Structured properties must receive a model class with a '
                 'callable ProtoModel attribute. The class %s has no such '
                 'attribute.' % (modelclass.__name__,))
    raise TypeError(error_msg)

  # No default for {MessageField}s
  kwargs = GetKeywordArgs(prop, include_default=False)
  return messages.MessageField(property_proto, index, **kwargs)
NDB_PROPERTY_TO_PROTO[ndb.StructuredProperty] = StructuredPropertyToProto
# Ignore fact that LocalStructuredProperty is just a blob in the datastore
NDB_PROPERTY_TO_PROTO[ndb.LocalStructuredProperty] = StructuredPropertyToProto


def EnumPropertyToProto(prop, index):
  """Converts an enum property from a model to a message field.

  Args:
    prop: The NDB enum property to be converted.
    index: The index of the property within the message.

  Returns:
    An enum field with attributes corresponding to those in prop, index
        corresponding to that which was passed in and with underlying enum type
        equal to the enum type set in the enum property.
  """
  enum = prop._enum_type
  kwargs = GetKeywordArgs(prop)
  return messages.EnumField(enum, index, **kwargs)
NDB_PROPERTY_TO_PROTO[msgprop.EnumProperty] = EnumPropertyToProto


def MessagePropertyToProto(prop, index):
  """Converts a message property from a model to a message field.

  Args:
    prop: The NDB message property to be converted.
    index: The index of the property within the message.

  Returns:
    A message field with attributes corresponding to those in prop, index
        corresponding to that which was passed in and with underlying message
        class equal to the message type set in the message property.
  """
  message_type = prop._message_type
  # No default for {MessageField}s
  kwargs = GetKeywordArgs(prop, include_default=False)
  return messages.MessageField(message_type, index, **kwargs)
NDB_PROPERTY_TO_PROTO[msgprop.MessageProperty] = MessagePropertyToProto


def GeoPtPropertyToProto(prop, index):
  """Converts a model property to a Geo Point message field.

  Args:
    prop: The NDB property to be converted.
    index: The index of the property within the message.

  Returns:
    A message field with attributes corresponding to those in prop, index
        corresponding to that which was passed in and with underlying message
        class equal to GeoPtMessage.
  """
  # No default for {MessageField}s
  kwargs = GetKeywordArgs(prop, include_default=False)
  return messages.MessageField(GeoPtMessage, index, **kwargs)
NDB_PROPERTY_TO_PROTO[ndb.GeoPtProperty] = GeoPtPropertyToProto


def UserPropertyToProto(prop, index):
  """Converts a model property to a user message field.

  Args:
    prop: The NDB property to be converted.
    index: The index of the property within the message.

  Returns:
    A message field with attributes corresponding to those in prop, index
        corresponding to that which was passed in and with underlying message
        class equal to UserMessage.
  """
  # No default for {MessageField}s
  kwargs = GetKeywordArgs(prop, include_default=False)
  return messages.MessageField(UserMessage, index, **kwargs)
NDB_PROPERTY_TO_PROTO[ndb.UserProperty] = UserPropertyToProto
