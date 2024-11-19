Usage
=====

.. _installation:

Installation
------------

To use piec, first install it using pip:

.. code-block:: console

   (.venv) $ pip install piec

Then if using GPIB to communicate installInstall NI 488.2 Drivers from
https://www.ni.com/en/support/downloads/drivers/download.ni-488-2.html#544048

NOTE: If using digilient drivers then optional install of UL is required:
http://www.mccdaq.com/swdownload
Creating recipes
----------------

To retrieve a list of random ingredients,
you can use the ``lumache.get_random_ingredients()`` function:

.. autofunction:: lumache.get_random_ingredients

The ``kind`` parameter should be either ``"meat"``, ``"fish"``,
or ``"veggies"``. Otherwise, :py:func:`lumache.get_random_ingredients`
will raise an exception.

.. autoexception:: lumache.InvalidKindError

For example:

>>> import piec as pc
>>> from pc.drivers.keysight81150a import Keysight81150a
['shells', 'gorgonzola', 'parsley']

