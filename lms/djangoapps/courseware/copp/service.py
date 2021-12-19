#from api import Api
import logging

from lms.djangoapps.courseware.copp.api import Api
from .discovery import DiscoveryApiClient
log = logging.getLogger("CoppService")

class CoppService():

    def getDocTypes(self):
        api = Api()
        response = api.get("docTypes")
        log.info('getDocTypes')
        log.info(response)
        return response

    def getCourseDocTypes(self, course_key):
        api = Api()
        parameters = [('course_run_key', course_key)]

        response = api.get("courseRunDocTypes", parameters)

        if len(response) > 0:
            course_doc_types = response[0]['doc_types']
            course_docs_list = course_doc_types.split(";")
            log.info('getCourseDocTypes: {}'.format(' '.join(course_docs_list)))
            return course_docs_list

        log.info('getCourseDocTypes noData')
        return []

    def getStudentDocumentTypes(self, student_id):

        if student_id==None:
            return []

        api = Api()
        parameters = [('sid', student_id)]
        student_docs = api.get('docs', parameters)

        result = []
        for sdt in student_docs:
            if sdt['status'] == 'v':
                result.append(sdt['description'])

        log.info('getStudentDocumentTypes: student_id => {}'.format(student_id))
        log.info('getStudentDocumentTypes: {}'.format(' '.join(result)))

        return result

    def getRequiredDocTypes(self, course_doc_types, student_doc_types, doc_types):

        if len(course_doc_types) > 0:
            rdt = [ crdt for crdt in course_doc_types if crdt not in student_doc_types]
            dt = [ docType for docType in doc_types if docType['value'] in rdt ]
            return dt

        return []

    def getExistDocTypes(self, course_doc_types, student_doc_types, doc_types):

        if len(course_doc_types) > 0:
            rdt = [ crdt for crdt in course_doc_types if crdt in student_doc_types]
            dt = [ docType for docType in doc_types if docType['value'] in rdt ]
            return dt

        return []

    def getCourseRunDetails(self, course_key):
        discovery_api = DiscoveryApiClient()
        
        result = discovery_api.get_course_run_detail(course_key)
        return result
