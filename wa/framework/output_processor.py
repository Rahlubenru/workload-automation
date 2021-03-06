import logging

from wa.framework import pluginloader
from wa.framework.exception import ConfigError
from wa.framework.instrument import is_installed
from wa.framework.plugin import Plugin
from wa.utils.log import log_error, indent, dedent
from wa.utils.misc import isiterable
from wa.utils.types import identifier


class OutputProcessor(Plugin):

    kind = 'output_processor'
    requires = []

    def __init__(self, **kwargs):
        super(OutputProcessor, self).__init__(**kwargs)
        self.is_enabled = True

    def validate(self):
        super(OutputProcessor, self).validate()
        for instrument in self.requires:
            if not is_installed(instrument):
                msg = 'Instrument "{}" is required by {}, but is not installed.'
                raise ConfigError(msg.format(instrument, self.name))

    def initialize(self):
        pass

    def finalize(self):
        pass


class ProcessorManager(object):

    def __init__(self, loader=pluginloader):
        self.loader = loader
        self.logger = logging.getLogger('processor')
        self.processors = []

    def install(self, processor, context):
        if not isinstance(processor, OutputProcessor):
            processor = self.loader.get_output_processor(processor)
        self.logger.debug('Installing {}'.format(processor.name))
        processor.logger.context = context
        self.processors.append(processor)

    def disable_all(self):
        for output_processor in self.processors:
            self._disable_output_processor(output_processor)

    def enable_all(self):
        for output_processor in self.processors:
            self._enable_output_processor(output_processor)

    def enable(self, to_enable):
        if isiterable(to_enable):
            for inst in to_enable:
                self._enable_output_processor(inst)
        else:
            self._enable_output_processor(to_enable)

    def disable(self, to_disable):
        if isiterable(to_disable):
            for inst in to_disable:
                self._disable_output_processor(inst)
        else:
            self._disable_output_processor(to_disable)

    def get_output_processor(self, processor):
        if isinstance(processor, OutputProcessor):
            return processor

        processor = identifier(processor)
        for p in self.processors:
            if processor == p.name:
                return p
        raise ValueError('Output processor {} is not installed'.format(processor))

    def get_enabled(self):
        return [p for p in self.processors if p.is_enabled]

    def get_disabled(self):
        return [p for p in self.processors if not p.is_enabled]

    def validate(self):
        for proc in self.processors:
            proc.validate()

    def initialize(self):
        for proc in self.processors:
            proc.initialize()

    def finalize(self):
        for proc in self.processors:
            proc.finalize()

    def process_job_output(self, context):
        self.do_for_each_proc('process_job_output', 'processing using "{}"',
                              context.job_output, context.target_info,
                              context.run_output)

    def export_job_output(self, context):
        self.do_for_each_proc('export_job_output', 'Exporting using "{}"',
                              context.job_output, context.target_info,
                              context.run_output)

    def process_run_output(self, context):
        self.do_for_each_proc('process_run_output', 'Processing using "{}"',
                              context.run_output, context.target_info)

    def export_run_output(self, context):
        self.do_for_each_proc('export_run_output', 'Exporting using "{}"',
                              context.run_output, context.target_info)

    def do_for_each_proc(self, method_name, message, *args):
        try:
            indent()
            for proc in self.processors:
                if proc.is_enabled:
                    proc_func = getattr(proc, method_name, None)
                    if proc_func is None:
                        continue
                    try:
                        self.logger.info(message.format(proc.name))
                        proc_func(*args)
                    except Exception as e:
                        if isinstance(e, KeyboardInterrupt):
                            raise
                        log_error(e, self.logger)
        finally:
            dedent()

    def _enable_output_processor(self, inst):
        inst = self.get_output_processor(inst)
        self.logger.debug('Enabling output processor {}'.format(inst.name))
        if not inst.is_enabled:
            inst.is_enabled = True

    def _disable_output_processor(self, inst):
        inst = self.get_output_processor(inst)
        self.logger.debug('Disabling output processor {}'.format(inst.name))
        if inst.is_enabled:
            inst.is_enabled = False

