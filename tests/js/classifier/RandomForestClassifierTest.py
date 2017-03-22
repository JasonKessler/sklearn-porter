# -*- coding: utf-8 -*-

import unittest

from sklearn.ensemble import RandomForestClassifier
from sklearn_porter import Porter

from ..JavaScriptTest import JavaScriptTest


class RandomForestClassifierTest(JavaScriptTest, unittest.TestCase):

    def setUp(self):
        super(RandomForestClassifierTest, self).setUp()
        mdl = RandomForestClassifier(n_estimators=100, random_state=0)
        self._port_model(mdl)

    def tearDown(self):
        super(RandomForestClassifierTest, self).tearDown()
