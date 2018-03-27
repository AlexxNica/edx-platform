"""
Command to migrate transcripts to S3.
"""

import logging

from django.core.management import BaseCommand, CommandError

from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locator import CourseLocator

from cms.djangoapps.contentstore.tasks import (
    DEFAULT_ALL_COURSES,
    DEFAULT_FORCE_UPDATE,
    DEFAULT_COMMIT,
    enqueue_async_migrate_transcripts_tasks
)

log = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Example usage:
        $ ./manage.py cms migrate_transcripts --all-courses --force-update --commit
        $ ./manage.py cms migrate_transcripts --course-id 'Course1' -course-id 'Course2' --commit
    """
    args = '<course_id course_id ...>'
    help = 'Migrates transcripts to S3 for one or more courses.'

    def add_arguments(self, parser):
        """
        Add arguments to the command parser.
        """
        parser.add_argument(
            '--course-id',
            dest='course_id',
            action='append'
        )
        parser.add_argument(
            '--all-courses', '--all',
            dest='all_courses',
            action='store_true',
            default=DEFAULT_ALL_COURSES,
            help=u'Migrates transcripts to S3 for all courses.'
        )
        parser.add_argument(
            '--force-update', '--force_update',
            dest='force_update',
            action='store_true',
            default=DEFAULT_FORCE_UPDATE,
            help=u'Force migrate transcripts for the requested courses, overwrite if already present.'
        )
        parser.add_argument(
            '--commit',
            dest='commit',
            action='store_true',
            default=DEFAULT_COMMIT,
            help=u'Commits the discovered video transcripts to S3. '
                 u'Without this flag, the command will return the transcripts discovered for migration '
        )

    def _parse_course_key(self, raw_value):
        """ Parses course key from string """
        try:
            result = CourseKey.from_string(raw_value)
        except InvalidKeyError:
            raise CommandError("Invalid course_key: '%s'." % raw_value)

        if not isinstance(result, CourseLocator):
            raise CommandError(u"Argument {0} is not a course key".format(raw_value))

        return result

    def handle(self, *args, **options):
        """
        Invokes the migrate transcripts enqueue function.
        """
        course_ids = options['course_id']
        all_option = options['all_courses']
        if course_ids is None:
            course_ids = []

        if (not len(course_ids) and not all_option) or (len(course_ids) and all_option):
            raise CommandError("At least one course or --all-courses must be specified.")

        kwargs = {key: options[key] for key in ['all_courses', 'force_update', 'commit'] if options.get(key)}
        course_keys = map(self._parse_course_key, course_ids)

        try:
            enqueue_async_migrate_transcripts_tasks(
                course_keys,
                **kwargs
            )
        except InvalidKeyError as exc:
            raise CommandError(u'Invalid course key: ' + unicode(exc))
