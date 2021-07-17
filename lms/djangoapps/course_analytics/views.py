from django.shortcuts import render_to_response
from opaque_keys.edx.keys import CourseKey
from courseware.courses import get_course_with_access


def my_custom_function(request, course_id):
    course_key = CourseKey.from_string(course_id)
    course = get_course_with_access(request.user, "load", course_key)

    context = {
        "course": course,
    }
    return render_to_response("course_analytics/course_analytics_tab.html", context)