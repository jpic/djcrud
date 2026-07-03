View mixins
~~~~~~~~~~~

djcrud composes generic views from these mixins. Set class attributes on a
cloned view (``ListView.clone(paginate_by=10)``) or on a subclass. Templates
receive the view instance as ``view`` in context.

:doc:`../view` documents :class:`~djcrud.view.ViewMixin`. :doc:`../model` documents
:class:`~djcrud.model.ModelMixin`.

.. toctree::
   :maxdepth: 1

   template
   template_view
   list
   filter
   pagination
   tables2
   form
   modelform
   object
   objectform
   object_modelform
   action
   delete
   list_action
   log