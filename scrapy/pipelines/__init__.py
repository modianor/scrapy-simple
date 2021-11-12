"""
Item pipeline

See documentation in docs/item-pipeline.rst
"""

from scrapy.middleware import MiddlewareManager
from scrapy.utils.conf import build_component_list


class ItemPipelineManager(MiddlewareManager):
    component_name = 'item pipeline'

    @classmethod
    def _get_mwlist_from_settings(cls, settings):
        return build_component_list(settings.getwithbase('ITEM_PIPELINES'))

    def _add_middleware(self, pipe):
        super(ItemPipelineManager, self)._add_middleware(pipe)
        if hasattr(pipe, 'process_item'):
            self.methods['process_item'].append(pipe.process_item)
        if hasattr(pipe, 'process_task'):
            self.methods['process_task'].append(pipe.process_task)

    def process_item(self, item, spider):
        return self._process_chain('process_item', item, spider)

    def process_task(self, task, spider):
        return self._process_chain('process_task', task, spider)


class TaskPipelineManager(MiddlewareManager):
    component_name = 'task pipeline'

    @classmethod
    def _get_mwlist_from_settings(cls, settings):
        return ['scrapy.pipelines.tasks.TaskPipeline']

    def _add_middleware(self, pipe):
        super(TaskPipelineManager, self)._add_middleware(pipe)
        if hasattr(pipe, 'process_task'):
            self.methods['process_task'].append(pipe.process_task)

    def process_task(self, task, spider):
        return self._process_chain('process_task', task, spider)
