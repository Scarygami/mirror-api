# Copyright 2013 Google Inc. All Rights Reserved.

"""Tests for utils.py."""


import unittest

from protorpc import messages

from . import utils


class UtilsTests(unittest.TestCase):
  """Comprehensive test for the endpoints_proto_datastore.utils module."""

  def testIsSubclass(self):
    """Tests the utils.IsSubclass method."""
    self.assertTrue(utils.IsSubclass(int, int))

    self.assertTrue(utils.IsSubclass(bool, int))
    self.assertTrue(utils.IsSubclass(str, (str, basestring)))
    self.assertFalse(utils.IsSubclass(int, bool))

    # Make sure this does not fail
    self.assertFalse(utils.IsSubclass(int, None))

  def testDictToTuple(self):
    """Tests the utils._DictToTuple method."""
    # pylint:disable-msg=W0212
    self.assertRaises(AttributeError, utils._DictToTuple, None)

    class Simple(object):
      items = None  # Not callable
    self.assertRaises(TypeError, utils._DictToTuple, Simple)

    single_value_dictionary = {1: 2}
    self.assertEqual((1,), utils._DictToTuple(single_value_dictionary))

    multiple_value_dictionary = {-5: 3, 1: 1, 3: 2}
    self.assertEqual((1, 3, -5), utils._DictToTuple(multiple_value_dictionary))
    # pylint:enable-msg=W0212

  def testGeoPtMessage(self):
    """Tests the utils.GeoPtMessage protorpc message class."""
    geo_pt_message = utils.GeoPtMessage(lat=1.0)
    self.assertEqual(geo_pt_message.lat, 1.0)
    self.assertEqual(geo_pt_message.lon, None)
    self.assertFalse(geo_pt_message.is_initialized())

    geo_pt_message.lon = 2.0
    self.assertEqual(geo_pt_message.lon, 2.0)
    self.assertTrue(geo_pt_message.is_initialized())

    self.assertRaises(messages.ValidationError,
                      utils.GeoPtMessage, lat='1', lon=2)

    self.assertRaises(TypeError, utils.GeoPtMessage, 1.0, 2.0)

    self.assertRaises(AttributeError, utils.GeoPtMessage,
                      lat=1.0, lon=2.0, other=3.0)

    geo_pt_message = utils.GeoPtMessage(lat=1.0, lon=2.0)
    self.assertTrue(geo_pt_message.is_initialized())


if __name__ == '__main__':
  unittest.main()
