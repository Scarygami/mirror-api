# Copyright 2013 Google Inc. All Rights Reserved.

"""Run all unittests.

Idea borrowed from ndb project:
code.google.com/p/appengine-ndb-experiment/source/browse/ndb/ndb_test.py
"""


import os
import subprocess
import sys
import unittest


MODULES_TO_TEST = ['utils']
NO_DEVAPPSERVER_TEMPLATE = ('Either dev appserver file path %r does not exist '
                            'or dev_appserver.py is not on your PATH.')


def fix_up_path():
  """Changes import path to make all dependencies import correctly.

  Performs the following:
  - Removes the 'google' module from sys.modules, if it exists, since
    this could cause the google.appengine... imports to fail.
  - Follow the symlink that puts dev_appserver.py on the user's path
    to find the App Engine SDK and add the SDK root to the path.
  - Import dev_appserver from the SDK and fix up the path for imports using
    dev_appserver.fix_sys_path.
  - Add the current git project root to the import path.
  """
  # May have namespace conflicts with google.appengine.api...
  # such as google.net.proto
  sys.modules.pop('google', None)

  # TODO(dhermes): Support finding the correct location on Windows too.
  # Find where dev_appserver.py is installed locally. If dev_appserver.py
  # is not on the path, then 'which' will exit with status code 1 and
  # subprocess.check_output will raise an exception.
  dev_appserver_on_path = subprocess.check_output(
      ['which', 'dev_appserver.py']).strip()
  if not os.path.exists(dev_appserver_on_path):
    print >>sys.stderr, NO_DEVAPPSERVER_TEMPLATE % (dev_appserver_on_path,)
    raise SystemExit(1)

  real_path = os.path.realpath(dev_appserver_on_path)
  sys.path.insert(0, os.path.dirname(real_path))
  import dev_appserver
  # Use fix_sys_path to make all App Engine imports work
  dev_appserver.fix_sys_path()

  project_root = subprocess.check_output(
      ['git', 'rev-parse', '--show-toplevel']).strip()
  sys.path.insert(0, project_root)


def load_tests(import_location):
  """Loads all tests for modules and adds them to a single test suite.

  Args:
    import_location: String; used to determine how the endpoints_proto_datastore
        package is imported.

  Returns:
    Instance of unittest.TestSuite containing all tests from the modules in
        this library.
  """
  test_modules = ['%s_test' % name for name in MODULES_TO_TEST]
  endpoints_proto_datastore = __import__(import_location,
                                         fromlist=test_modules, level=1)

  loader = unittest.TestLoader()
  suite = unittest.TestSuite()

  for module in [getattr(endpoints_proto_datastore, name)
                 for name in test_modules]:
    for name in set(dir(module)):
      try:
        if issubclass(getattr(module, name), unittest.TestCase):
          test_case = getattr(module, name)
          tests = loader.loadTestsFromTestCase(test_case)
          suite.addTests(tests)
      except TypeError:
        pass

  return suite


def main():
  """Fixes up the import path and runs all tests.

  Also makes sure it can import the endpoints_proto_datastore package and passes
  the import location along to load_tests().
  """
  fix_up_path()
  # As the number of environments goes up (such as Google's production
  # environment), this will expand to include those.
  import endpoints_proto_datastore
  import_location = 'endpoints_proto_datastore'

  v = 1
  for arg in sys.argv[1:]:
    if arg.startswith('-v'):
      v += arg.count('v')
    elif arg == '-q':
      v = 0
  result = unittest.TextTestRunner(verbosity=v).run(load_tests(import_location))
  sys.exit(not result.wasSuccessful())


if __name__ == '__main__':
  main()
