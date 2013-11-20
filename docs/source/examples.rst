.. _examples:

Usage examples
==============

In general, usage can also be understood by looking at the test classes that are run by nose.

The first example shows how to create and query a digital object. 
For this to work, we first need to set up some infrastructure class, and then issue a create command and a lookup. 
For testing, we can always use the InMemoryInfrastructure class, which does not persist any information. In this example
however, we will use a proper Handle Server as the backend. ::

  # parameters
  host = "handle.example.com"
  port = 8090
  urlpath = "/handle/"
  prefix = "12345"
  do_infra = HandleInfrastructure(host, port, urlpath, prefix)  
  # now issue a Handle
  my_digital_object = do_infra.create_do(prefix+"testhandle")
  my_digital_object.resource_location = "http://www.google.com"
  # lookup should also work
  retrieved_object = do_infra.lookup_pid(prefix+"testhandle")
  
Note that the HandleInfrastructure class does not interact directly with a Handle Server, but requires a small servlet inbetween since
the Handle System up to version 7 does not offer a HTTP/RESTful interface. A quick and dirty implementation of such a minimal
service servlet can be found here: https://github.com/TobiasWeigel/handle-rest

To work with collections, we simply specify an optional parameter to create_do, which effectively expresses a factory pattern. ::

  # create a set and add an element
  my_set = do_infra.create_do(prefix+"myset", DigitalObjectSet)
  my_set.add_do(my_digital_object)
  # create an array and add an element
  my_array = do_infra.create_do(prefix+"myarray", DigitalObjectArray)
  my_array.add_do(my_digital_object)
  # create a linked list and add an element
  my_linkedlist = do_infra.create_do(prefix+"mylinkedlist", DigitalObjectLinkedList)
  my_linkedlist.add_do(my_digital_object)
  # retrieve a set and iterate
  retrieved_set = do_infra.lookup_pid(prefix+"myset")
  assert isinstance(retrieved_set, DigitalObjectSet)   # should pass
  # print element PIDs
  num_subele = 0
  for sele in retrieved_set.iter_set_elements():
    print(sele.identifier)  
        
The set, array and linked list objects store their membership information in PID records so that it persists together with
the PID itself. Note that these implicit membership relations are bilateral: Adding an element to a set will cause changes
in this element's PID record as well. 
Luckily, using these features however usually does not require that one understands all of these details, as such collection
mechanics are designed explicitly to be treated as black boxes.


  

