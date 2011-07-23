About Quickimport
=================

The module quickimport provides an improved importer for python. If 
you ever started a Python application from a lame file server (like 
a CIFS server) you know the problem of long startup times. The quickimport
importer uses the PEP-302 import hooks to reduce the number of 
failing stat system calls for each loaded module.

The code was developed as part of a commercial project and released as free
software under the GNU Lesser General Public License by 
science + computing ag. The software is copyrighted by 
science + computing ag.

Why did we decide to make Quickimport free software? We utilise Python and 
other open source products a lot. Therefore we think it is just fair
to release enhancements back to the public. 


Requirements
------------

* Python 2.7 (may work on earlier versions too)

(Sorry, currently no Python 3 support)  
 

Installation
------------

Get easy_install and do "easy_install quickimport".
Or get the latest source code from github.
git clone git://github.com/akruis/quickimport.git

Using Quickimport
-----------------

Invoke the function quickimport.install() early during application 
startup. You can use a .pth-file to do it.


Support
=======
There is currently no support available, but you can drop me a mail.
a [dot] kruis [at] science-computing [dot] de  

Plan
====
No further plans currently

Changes
=======



Version 0.0.1
-------------
Initial version, released by science + computing ag. This version is more or 
less a copy of a module from the flowGuide2 source code. The code works
for the specific requirements of flowGuide2, but has not been tested outside
of the flowGuide2 environment. 
