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

"""
=============
 Quickimport
=============

The module :mod:`quickimport` provides an improved importer for python. If 
you ever started a Python application from a lame file server (like 
a CIFS server) you know the problem of long startup times. Usually 
the long startup time is caused by the enormous number of 
:c:func:`stat()` calls required to locate the module. For each directory
on ``sys.path`` (or on the package specific search path) and for each
possible suffix (see function :func:`imp.get_suffixes`) Python 
probes the existence of a module or a package using the 
C-function call :c:func:`stat()`. If your search path contains several 
directories (if you use easy_install, it usually contains many directories),
you end up with several thousands :c:func:`stat()` calls. Most of 
these calls fail, because the probed file does not exist. 

The basic idea of Quickimport is to avoid those :c:func:`stat()` calls
that will fail for sure, because there is no matching 
file in the directory in question. If we assume, that the content of
the directory does not change while our application is running, we can 
read the directory content once. A perfect implementation of this concept
requires a patch for python. Fortunately we can use the PEP-302 import
hooks to create a nearly perfect version, that skips directories 
not containing any candidate for the wanted module or package. 
You only need to invoke the function :func:`install` early enough.
This function installs a PEP-302 importer and optionally 
eliminates directories without any Python modules or packages from 
``sys.path``.

Another option to speed up lame imports is to store many modules into 
a zip-archive. The time required to extract modules from a zip-archive 
is usually much lower than the time to locate the modules on the 
file system and to read them. Therefore ``sys.path`` already contains
an entry for a zip-archive ``pythonXY.zip``. The function 
:func:`buildZip` creates such a zip-archive for you.

.. warning::
   Although the author is using the module quickimport in production, it is 
   more or less untested outside the specific environment it was written for.

.. autofunction:: install

.. autofunction:: isDirRelevant

.. autofunction:: prepareCache

.. autofunction:: buildZip

.. autoclass:: QuickimportFinder

.. autoclass:: QuickimportFinder_NoAutoload

"""



from __future__ import absolute_import

import sys
from imp import acquire_lock, release_lock, find_module, get_suffixes
import pkgutil
from pkgutil import ImpLoader
import os.path

suffixes = [ os.path.normcase(s[0]) for s in get_suffixes() ]

__all__ = []

def buildZip(zipname=None):
    """
    Build a zip-archive containing all suitable top-level modules.
    
    This function creates the zip-archive `zipname` and adds
    a compiled version of every suitable top-level module to the
    archive. A module is suitable, if the module's Python source 
    code is available and does not reference the __path__ or 
    __file__ members.
    
    This function uses the python :mod:`logging` system to report
    its progress. Set the log level to ``INFO`` or ``DEBUG`` to get
    progress information.
    
    You can run this module as a pathon script to invoke this function::
    
        python -m quickimport [zipname]
    
    :param zipname: the name of the archive. If not given, the function 
        uses the name of the ``pythonXY.zip``-item of ``sys.path``. 
    :type zipname: str or unicode
    """
    import logging
    LOGGER = logging.getLogger(__name__)
    import collections
    import zipfile
    
    try:
        from quickimport import FindFastFinder as FindFastFinder2
    except ImportError:
        FindFastFinder2 = QuickimportFinder
    
    for h in sys.path_hooks[:]:
        if isinstance(h, type) and issubclass(h, (QuickimportFinder, FindFastFinder2)):
            sys.path_hooks.remove(h)
            sys.path_importer_cache.clear()
            
    if zipname is None:
        for item in sys.path:
            if (os.path.isabs(item) and 
                os.path.normcase(os.path.basename(item)) == 
                os.path.normcase("python%s%s%szip" % (sys.version_info[0], sys.version_info[1], os.extsep))):
                zipname = item
                break
        else:
            raise RuntimeError("Failed to determine zipname from sys.path. Please provide the zipname argument.")

    LOGGER.info("Creating zip archive %r ...", zipname)

    files = collections.OrderedDict()
    for dir in sys.path:
        if os.path.normcase(os.path.realpath(dir)) == os.path.normcase(os.path.realpath(zipname)):
            continue
        LOGGER.info("Scanning dir %r", dir)
        try:
            for module_loader, name, ispkg in pkgutil.iter_modules([dir]):
                if name in files:
                    LOGGER.info("Module %r already found as %r", name, files[name])
                    continue
                
                files[name] = None
                
                if ispkg:
                    LOGGER.info("Omitting package %r", name)
                    continue
                
                module_loader = module_loader.find_module(name)
                
                filename = module_loader.get_filename(name)
                source = module_loader.get_source(name)
                if source is None:
                    LOGGER.info("Omitting module %r: no source", name)
                    continue
                if "__file__" in source or "__path__" in source:
                    LOGGER.info("Omitting module %r: __file__ or __path__ in source", name)
                    continue

                LOGGER.debug("Selecting module %r: %r", name, filename)
                files[name] = filename
                
        except OSError, e:
            LOGGER.warn("Exeception in dir %r: %s", dir, e)
    
    if os.path.exists(zipname):
        if not os.path.isfile(zipname) or os.path.islink(zipname):
            raise ValueError("Must be a regular file: %r" % (zipname,))
        LOGGER.warn("Zipfile already exists, going to remove it: %r", zipname)
        os.unlink(zipname)
    f = zipfile.PyZipFile(zipname, "w", zipfile.ZIP_DEFLATED, True)
    
    for filename in files.itervalues():
        if filename is not None:
            f.writepy(filename)
    f.close()
    LOGGER.info("Created zip archive %r", zipname)
            

def isDirRelevant(dir):
    """
    Test is a given directory contains any entries that
    could be modules or packages.
    
    :param dir: the directory to inspect
    :type dir: str or unicode
    :returns: `True` if the directory might contain Python modules or packages.
              `False` otherwise.
    :rtype: bool
    
    """
    if sys.path_importer_cache.get(dir, True) is not None:
        return True

    if not os.path.isabs(dir):
        return True

    isdir = os.path.isdir
    if not isdir(dir):
        return False

    listdir = os.listdir
    try:
        files = listdir(dir)
    except Exception:
        # Dir is unreadable, assume it contains modules
        return True

    normcase = os.path.normcase
    # First pass: look for matching module names
    for f in files:
        for s in suffixes:
            if normcase(f).endswith(s):
                return True

    # second pass: look for packages
    join = os.path.join
    initfiles = [ normcase('__init__' + s) for s in suffixes ]
    for f in files:
        d = join(dir,f)
        if not isdir(d):
            continue
        try:
            dfiles = listdir(d)
        except Exception:
            # Dir is unreadable, assume it contains modules
            return True
        for ff in dfiles:
            if normcase(ff) in initfiles:
                return True

    # Nothing suitable found
    return False

def prepareCache(path=None, cache=None):
    """
    Create or update the directory cache for :class:`QuickimportFinder`.
    
    :param path: a list of path entries to process
    :type path: :class:`list`
    :param cache: the cache dictionary. If not given, a new dictionary is used
    :type cache: dict
    :returns: the cache dictionary
    :rtype: :class:`dict`
    """
    if path is None:
        path = sys.path
    if cache is None:
        cache = {}
        
    isdir = os.path.isdir
    isabs = os.path.isabs
    listdir = os.listdir
    normcase = os.path.normcase
    for dir in path:
        if not isabs(dir) or not isdir(dir):
            continue
        try:
            files = map(normcase, listdir(dir))
        except Exception:
            continue
        cache[dir] = frozenset(files)
    return cache

class QuickimportFinder(object):
    """
    A PEP-302 finder class for the ``sys.path_hooks`` hook.
    
    This class uses the directory cache ``sys.quickimport_cache``
    to store the content of directories from ``sys.path`` or 
    from package specific search path lists.
    
    .. py:attribute:: autocache
        
        If the class-attribute `autocache` is ``True``, the 
        method :meth:`__init__` tries to add new directories 
        to ``sys.quickimport_cache`` on the fly. If set to ``False``, 
        :meth:`__init__` will not modify the content of ``sys.quickimport_cache``.
        The default value of this attribute is ``True`` for class
        :class:`QuickimportFinder` and ``False`` for class
        :class:`QuickimportFinder_NoAutoload`.
            
    """
    __slots__ = ("dir")
    autocache = True
    """
    The autocache class attribute 
    """

    def __init__(self, dir):
        try:
            cache = sys.quickimport_cache
        except AttributeError:
            pass
        else:
            if dir in cache:
                self.dir = dir
                return
            if self.autocache:
                prepareCache([dir], cache)
                if dir in cache:
                    self.dir = dir
                    return
        raise ImportError("no cache for %r" % (dir,))
            
    def find_module(self, fullname, path=None):
        # print >> sys.stderr, "find_module (%s): %r" % (self.dir, fullname), 
        acquire_lock()
        try:
            dir = self.dir
            try:
                files = sys.quickimport_cache[dir]
            except Exception, e:
                raise ImportError("Can't import %r: No quickimport dir cache for dir %r: %s" % (fullname, dir, e) )
            basename = fullname.rsplit('.', 1)[-1]
            basenameNormcase = os.path.normcase(basename)
            if not basenameNormcase in files:
                for s in suffixes:
                    if (basenameNormcase + s) in files:
                        break
                else:
                    # print >> sys.stderr, ""
                    return None
            # this path is a candidate
            importer = sys.path_importer_cache.get(dir)
            assert importer is self
            try:
                # print >> sys.stderr, "testing.. ",
                return ImpLoader(fullname, *find_module(basename, [dir]))
            except ImportError, e:
                # print >> sys.stderr, e
                return None
        finally:
            release_lock()
            
class QuickimportFinder_NoAutoload(QuickimportFinder):
    """
    A variant of class :class:`QuickimportFinder` with
    :attr:`autocache` set to ``False``.
    """
    autocache = False

def install(keepSysPath=None, noChache=None):
    """
    Install the Quickimport importer.
    
    This function optionally
    
    * removes directories without any modules or packages from
      ``sys.path``.
    * appends the PEP-302 importer :class:`QuickimportFinder` 
      to the end of the ``sys.path_hooks`` list.
    
    :param keepSysPath: if ``bool(keepSysPath)`` is ``True``, 
       do not modify ``sys.path``.
    :param noCache: if ``bool(noCache)`` is ``True``, 
       do not modify ``sys.path_hooks``.
    """
    acquire_lock()
    try:
        if not keepSysPath:
            sys.path[:] = filter(isDirRelevant, sys.path)
               
        if not noChache:
            sys.quickimport_cache = cache = prepareCache()
            sys.path_hooks.append(QuickimportFinder)
            for dir in cache.keys():
                if sys.path_importer_cache.get(dir) is None:
                    sys.path_importer_cache.pop(dir, None)
                else:
                    del cache[dir]
    finally:
        release_lock()
    

if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG)
    buildZip(*sys.argv[1:])
