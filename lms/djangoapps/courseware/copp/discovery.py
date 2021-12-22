"""
Discovery service api client code.
"""
import logging

from django.conf import settings
from .base_oauth import BaseOAuthClient


LOGGER = logging.getLogger(__name__)
DISCOVERY_COURSES_ENDPOINT = settings.DISCOVERY_COURSES_ENDPOINT

class DiscoveryApiClient(BaseOAuthClient):
    """
    Object builds an API client to make calls to the Discovery Service.
    """

    def _retrieve_course_run_detail(self, course_run_key):

        LOGGER.info('Retrieving course run detail from course-discovery for')
        response = self.client.get(
            f"{DISCOVERY_COURSES_ENDPOINT}/courses/{course_run_key}/",
            #f"{DISCOVERY_COURSES_ENDPOINT}/course_runs/course-v1:edX+DemoX+Demo_Course/",
        ).json()
        return response

    def get_course_run_detail(self, course_run_key):
        try:
            response = self._retrieve_course_run_detail(course_run_key)
            LOGGER.info('get_course_run_detail %s', course_run_key)
            return response

        except Exception as exc:  # pylint: disable=broad-except
            LOGGER.error(
                'Could not get course-run details from course-discovery with course_run_key %s: %s ',
                course_run_key,
                exc,
            )
