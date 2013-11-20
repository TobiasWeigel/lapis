.. lapis documentation master file, created by
   sphinx-quickstart on Wed May 23 15:39:58 2012.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to the Lapis documentation!
===========================================================

The Lapis API for Persistent Identifier Services python package can be used by domain-specific services to create and manage
Digital Objects (Kahn & Wilensky 2006). On the user's side, high-level APIs provide simplified interaction with 
the backend Digital Object / Persistent Identifier infrastructure. The basic idea is that users do not have to know
about Digital Objects and their storage methods at all, and just get a plain view of events and (perhaps) PIDs.  

Contents:

.. toctree::
   :maxdepth: 2
   
   examples
   highlevelarchitecture
   infrastructure
   digitalobject
   c3api
   

Current status
==============

The top-level API offers the following **stable** services:

* creation, removal and modification of PIDs
* single resource links for a PID including a resource type
* arbitrary annotations for PIDs (Handle key-metadata)
* typed PID-to-PID references
* basic PID collection (PID set) operations, including add, remove, iterate and containment queries
* support for different low-level PID infrastructures/architectures
* extensive unit testing of the implemented features using Nose

The following services are currently **under construction**:

* Full support for the EPIC API v2 as an infrastructural layer (some parts are not implemented yet)

The package does not guarantee exchangability of the underlying architecture, meaning that e.g. PIDs created in native Handle system mode are not guaranteed to be compatible with reading mechanisms of the EPIC API mode.
The package is also not optimized for request efficiency, meaning that a single simple API call may result in multiple calls to the underlying infrastructure. This is a consequence of the current modular approach that tries to abstract from a specific infrastructure. If future developments turn out to focus on a single infrastructure, the request mechanisms may be simplified.

Prerequisites for running the service
=====================================

There are two infrastructure configurations this software is currently able to work on: native Handle system mode and EPIC APIv2 mode.
The top-level API operations behave the same way independent of the architecture chosen for the lower level.

Native Handle system mode
-------------------------

All API calls will be broken down into operations for the native Handle System Java API.
This mode requires:

* operational 'handle-rest' service

 * github project site: https://github.com/TobiasWeigel/handle-rest
 
* a Java Servlet container (e.g. Tomcat) for the handle-rest service
* a Handle server with full administrative rights

EPIC APIv2 mode
---------------

All API calls are redirected to the RESTful EPIC API service, implemented in JRuby.
This mode requires:

* operational EPIC API v2 service

 * github project site: https://github.com/CatchPlus/EPIC-API-v2
 * documentation available here: http://catchplus.github.com/EPIC-API-v2/
 
* consequently, also a Handle server with full administrative rights, working on a MySQL database



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

