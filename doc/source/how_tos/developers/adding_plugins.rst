.. _adding-a-workload:

Adding a Workload Examples
==========================

The easiest way to create a new workload is to use the create command. ``wa
create workload <args>``.  This will use predefined templates to create a
workload based on the options that are supplied to be used as a starting point
for the workload. For more information on using the create workload command see
``wa create workload -h``

The first thing to decide is the type of workload you want to create depending
on the OS you will be using and the aim of the workload. The are currently 6
available workload types to choose as detailed :ref:`here<workload-types>`.

Once you have decided what type of workload you wish to choose this can be
specified with ``-k <workload_kind>`` followed by the workload name. This
will automatically generate a workload in the your ``WA_CONFIG_DIR/plugins``. If
you wish to specify a custom location this can be provided with ``-p
<directory>``

Adding a Basic Workload Example
--------------------------------

To add a basic workload you can simply use the command::

        wa create workload basic

This will generate a very basic workload with dummy methods for the workload
interface and it is left to the developer to add any required functionality to
the workload.

This example shows a simple workload that times how long it takes to compress a
file of a particular size on the device, not all the methods are required to be
implements however as many as possible have been used to demonstrate their
purpose.

.. note:: This is intended as an example of how to implement the Workload
          :ref: `interface <workload-interface>`. The methodology used to
          perform the actual measurement is not necessarily sound, and this
          Workload should not be used to collect real measurements.

.. code-block:: python

    import os
    from wa import Workload, Parameter

    class ZipTestWorkload(Workload):

        name = 'ziptest'
        description = '''
                      Times how long it takes to gzip a file of a particular size on a device.

                      This workload was created for illustration purposes only. It should not be
                      used to collect actual measurements.

                      '''

        parameters = [
                Parameter('file_size', kind=int, default=2000000,
                          description='Size of the file (in bytes) to be gzipped.')
        ]

        def setup(self, context):
            """
            In the setup method we do any preparation that is required before
            the workload is ran, this is usually things like setting up required
            files on the device and generating commands from user input. In this
            case we will generate our input file on the host system and then
            push it to a known location on the target for use in the 'run'
            stage.
            """
            super(ZipTestWorkload, self).setup(context)
            # Generate a file of the specified size containing random garbage.
            host_infile = os.path.join(context.output_directory, 'infile')
            command = 'openssl rand -base64 {} > {}'.format(self.file_size, host_infile)
            os.system(command)
            # Set up on-device paths
            devpath = self.target.path  # os.path equivalent for the target
            self.target_infile = devpath.join(self.target.working_directory, 'infile')
            self.target_outfile = devpath.join(self.target.working_directory, 'outfile')
            # Push the file to the target
            self.target.push(host_infile, self.target_infile)

        def run(self, context):
            """
            The run method is where the actual 'work' of the workload takes
            place and is what is measured by any instrumentation. So for this
            example this is the execution of creating the zip file on the
            target.
            """
            cmd = 'cd {} && (time gzip {}) &>> {}'
            self.target.execute(cmd.format(self.target.working_directory,
                                           self.target_infile,
                                           self.target_outfile))
        def extract_results(self, context):
            """
            This method is used to extract any results from the target for
            example we want to pull the file containing the timing information
            that we will use to generate metrics for our workload and then we
            add this file as a artifact as a 'raw' file which once WA has
            finished processing it will allow it to decide whether to keep the
            file or not.
            """
            super(ZipTestWorkload, self).extract_results(context)
            # Pull the results file to the host
            self.host_outfile = os.path.join(context.output_directory, 'timing_results')
            self.target.pull(self.target_outfile, self.host_outfile)
            context.add_artifact('ziptest-results', host_output_file, kind='raw')

        def update_output(self, context):
            """
            In this method we can do any generation of metric that we wish to
            for our workload. In this case we are going to simply convert the
            times reported to seconds and add them as 'metrics' to WA which can
            then be displayed to the user along with any others in a format
            dependant on which output processors they have enabled for the run.
            """
            super(ZipTestWorkload, self).update_output(context)
            # Extract metrics form the file's contents and update the result
            # with them.
            content = iter(open(self.host_outfile).read().strip().split())
            for value, metric in zip(content, content):
                mins, secs = map(float, value[:-1].split('m'))
                context.add_metric(metric, secs + 60 * mins, 'seconds')

        def teardown(self, context):
            """
            Here we will perform any required clean up for the workload so we
            will delete the input and output files from the device.
            """
            super(ZipTestWorkload, self).teardown(context)
            self.target.remove(self.target_infile)
            self.target.remove(self.target_outfile)


.. _apkuiautomator-example:

Adding a ApkUiAutomator Workload Example
-----------------------------------------

If we wish to create a workload to automate the testing of the Google Docs
android app, we would choose to perform the automation using UIAutomator and we
would want to automatically deploy and install the apk file to the target,
therefore we would choose the :ref:`ApkUiAutomator workload
<apkuiautomator-workload>` type with the following command::

    $ wa create workload -k apkuiauto google_docs
    Workload created in $WA_USER_DIRECTORY/plugins/google_docs


From here you can navigate to the displayed folder and you will find your
``__init__.py``  and a ``uiauto`` directory. The former is your python WA
workload and will look something like this::

        from wa import Parameter, ApkUiautoWorkload
        class GoogleDocs(ApkUiautoWorkload):
            name = 'google_docs'
            description = "This is an placeholder description"
            # Replace with a list of supported package names in the APK file(s).
            package_names = ['package_name']

            parameters = [
             # Workload parameters go here e.g.
             Parameter('example_parameter', kind=int, allowed_values=[1,2,3],
                       default=1, override=True, mandatory=False,
                       description='This is an example parameter')
            ]

            def __init__(self, target, **kwargs):
             super(GoogleDocs, self).__init__(target, **kwargs)
             # Define any additional attributes required for the workload

            def init_resources(self, context):
             super(GoogleDocs, self).init_resources(context)
             # This method may be used to perform early resource discovery and
             # initialization. This is invoked during the initial loading stage and
             # before the device is ready, so cannot be used for any device-dependent
             # initialization. This method is invoked before the workload instance is
             # validated.

            def initialize(self, context):
             super(GoogleDocs, self).initialize(context)
             # This method should be used to perform once-per-run initialization of a
             # workload instance.

            def validate(self):
             super(GoogleDocs, self).validate()
             # Validate inter-parameter assumptions etc

            def setup(self, context):
             super(GoogleDocs, self).setup(context)
             # Perform any necessary setup before starting the UI automation

            def extract_results(self, context):
             super(GoogleDocs, self).extract_results(context)
             # Extract results on the target

            def update_output(self, context):
             super(GoogleDocs, self).update_output(context)
             # Update the output within the specified execution context with the
             # metrics and artifacts form this workload iteration.

            def teardown(self, context):
             super(GoogleDocs, self).teardown(context)
             # Perform any final clean up for the Workload.


Depending on the purpose of your workload you can choose to implement which
methods you require. The main things that need setting are the list of
``package_names`` which must be a list of strings containing the android package
name that will be used during resource resolution to locate the relevant apk
file for the workload. Additionally the the workload parameters will need to
updating to any relevant parameters required by the workload as well as the
description.


The latter will contain a framework for performing the UI automation on the
target, the files you will be most interested in will be
``uiauto/app/src/main/java/arm/wa/uiauto/UiAutomation.java`` which will contain
the actual code of the automation and will look something like::

        package com.arm.wa.uiauto.google_docs;

        import android.app.Activity;
        import android.os.Bundle;
        import org.junit.Test;
        import org.junit.runner.RunWith;
        import android.support.test.runner.AndroidJUnit4;

        import android.util.Log;
        import android.view.KeyEvent;

        // Import the uiautomator libraries
        import android.support.test.uiautomator.UiObject;
        import android.support.test.uiautomator.UiObjectNotFoundException;
        import android.support.test.uiautomator.UiScrollable;
        import android.support.test.uiautomator.UiSelector;

        import org.junit.Before;
        import org.junit.Test;
        import org.junit.runner.RunWith;

        import com.arm.wa.uiauto.BaseUiAutomation;

        @RunWith(AndroidJUnit4.class)
        public class UiAutomation extends BaseUiAutomation {

            protected Bundle parameters;

            public static String TAG = "google_docs";

            @Before
            public void initilize() throws Exception {
                parameters = getParams();
                // Perform any parameter initialization here
            }

            @Test
            public void setup() throws Exception {
                // Optional: Perform any setup required before the main workload
                // is ran, e.g. dismissing welcome screens
            }

            @Test
            public void runWorkload() throws Exception {
                   // The main UI Automation code goes here
            }

            @Test
            public void extractResults() throws Exception {
                // Optional: Extract any relevant results from the workload,
            }

            @Test
            public void teardown() throws Exception {
                // Optional: Perform any clean up for the workload
            }
        }

Once you have implemented your java workload you can use the file
``uiauto/build.sh`` to compile your automation into an apk file to perform the
automation. The generated apk will be generated with the package name
``com.arm.wa.uiauto.<workload_name>`` which when running your workload will be
automatically detected by the resource getters and deployed to the device.


Adding a ReventApk Workload Example
------------------------------------

If we wish to create a workload to automate the testing of a UI based workload
that we cannot / do not wish to use UiAutomator then we can perform the
automation using revent. In this example we would want to automatically deploy
and install an apk file to the target, therefore we would choose the
:ref:`ApkRevent workload <apkrevent-workload>` type with the following
command::

    $ wa create workload -k apkrevent my_game
    Workload created in $WA_USER_DIRECTORY/plugins/my_game

This will generate a revent based workload you will end up with a very similar
python file as to the one outlined in generating a :ref:`UiAutomator based
workload <apkuiautomator-example>` except without the java automation files.

The main difference between the two is that this workload will subclass
``ApkReventWorkload`` instead of ``ApkUiautomatorWorkload`` as shown below.

.. code-block:: python

    from wa import ApkReventWorkload

    class MyGame(ApkReventWorkload):

        name = 'mygame'
        package_names = ['com.mylogo.mygame']

        # ..


---------------------------------------------------------------

.. _adding-an-instrument-example:

Adding an Instrument Example
=============================
This is an example of how we would create a instrument which will trace device
errors. For more detailed information please see :ref:`here <instrument-reference>`.
The first thing to do is to subclass :class:`Instrument`, overwrite
the variable name with what we want our instrument to be called and locate our
binary for our instrument. ::

        class TraceErrorsInstrument(Instrument):

            name = 'trace-errors'

            def __init__(self, target):
                super(TraceErrorsInstrument, self).__init__(target)
                self.binary_name = 'trace'
                self.binary_file = os.path.join(os.path.dirname(__file__), self.binary_name)
                self.trace_on_target = None

We then declare and implement the required methods as detailed
:ref:`here <instrument-api>`. For the ``initialize`` method, we want to install
    the executable file to the target so we can use the target's ``install``
    method which will try to copy the file to a location on the device that
    supports execution, will change the file mode appropriately and return the
    file path on the target. ::

    def initialize(self, context):
        self.trace_on_target = self.target.install(self.binary_file)

Then we implemented the start method, which will simply run the file to start
tracing. Supposing that the call to this binary requires some overhead to begin
collecting errors we might want to decorate the method with the ``@slow``
decorator to try and reduce the impact on other running instruments. For more
information on prioritization please see :ref:`here <prioritization>`::

    @slow
    def start(self, context):
        self.target.execute('{} start'.format(self.trace_on_target))

Lastly, we need to stop tracing once the workload stops and this happens in the
stop method, assuming stopping the collection also require some overhead we have
again decorated the method::

    @slow
    def stop(self, context):
        self.target.execute('{} stop'.format(self.trace_on_target))

Once we have generated our result data we need to retrieve it from the device
for further processing or adding directly to WA's output for that job. For
example for trace data we will want to pull it to the device and add it as a
:ref:`artifact <atrifact>` to WA's :ref:`context <context>` as shown below::

    def extract_results(self, context):
        # pull the trace file from the target
        self.result = os.path.join(self.target.working_directory, 'trace.txt')
        self.target.pull(self.result, context.working_directory)
        context.add_artifact('error_trace', self.result, kind='export')

Once we have retrieved the data we can now do any further processing and add any
relevant :ref:`Metrics <metrics>` to the :ref:`context <context>`. For this we
will use the the ``add_metric`` method and to add the instruments results to the
final result for that workload. The method can be passed 4 params, which are the
metric `key`, `value`, `unit` and `lower_is_better`. ::

    def update_output(self, context):
        # parse the file if needs to be parsed, or add result directly to
        # context.

        metric = # ..
        context.add_metric('number_of_errors', metric, lower_is_better=True

At the end of each job we might want to delete any files generated by the
instruments and the code to clear these file goes in teardown method. ::

    def teardown(self, context):
        self.target.remove(os.path.join(self.target.working_directory, 'trace.txt'))

At the very end of the run we would want to uninstall the binary we deployed earlier ::

    def finalize(self, context):
        self.target.uninstall(self.binary_name)

So the full example would look something like::

        class TraceErrorsInstrument(Instrument):

            name = 'trace-errors'

            def __init__(self, target):
                super(TraceErrorsInstrument, self).__init__(target)
                self.binary_name = 'trace'
                self.binary_file = os.path.join(os.path.dirname(__file__), self.binary_name)
                self.trace_on_target = None

            def initialize(self, context):
                self.trace_on_target = self.target.install(self.binary_file)

            @slow
            def start(self, context):
                self.target.execute('{} start'.format(self.trace_on_target))

            @slow
            def stop(self, context):
                self.target.execute('{} stop'.format(self.trace_on_target))

            def extract_results(self, context):
                self.result = os.path.join(self.target.working_directory, 'trace.txt')
                self.target.pull(self.result, context.working_directory)
                context.add_artifact('error_trace', self.result, kind='export')

            def update_output(self, context):
                metric = # ..
                context.add_metric('number_of_errors', metric, lower_is_better=True

            def teardown(self, context):
                self.target.remove(os.path.join(self.target.working_directory, 'trace.txt'))

            def finalize(self, context):
                self.target.uninstall(self.binary_name)


Adding an Output Processor Example
===================================

This is an example of how we would create an output processor which will format
the run metrics  as a column-aligned table. The first thing to do is to subclass
:class:`OutputProcessor` and overwrite the variable name with what we want our
processor to be called and provide a short description.

Next we need to implement any relevant methods, (please see
:ref:`adding an output processor <adding-an-output-processor>` for all the
available methods). In this case we only want to implement the
``export_run_output`` method as we are not generating any new artifacts and
we only care about the overall output rather than the individual job
outputs. And the implementation is very simple, it just loops through all
the available metrics for all the available jobs and adds them to a list
which is written to file and then added as an :ref:`artifact <artifact>` to
the :ref:`context <context>`.

.. code-block:: python

    import os
    from wa import OutputProcessor
    from wa.utils.misc import write_table


    class Table(OutputProcessor):

        name = 'table'
        description = 'Generates a text file containing a column-aligned table with run results.'

        def export_run_output(self, output, target_info):
            rows = []

            for job in output.jobs:
                for metric in job.metrics:
                    rows.append([metric.name, str(metric.value), metric.units or '',
                                 metric.lower_is_better  and '-' or '+'])

            outfile =  output.get_path('table.txt')
            with open(outfile, 'w') as wfh:
                write_table(rows, wfh)
            output.add_artifact('results_table', 'table.txt, 'export')


.. _adding-custom-target-example:
Adding a Custom Target Example
===============================
This is an example of how we would create a customised target, this is typically
used where we would need to augment the existing functionality for example on
development boards where we need to perform additional actions to implement some
functionality. In this example we are going to assume that this particular
device is running Android and requires a special "wakeup" command to be sent before it
can execute any other command.

To add a new target to WA we will first create a new file in
``$WA_USER_DIRECTORY/plugins/example_target.py``. In order to facilitate with
creating a new target WA provides a helper function to create a description for
the specified target class, and specified components. For components that are
not explicitly specified it will attempt to guess sensible defaults based on the target
class' bases.

.. code-block:: python

        # Import our helper function
        from wa import add_description_for_target

        # Import the Target that our custom implementation will be based on
        from devlib import AndroidTarget

        class ExampleTarget(AndroidTarget):
            # Provide the name that will be used to identify your custom target
            name = 'example_target'

            # Override our custom method(s)
            def execute(self, *args, **kwargs):
                super(ExampleTarget, self).execute('wakeup', check_exit_code=False)
                return super(ExampleTarget, self).execute(*args, **kwargs)


        description = '''An Android target which requires an explicit "wakeup" command
                          to be sent before accepting any other command'''
        # Call the helper function with our newly created function and its description.
        add_description_for_target(ExampleTarget, description)

