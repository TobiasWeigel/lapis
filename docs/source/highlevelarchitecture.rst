.. _highlevelarchitecture:

High-level architecture
=======================

The basic motivation of Lapis is to provide a more comfortable API and more sophisticated structures for PID creation and
overall organization of persistent objects. The basic architecture therefore resembles a central service layer, which 
connects on both top and bottom end to interchangeable modules:
 
 * At the top, project- or community-specific APIs should be implemented that provide easy to understand methods. 
   An event-driven architecture style may often seem the best solution.
 * At the bottom, a 'Digital Object Infrastructure' component can be plugged in that supports all calls from the top
   layer.
   
The basic idea is also to hold PID or Digital Object information in native Python object. All changes to these objects 
are directly mapped and executed on the DO infrastructure (e.g. the Handle System). The end-user of a project-specific
API is largely unaware of these operations.

The following figure roughly summarizes the concept:

.. image:: figures/lapis-stack.*
