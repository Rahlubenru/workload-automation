.. _migration-guide:

Migration Guide
================

.. contents:: Contents
   :depth: 4
   :local:

Users
"""""

Configuration
--------------

Default configuration file change
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Instead of the standard ``config.py`` file located at ``$WA_USER_HOME/config.py`
WA not use a ``confg.yaml`` files which is written in the YAML format instead of
python. Additionally upon first invocation WA3 will automatically try and detect
whether a WA2 config file is present and convert it to use the new WA3 format.
During this process any know parameter name changes should be detected and
updated accordingly.

Plugin Changes
^^^^^^^^^^^^^^^
Please note that not all plugins that were available for WA2 are currently
available for WA3 so you may need to remove plugins that are no longer present
from your config files. One plugin of note is the ``standard`` results
processor, this has been removed and it's functionality built into the core
framework.

--------------------------------------------------------

Agendas
-------

WA3 is designed to keep configuration as backwards compatible as possible so
most agendas should work out of the box, however the main changes in the style
of WA3 agendas are:

Global Section
^^^^^^^^^^^^^^
The ``global`` and ``config`` sections have been merged so now all configuration
that was specified under the "global" keyword can now also be specified under
"config". Although "global"  is still a valid keyword you will need to ensure that
there are not duplicated entries in each section.

Instrumentation and Results Processors merged
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``instrumentation`` and ``results_processors`` sections from WA2 have now
been merged into a single ``augmentations`` section to simplify the
configuration process. Although for backwards compatibility, support for the old
sections has be retained.


Per workload enabling of augmentations
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
All augmentations can now been enabled and disabled on a per workload basis.


Setting Runtime Parameters
^^^^^^^^^^^^^^^^^^^^^^^^^^
:ref:`Runtime Parameters <runtime-parmeters>` are now the preferred way of
configuring, cpufreq, hotplug and cpuidle rather setting the corresponding
sysfile values as this will perform additional validation and ensure the nodes
are set in the correct order to avoid any conflicts.

Parameter Changes ### TODO
^^^^^^^^^^^^^^^^^
Any parameter names changes  listed below will also have their old names
specified as aliases and should continue to work as normal, however going forward
the new parameter names should be preferred:

- The workload parameter ``clean_up`` has be renamed to ``cleanup_assets`` to
  better reflect its purpose.

- The workload parameter ``check_apk`` has been renamed to
  ``prefer_host_package`` to be more explicit in it's functionality to indicated
  whether a package on the target for the host should have priority when
  searching for a suitable package.


Output ### TODO
^^^^^^^
Output Directory
~~~~~~~~~~~~~~~~
The :ref:`output directory <output_directory>`'s structure has changed layout
and now includes additional subdirectories. There is now a ``__meta`` directory
that contains copies of the agenda and config files supplied to WA for that
particular run so that all the relevant config is self contained. Additionally
if one or more jobs fail during a run then corresponding output folder will be
moved into a ``__failed`` subdirectory to allow for quicker analysis.


Output API
~~~~~~~~~~
There is now an Output API which can be used to more easily post process the
output from a workload. For more information please see the
:ref:`Output API <output-api>` documentation.


-----------------------------------------------------------

Developers
""""""""""""

Framework
---------

Imports
^^^^^^^

To distinguish between the different versions of WA, WA3's package name has been
renamed to ``wa``. This means that all the old ``wlauto`` imports will need to
be updated. For more information please see the corresponding section in the
:ref:`developer reference section<developer_reference>`

Asset Deployment
^^^^^^^^^^^^^^^^^^
WA3 now contains a generic assets deployment and clean up mechanism so if a
workload was previously doing this in an ad-hoc manner this should be updated to
utilize the new functionality. To make use of this functionality a list of
assets should be set as the workload ``deployable_assets`` attribute, these will
be automatically retrieved via WA's resource getters and deployed either to the
targets working directory or a custom folder specified as the workloads
``assets_directory`` attribute. If a custom implementation is required the
``deploy_assets`` method should be overridden inside the workload. To allow for
the removal of the additional assets any additional file paths should be added
to the ``self.deployed_assets`` list which is used to keep track of any assets
that have been deployed for the workload. This is what is used by the generic
``remove_assets`` method to clean up any files deployed to the target.
Optionally if the file structure of the deployed assets requires additional
logic then the ``remove_assets`` method can be overridden for a particular
workload as well.

--------------------------------------------------------

Workloads
---------

Python Workload Structure
^^^^^^^^^^^^^^^^^^^^^^^^^^
The ``update_results`` method has been split out into 2 stages. There is now
``extract_results`` and ``update_output`` which should be used for extracting
any results from the target back to the host system and to update the output
with any metrics or artefacts for the specific workload iteration respectively.

APK Functionality
^^^^^^^^^^^^^^^^^
All apk functionality has re-factored into an APKHandler object which is
available as the apk attribute of the workload. This means that for example
``self.launchapplication()`` would now become ``self.apk.start_activity()``


UiAutomator Java Structure
^^^^^^^^^^^^^^^^^^^^^^^^^^
Instead of a single ``runUiAutomation`` method to perform all of the UiAutomation,
the structure has been refactored into 4 methods that can optionally be overridden.
The available methods are ``initialize``, ``setup``, ``runWorkload``, ``extactResults``
and ``teardown`` to better mimic the different stages in the python workload.


``initialize`` should have the ``@Before`` tag attached to the method which will cause it
to be ran before each of the stages of the workload. This method should be used to retrieve
and set any relevant parameters required during the workload.

The remaining method all have the ``@Test`` tag attached to the method to indicate that this
is a test stage that should be called at the appropriate time.

``setup`` should be used to perform any setup required for the workload, for
example dismissing popups or configuring and required settings.

``runWorkload`` should be used to perform the actual measurable work of the workload.

``extractResults`` should be used to extract any relevant results from the
target after the workload has been completed.

``teardown`` should be used to perform any final clean up of the workload on the target.

GUI Functionality
^^^^^^^^^^^^^^^^^
For UI based applications all UI functionality has been re-factored to into a
``gui`` attribute which currently will be either a ``UiAutomatorGUI`` object or
a ``ReventGUI`` depending on the workload type. This means that for example if
you wish to pass parameters to a UiAuotmator workload you will now need to use
``self.gui.uiauto_params['Parameter Name'] = value``

Attributes
^^^^^^^^^^
The ``device`` attribute of the workload is now a devlib ``target``. Some of the
command names remain the same, however there will be differences. The API can be
found here: http://devlib.readthedocs.io/en/latest/target.html however some of
the more common changes can be found below:


+----------------------------------------------+---------------------------------+
| Original Method                              | New Method                      |
+----------------------------------------------+---------------------------------+
|``self.device.pull_file(file)``               | ``self.target.pull(file)``      |
+----------------------------------------------+---------------------------------+
|``self.device.push_file(file)``               | ``self.target.push(file)``      |
+----------------------------------------------+---------------------------------+
|``self.device.install_executable(file)``      |  ``self.target.install(file)``  |
+----------------------------------------------+---------------------------------+
|``self.device.execute(cmd, background=True)`` |  ``self.target.background(cmd)``|
+----------------------------------------------+---------------------------------+


The old ``package`` attribute has been replaced by ``package_names`` which
expects a list of strings which allows for multiple package names to be
specified if required. It is also no longer required to explicitly state the
launch-able activity, this will be automatically discovered from the apk so this
workload attribute can be removed.

