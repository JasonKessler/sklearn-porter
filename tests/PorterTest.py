# -*- coding: utf-8 -*-

import random
import time
import subprocess as subp
import unittest
import filecmp
import os

from sklearn.datasets import load_iris
from sklearn.externals import joblib
from sklearn.tree import tree
from sklearn.utils import shuffle

from sklearn_porter import Porter


class PorterTest(unittest.TestCase):

    TEST_DEPENDENCIES = ['mkdir', 'rm', 'java', 'javac']

    def setUp(self):
        self._check_test_dependencies()
        self._init_test()
        self._train_model()
        self._port_model()
        self._start_test()

    def tearDown(self):
        self._clear_model()
        self._stop_test()

    def _check_test_dependencies(self):
        # $ if hash gcc 2/dev/null; then echo 1; else echo 0; fi
        for dep in self.TEST_DEPENDENCIES:
            cmd = 'if hash {} 2/dev/null; then ' \
                  'echo 1; else echo 0; fi'.format(dep)
            available = subp.check_output(cmd, shell=True, stderr=subp.STDOUT)
            available = available.strip() is '1'
            if not available:
                error = "The required test dependency '{0}'" \
                        " is not available.".format(dep)
                self.fail(error)

    def _init_test(self):
        self.tmp_fn = 'Brain'
        self.n_random_tests = 150
        if 'N_RANDOM_TESTS' in set(os.environ):
            n_tests = os.environ.get('N_RANDOM_TESTS')
            if str(n_tests).strip().isdigit():
                n_tests = int(n_tests)
                if n_tests > 0:
                    self.n_random_tests = n_tests

    def _train_model(self, random_state=0):
        data = load_iris()
        self.X = shuffle(data.data, random_state=random_state)
        self.y = shuffle(data.target, random_state=random_state)
        self.n_features = len(self.X[0])
        self.clf = tree.DecisionTreeClassifier(random_state=random_state)
        self.clf.fit(self.X, self.y)

    def _start_test(self):
        self.startTime = time.time()

    def _stop_test(self):
        print('%.3fs' % (time.time() - self.startTime))

    def _port_model(self):
        """Create and compile ported model for comparison of predictions."""
        # $ rm -rf temp
        subp.call(['rm', '-rf', 'tmp'])
        # $ mkdir temp
        subp.call(['mkdir', 'tmp'])
        filename = '{}.java'.format(self.tmp_fn)
        path = os.path.join('tmp', filename)
        with open(path, 'w') as f:
            out = Porter(self.clf).export(method_name='predict',
                                          class_name=self.tmp_fn)
            f.write(out)
        # $ javac temp/Tmp.java
        subp.call(['javac', path])

    def _clear_model(self):
        """Remove all temporary test files."""
        self.clf = None
        # $ rm -rf temp
        subp.call(['rm', '-rf', 'tmp'])

    def test_porter_args_method(self):
        """Test invalid method name."""
        args = dict(method='random')
        self.assertRaises(AttributeError,
                          lambda: Porter(self.clf, args))

    def test_porter_args_language(self):
        """Test invalid programming language."""
        args = dict(method='predict', language='random')
        self.assertRaises(AttributeError,
                          lambda: Porter(self.clf, args))

    def test_python_command_execution(self):
        """Test command line execution."""

        # Rename model for comparison:
        filename = '{}.java'.format(self.tmp_fn)
        cp_src = os.path.join('tmp', filename)
        filename = '{}_2.java'.format(self.tmp_fn)
        cp_dest = os.path.join('tmp', filename)
        # $ mv temp/Brain.java temp/Brain_2.java
        subp.call(['mv', cp_src, cp_dest])

        # Dump model:
        filename = '{}.pkl'.format(self.tmp_fn)
        pkl_path = os.path.join('tmp', filename)
        joblib.dump(self.clf, pkl_path)

        # Port model:
        cmd = ['python', '-m', 'sklearn_porter', '-i', pkl_path]
        subp.call(cmd)
        # Compare file contents:
        equal = filecmp.cmp(cp_src, cp_dest)

        self.assertEqual(equal, True)

    def test_java_command_execution(self):
        """Test whether the prediction of random features match or not."""
        # Create random features:
        Y, Y_py = [], []
        for n in range(self.n_random_tests):
            x = [random.uniform(0., 10.) for n in range(self.n_features)]
            y_py = int(self.clf.predict([x])[0])
            Y_py.append(y_py)
            y = self.make_pred_in_custom(x)
            Y.append(y)
        self.assertEqual(Y_py, Y)

    def make_pred_in_custom(self, features):
        """Run Java prediction on the command line."""
        # $ java -classpath temp <temp_filename> <features>
        cmd = ['java', '-classpath', 'tmp', self.tmp_fn]
        args = [str(f).strip() for f in features]
        cmd += args
        pred = subp.check_output(cmd, stderr=subp.STDOUT)
        return int(pred)
