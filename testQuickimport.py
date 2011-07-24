#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2011 by science+computing ag
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
# 
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
#

from __future__ import absolute_import

from unittest import TestCase, skipIf
import os.path
import tempfile
import sys

import quickimport as q
DIR1 = os.path.dirname(os.path.abspath(__file__))

class QuickimportTest(TestCase):
    def setUp(self):
        self.origSysPath = sys.path[:]
        self.origPathHooks = sys.path_hooks[:]
        self.origPIC = dict(sys.path_importer_cache)
    def tearDown(self):
        q.uninstall()
        sys.path[:] = self.origSysPath
        sys.path_hooks[:] = self.origPathHooks
        sys.path_importer_cache.clear()
        sys.path_importer_cache.update(self.origPIC)
    
    def testReadAndAnalyseDir(self):
        relevant, files = q.readAndAnalyseDir(DIR1)
        self.assertTrue(relevant)
        self.assertIn("quickimport.py", files)
        
        emptyDir = tempfile.mkdtemp()
        try:
            relevant, files = q.readAndAnalyseDir(emptyDir)
        finally:
            os.rmdir(emptyDir)
        self.assertFalse(relevant)
        self.assertEqual([], files)
        
        # not a dir 
        relevant, files = q.readAndAnalyseDir(os.path.abspath(__file__))
        self.assertFalse(relevant)
        self.assertIsNone(files)
        
        # not existent
        relevant, files = q.readAndAnalyseDir(os.path.join(os.path.abspath(os.getcwd()),"aNotExistingPath"))
        self.assertFalse(relevant)
        self.assertIsNone(files)
        
    def testUninstall(self):
        self.assertFalse(hasattr(sys, "quickimport_cache"))
        q.install("off")
        self.assertFalse(hasattr(sys, "quickimport_cache"))
        self.assertListEqual(self.origSysPath, sys.path)
        self.assertListEqual(self.origPathHooks, sys.path_hooks)
        self.assertDictEqual(self.origPIC, sys.path_importer_cache)
        
        q.install()
        self.assertTrue(hasattr(sys, "quickimport_cache"))
        self.assertTrue(sys.quickimport_cache[q.AUTOCHACHE_KEY])
        self.assertListEqual(self.origSysPath, sys.path)
        
        q.uninstall()
        self.assertFalse(hasattr(sys, "quickimport_cache"))
        self.assertListEqual(self.origSysPath, sys.path)
        self.assertListEqual(self.origPathHooks, sys.path_hooks)
        self.assertDictEqual(sys.path_importer_cache, {})
        
    def testInstall_filterSysPath(self):
        emptyDir = tempfile.mkdtemp()
        try:
            dirs = ["", "/somewhere/python27.zip", DIR1, emptyDir]
            q.install("noCache filterDirs", dirs)
        finally:
            os.rmdir(emptyDir)
        self.assertListEqual(dirs, ["", "/somewhere/python27.zip", DIR1])
        
    def testImports(self):
        q.install()
        import tabnanny
        sys.modules.pop("email", None)
        import email  # a package
        sys.modules.pop("email.message", None)
        import email.message
        self.assertRaises(ImportError, __import__, "NoSuchModule")
        
    