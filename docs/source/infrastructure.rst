.. _infrastructure:

Infrastructure classes
======================

The infrastructural abstraction layer is formed through a class hierarchy with the class DOInfrastructure_ 
at the top. The class forms a Factory pattern and can manufacture instances of Python-native DigitalObject_ instances.
The basic idea is that user code can request new or retrieve existing Digital Objects through the factory and
interact with the Digital Objects natively. The DigitalObject methods redirect calls to the underlying Infrastructure
instance, which will map them, to a physical PID/DO infrastructure such as the Handle System.

.. autoclass::dkrz.digitalobjects.infra.infrastructure.DOInfrastructure

.. autoclass::dkrz.digitalobjects.infra.infrastructure.InMemoryInfrastructure

.. autoclass::dkrz.digitalobjects.infra.handleinfrastructure.HandleInfrastructure 