#from api import Api
import logging

from lms.djangoapps.courseware.copp.api import Api
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
            result.append(sdt['description'])
        
        log.info('getStudentDocumentTypes: student_id => {}'.format(student_id))
        log.info('getStudentDocumentTypes: {}'.format(' '.join(result)))

        return result

    def getRequiredDocTypes(self, course_key, student_id):
        course_doc_types = self.getCourseDocTypes(course_key)
        
        if len(course_doc_types) > 0:
            sdts = self.getStudentDocumentTypes(student_id)
            rdt = [ crdt for crdt in course_doc_types if crdt not in sdts]
            doc_types = self.getDocTypes()
            dt = [ docType for docType in doc_types if docType['value'] in rdt ]
            return dt
        
        return []