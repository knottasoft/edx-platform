from api import Api
a = Api()
#response = a.get("docTypes")
#response = a._getRefreshToken()
#print(response)

doc_types = a.get("docTypes")

p = [('course_run_key','course-v1:edX+12332+3T2021')]
r = a.get("courseRunDocTypes", p)
course_docs = r[0]['doc_types']
course_docs_list = course_docs.split(";")


p2 = [('sid', '777')]
student_docs = a.get('docs', p2)
sdts = []
for sdt in student_docs:
    sdts.append(sdt['description'])

print(sdts)


#print(doc_types)
print(course_docs_list)

rdt = [ crdt for crdt in course_docs_list if crdt not in sdts]
print(rdt)

dt = [ docType for docType in doc_types if docType['value'] in rdt ]

print(dt)