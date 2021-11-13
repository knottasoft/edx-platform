from service import CoppService

service = CoppService()
requiredDocTypes = service.getRequiredDocTypes('course-v1:edX+12332+3T2021','777')
print(requiredDocTypes)