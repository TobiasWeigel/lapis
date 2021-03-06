.. _infrastructure:

======================
Infrastructure classes
======================

The infrastructural abstraction layer is formed through a class hierarchy with the class `DOInfrastructure`_
at the top. The class forms a Factory pattern and can manufacture instances of Python-native :doc:`digitalobject` instances.
The basic idea is that user code can request new or retrieve existing Digital Objects through the factory and
interact with the Digital Objects natively. The DigitalObject methods redirect calls to the underlying Infrastructure
instance, which will map them, to a physical PID/DO infrastructure such as the Handle System.

.. _doinfrastructure:

Infrastructure Base Class
------------------------- 

.. autoclass:: lapis.infra.infrastructure.DOInfrastructure

In-Memory-Infrastructure Class
------------------------------

.. autoclass:: lapis.infra.infrastructure.InMemoryInfrastructure

Handle Infrastructure Class
---------------------------

.. autoclass:: lapis.infra.handleinfrastructure.HandleInfrastructure 

Exceptions
----------

.. autoexception:: lapis.infra.handleinfrastructure.PIDAlreadyExistsError