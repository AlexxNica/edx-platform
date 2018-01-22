from collections import deque

from django.core.management.base import BaseCommand, CommandError

from opaque_keys.edx.keys import CourseKey
from xmodule.modulestore.django import modulestore
from lms.djangoapps.course_api.blocks.api import get_blocks
from openedx.core.lib.celery.task_utils import emulate_http_request
from openedx.core.djangoapps.site_configuration.tests.factories import SiteFactory
from student.tests.factories import UserFactory

class CompletionTraverser:

    def __init__(self, name_of_root_block, course_blocks):
        self._root_name = name_of_root_block
        self._course_blocks = course_blocks
        self._visited_blocks = {}


    def traverse(self):
        self._compute_course_completion(self._root_name, self._course_blocks)


    def _compute_course_completion(self, name_of_root_block, course_blocks):
        # print "Number of course_blocks: %d" % (len(course_blocks)) 
        course_completion = self._compute_completion_at_block(name_of_root_block)

        # print "Number of completed blocks: %f" % (course_completion)


    def _compute_completion_at_block(self, current_block_name):
        if self._block_is_visited(current_block_name):
            return

        self._mark_block_as_visited(current_block_name)

        current_block = self._get_block(current_block_name)
        names_of_children = current_block.get('children', None)
        completion_at_current_block = 0.0

        if names_of_children:
            completion_at_current_block += self._compute_childrens_completion(
                names_of_children
            )
        else:
            completion_at_current_block = current_block.get('completion', 0.0)

        return completion_at_current_block


    def _compute_childrens_completion(self, names_of_children):
        completion_of_children = 0.0
        for name_of_child in names_of_children:
                childs_completion = self._compute_completion_at_block(
                    name_of_child 
                )
                completion_of_children += childs_completion

        return completion_of_children


    def _get_block(self, name_of_block):
        return self._course_blocks[name_of_block]


    def _mark_block_as_visited(self, a_block_name):
        self._visited_blocks[a_block_name] = True


    def _block_is_visited(self, a_block_name):
        return self._visited_blocks.get(a_block_name, False)


class Command(BaseCommand):

    def handle(self, *args, **options):
        # Course has same contents as MIT's 6.001x:
        # https://www.edx.org/course/introduction-computer-science-mitx-6-00-1x-11
        course_name = 'course-v1:wert+qw4tqw4t+qertqert'
        course_usage_key = self._create_course_usage_key(course_name)

        user = UserFactory.create(
            username="staff",
            email="staff@example.com"
            )
        site = SiteFactory.create()


        with emulate_http_request(site, user) as request:
            import cProfile

            api_raw_course_data = get_blocks(
                request, 
                course_usage_key,
                user=user,
                requested_fields=['completion', 'children']
            )
            name_of_course_root = api_raw_course_data['root']
            course_blocks = api_raw_course_data['blocks']

            traverser = CompletionTraverser(name_of_course_root, course_blocks)

            # print "== get_blocks =="
            # cProfile.runctx(
            #     'get_blocks(request, course_usage_key, user=user, requested_fields=[\'completion\', \'children\'])', 
            #     globals(),
            #     locals()
            # )

            # print "== Calculate Completion DFS =="
            # cProfile.runctx('traverser.traverse()', globals(), locals())
            traverser.traverse()


    def _create_course_usage_key(self, course_name):
        course_key = CourseKey.from_string(course_name)
        return modulestore().make_course_usage_key(course_key)


    def _bfsTraverseBlocks(self, course_blocks):
        root_name = course_blocks['root']
        course_nodes = course_blocks['blocks']

        traversal_queue = deque()
        traversal_queue.appendleft(course_nodes[root_name])

        current_block = None
        while len(traversal_queue) > 0:
            current_block = traversal_queue.pop()
            current_block_completion = current_block.get('completion', None)

            for child_name in current_block.get('children', []):
                traversal_queue.appendleft(course_nodes[child_name])
