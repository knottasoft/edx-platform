from django.utils.translation import ugettext_noop
from courseware.tabs import CourseTab
from django.conf import settings


class MyCustomTab(CourseTab):
    """
    The representation of the course teams view type.
    """
    type = "new_tab_type"
    name = "new_tab_name"
    title = ugettext_noop("My tab's name for LMS")
    view_name = "django_logic_view"
    is_default = True
    tab_id = "my_tab_id"
    is_hideable = True

    @classmethod
    def is_enabled(cls, course, user=None):
        return settings.FEATURES.get('IS_MY_CUSTOM_TAB_ENABLED', False)