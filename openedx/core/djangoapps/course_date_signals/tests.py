# lint-amnesty, pylint: disable=missing-module-docstring
from datetime import timedelta
import ddt
from unittest.mock import patch  # lint-amnesty, pylint: disable=wrong-import-order

from cms.djangoapps.contentstore.config.waffle import CUSTOM_PLS
from edx_toggles.toggles.testutils import override_waffle_flag
from openedx.core.djangoapps.course_date_signals.handlers import _gather_graded_items, _get_custom_pacing_children, _has_assignment_blocks, extract_dates_from_course
from openedx.core.djangoapps.course_date_signals.models import SelfPacedRelativeDatesConfig
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase, SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from . import utils


@ddt.ddt
class SelfPacedDueDatesTests(ModuleStoreTestCase):  # lint-amnesty, pylint: disable=missing-class-docstring
    def setUp(self):
        super().setUp()
        self.course = CourseFactory.create()
        for i in range(4):
            ItemFactory(parent=self.course, category="sequential", display_name=f"Section {i}")

    def test_basic_spacing(self):
        expected_sections = [
            (0, 'Section 0', timedelta(days=7)),
            (1, 'Section 1', timedelta(days=14)),
            (2, 'Section 2', timedelta(days=21)),
            (3, 'Section 3', timedelta(days=28)),
        ]
        with patch.object(utils, 'get_expected_duration', return_value=timedelta(weeks=4)):
            actual = [(idx, section.display_name, offset) for (idx, section, offset) in utils.spaced_out_sections(self.course)]  # lint-amnesty, pylint: disable=line-too-long

        assert actual == expected_sections

    def test_hidden_sections(self):
        for _ in range(2):
            ItemFactory(parent=self.course, category="sequential", visible_to_staff_only=True)
        expected_sections = [
            (0, 'Section 0', timedelta(days=7)),
            (1, 'Section 1', timedelta(days=14)),
            (2, 'Section 2', timedelta(days=21)),
            (3, 'Section 3', timedelta(days=28)),
        ]
        with patch.object(utils, 'get_expected_duration', return_value=timedelta(weeks=4)):
            actual = [(idx, section.display_name, offset) for (idx, section, offset) in utils.spaced_out_sections(self.course)]  # lint-amnesty, pylint: disable=line-too-long

        assert actual == expected_sections

    def test_dates_for_ungraded_assignments(self):
        """
        _has_assignment_blocks should return true if the argument block
        children leaf nodes include an assignment that is graded and scored
        """
        with modulestore().bulk_operations(self.course.id):
            sequence = ItemFactory(parent=self.course, category="sequential")
            vertical = ItemFactory(parent=sequence, category="vertical")
            sequence = modulestore().get_item(sequence.location)
            assert _has_assignment_blocks(sequence) is False

            # Ungraded problems do not count as assignment blocks
            ItemFactory.create(
                parent=vertical,
                category='problem',
                graded=True,
                weight=0,
            )
            sequence = modulestore().get_item(sequence.location)
            assert _has_assignment_blocks(sequence) is False
            ItemFactory.create(
                parent=vertical,
                category='problem',
                graded=False,
                weight=1,
            )
            sequence = modulestore().get_item(sequence.location)
            assert _has_assignment_blocks(sequence) is False

            # Method will return true after adding a graded, scored assignment block
            ItemFactory.create(
                parent=vertical,
                category='problem',
                graded=True,
                weight=1,
            )
            sequence = modulestore().get_item(sequence.location)
            assert _has_assignment_blocks(sequence) is True

    def test_sequence_with_graded_and_ungraded_assignments(self):
        """
        _gather_graded_items should set a due date of None on ungraded problem blocks
        even if the block has graded siblings in the sequence
        """
        with modulestore().bulk_operations(self.course.id):
            sequence = ItemFactory(parent=self.course, category="sequential")
            vertical = ItemFactory(parent=sequence, category="vertical")
            ItemFactory.create(
                parent=vertical,
                category='problem',
                graded=False,
                weight=1,
            )
            ungraded_problem_2 = ItemFactory.create(
                parent=vertical,
                category='problem',
                graded=True,
                weight=0,
            )
            graded_problem_1 = ItemFactory.create(
                parent=vertical,
                category='problem',
                graded=True,
                weight=1,
            )
            expected_graded_items = [
                (ungraded_problem_2.location, {'due': None}),
                (graded_problem_1.location, {'due': 5}),
            ]
            self.assertCountEqual(_gather_graded_items(sequence, 5), expected_graded_items)

    def test_get_custom_pacing_children(self):
        """
        _get_custom_pacing_items should return a list of (block item location, field metadata dictionary)
        where the due dates are set from due_num_weeks
        """
        # A subsection with multiple units but no problems
        with modulestore().bulk_operations(self.course.id):
            sequence = ItemFactory(parent=self.course, category='sequential', due_num_weeks=2)
            vertical1 = ItemFactory(parent=sequence, category='vertical')
            vertical2 = ItemFactory(parent=sequence, category='vertical')
            vertical3 = ItemFactory(parent=sequence, category='vertical')
            expected_dates = [(sequence.location, {'due': timedelta(weeks=2)}),
                            (vertical1.location, {'due': timedelta(weeks=2)}),
                            (vertical2.location, {'due': timedelta(weeks=2)}),
                            (vertical3.location, {'due': timedelta(weeks=2)})]
            self.assertCountEqual(_get_custom_pacing_children(sequence, 2), expected_dates)

        # A subsection with multiple units, each of which has a problem
            problem1 = ItemFactory(parent=vertical1, category='problem')
            problem2 = ItemFactory(parent=vertical1, category='problem')
            expected_dates.extend([(problem1.location, {'due': timedelta(weeks=2)}),
                            (problem2.location, {'due': timedelta(weeks=2)})])
            sequence = modulestore().get_item(sequence.location)
            self.assertCountEqual(_get_custom_pacing_children(sequence, 2), expected_dates)

        # A subsection that has ORA as a problem
            ItemFactory.create(parent=vertical3, category='openassessment')
            sequence = modulestore().get_item(sequence.location)
            self.assertCountEqual(_get_custom_pacing_children(sequence, 2), expected_dates)

        # A subsection that has an ORA problem and a non ORA problem
            problem4 = ItemFactory(parent=vertical3, category='problem')
            expected_dates.append((problem4.location, {'due': timedelta(weeks=2)}))
            sequence = modulestore().get_item(sequence.location)
            self.assertCountEqual(_get_custom_pacing_children(sequence, 2), expected_dates)

@ddt.ddt
class SelfPacedCustomDueDateTests(SharedModuleStoreTestCase):

    def setUp(self):
        SelfPacedRelativeDatesConfig.objects.create(enabled=True)

        # setUpClassAndTestData() already calls setUpClass on SharedModuleStoreTestCase
        # pylint: disable=super-method-not-called
        with super().setUpClassAndTestData():
            self.courses = []

            # course 1: with due_num_weeks but without any units
            course1 = CourseFactory.create(self_paced=True)
            with self.store.bulk_operations(course1.id):
                chapter = ItemFactory.create(category='chapter', parent=course1)
                sequential = ItemFactory.create(category='sequential', parent=chapter, due_num_weeks=3)
            self.courses.append(course1)

            # course 2: with due_num_weeks and a unit
            course2 = CourseFactory.create(self_paced=True)
            with self.store.bulk_operations(course2.id):
                chapter = ItemFactory.create(category='chapter', parent=course2)
                sequential = ItemFactory.create(category='sequential', parent=chapter, due_num_weeks=2)
                vertical = ItemFactory.create(category='vertical', parent=sequential)
            self.courses.append(course2)

            # course 3: with due_num_weeks and a problem
            course3 = CourseFactory.create(self_paced=True)
            with self.store.bulk_operations(course3.id):
                chapter = ItemFactory.create(category='chapter', parent=course3)
                sequential = ItemFactory.create(category='sequential', parent=chapter, due_num_weeks=1)
                vertical = ItemFactory.create(category='vertical', parent=sequential)
                ItemFactory.create(category='problem', parent=vertical)
            self.courses.append(course3)

            # course 4: with due_num_weeks on all sections
            course4 = CourseFactory.create(self_paced=True)
            with self.store.bulk_operations(course4.id):
                chapter = ItemFactory.create(category='chapter', parent=course4)
                sequential1 = ItemFactory.create(category='sequential', parent=chapter, due_num_weeks=1)
                sequential2 = ItemFactory.create(category='sequential', parent=chapter, due_num_weeks=3)
                sequential3 = ItemFactory.create(category='sequential', parent=chapter, due_num_weeks=4)
            self.courses.append(course4)

            # course 5: without due_num_weeks on all sections
            course5 = CourseFactory.create(self_paced=True)
            with self.store.bulk_operations(course5.id):
                chapter = ItemFactory.create(category='chapter', parent=course5)
                sequential1 = ItemFactory.create(category='sequential', parent=chapter)
                sequential2 = ItemFactory.create(category='sequential', parent=chapter)
                sequential3 = ItemFactory.create(category='sequential', parent=chapter)
            self.courses.append(course5)

            # course 6: due_num_weeks in one of the sections
            course6 = CourseFactory.create(self_paced=True)
            with self.store.bulk_operations(course6.id):
                chapter = ItemFactory.create(category='chapter', parent=course6)
                sequential1 = ItemFactory.create(category='sequential', parent=chapter)
                sequential2 = ItemFactory.create(category='sequential', parent=chapter, due_num_weeks=1)
                sequential3 = ItemFactory.create(category='sequential', parent=chapter)
            self.courses.append(course6)

            # course 7: a unit with an ORA problem
            course7 = CourseFactory.create(self_paced=True)
            with self.store.bulk_operations(course7.id):
                chapter = ItemFactory.create(category='chapter', parent=course7)
                sequential = ItemFactory.create(category='sequential', parent=chapter, due_num_weeks=1)
                vertical = ItemFactory.create(category='vertical', parent=sequential)
                ItemFactory.create(category='openassessment', parent=vertical)
            self.courses.append(course7)

            # course 8: a unit with an ORA problem and a nonORA problem
            course8 = CourseFactory.create(self_paced=True)
            with self.store.bulk_operations(course8.id):
                chapter = ItemFactory.create(category='chapter', parent=course8)
                sequential = ItemFactory.create(category='sequential', parent=chapter, due_num_weeks=2)
                vertical = ItemFactory.create(category='vertical', parent=sequential)
                ItemFactory.create(category='openassessment', parent=vertical)
                ItemFactory.create(category='problem', parent=vertical)
            self.courses.append(course8)

            # course 9: a section with a subsection that has due_num_weeks and a section without due_num_weeks that has graded content
            course9 = CourseFactory.create(self_paced=True)
            with self.store.bulk_operations(course9.id):
                chapter1 = ItemFactory.create(category='chapter', parent=course9)
                sequential1 = ItemFactory.create(category='sequential', parent=chapter1, due_num_weeks=2)
                vertical1 = ItemFactory.create(category='vertical', parent=sequential1)
                ItemFactory.create(category='problem', parent=vertical1)

                chapter2 = ItemFactory.create(category='chapter', parent=course9)
                sequential2 = ItemFactory.create(category='sequential', parent=chapter2, graded=True)
                vertical2 = ItemFactory.create(category='vertical', parent=sequential2)
                ItemFactory.create(category='problem', parent=vertical2)
            self.courses.append(course9)

            # course 10: a section with a subsection that has due_num_weeks and multiple sections without due_num_weeks that has graded content
            course10 = CourseFactory.create(self_paced=True)
            with self.store.bulk_operations(course10.id):
                chapter1 = ItemFactory.create(category='chapter', parent=course10)
                sequential1 = ItemFactory.create(category='sequential', parent=chapter1, due_num_weeks=2)
                vertical1 = ItemFactory.create(category='vertical', parent=sequential1)
                ItemFactory.create(category='problem', parent=vertical1)

                chapter2 = ItemFactory.create(category='chapter', parent=course10)
                sequential2 = ItemFactory.create(category='sequential', parent=chapter2, graded=True)
                vertical2 = ItemFactory.create(category='vertical', parent=sequential2)
                ItemFactory.create(category='problem', parent=vertical2)

                chapter3 = ItemFactory.create(category='chapter', parent=course10)
                sequential3 = ItemFactory.create(category='sequential', parent=chapter3, graded=True)
                vertical3 = ItemFactory.create(category='vertical', parent=sequential3)
                ItemFactory.create(category='problem', parent=vertical3)

                chapter4 = ItemFactory.create(category='chapter', parent=course10)
                sequential4 = ItemFactory.create(category='sequential', parent=chapter4, graded=True)
                vertical4 = ItemFactory.create(category='vertical', parent=sequential4)
                ItemFactory.create(category='problem', parent=vertical4)
            self.courses.append(course10)


    @override_waffle_flag(CUSTOM_PLS, active=True)
    def test_extract_dates_from_course(self):
        """
        extract_dates_from_course should return a list of (block item location, field metadata dictionary)
        """

        # course 1: With due_num_weeks but without any units
        course = self.courses[0]
        chapter = course.get_children()[0]
        sequential = chapter.get_children()[0]
        expected_dates = [(course.location, {}),
                        (chapter.location, timedelta(days=28)),
                        (sequential.location, {'due': timedelta(days=21)})]
        course = modulestore().get_item(course.location)
        self.assertCountEqual(extract_dates_from_course(course), expected_dates)

        # course 2: with due_num_weeks and a unit
        course = self.courses[1]
        chapter = course.get_children()[0]
        sequential = chapter.get_children()[0]
        vertical = sequential.get_children()[0]
        expected_dates = [(course.location, {}),
                        (chapter.location, timedelta(days=28)),
                        (sequential.location, {'due': timedelta(days=14)}),
                        (vertical.location, {'due': timedelta(days=14)})]
        course = modulestore().get_item(course.location)
        self.assertCountEqual(extract_dates_from_course(course), expected_dates)

        # course 3: with due_num_weeks and a problem
        course = self.courses[2]
        chapter = course.get_children()[0]
        sequential = chapter.get_children()[0]
        vertical = sequential.get_children()[0]
        problem = vertical.get_children()[0]
        expected_dates = [(course.location, {}),
                        (chapter.location, timedelta(days=28)),
                        (sequential.location, {'due': timedelta(days=7)}),
                        (vertical.location, {'due': timedelta(days=7)}),
                        (problem.location, {'due': timedelta(days=7)})]
        course = modulestore().get_item(course.location)
        self.assertCountEqual(extract_dates_from_course(course), expected_dates)

        # course 4: with due_num_weeks on all sections
        course = self.courses[3]
        chapter = course.get_children()[0]
        sequential = chapter.get_children()
        expected_dates = [(course.location, {}),
                        (chapter.location, timedelta(days=28)),
                        (sequential[0].location, {'due': timedelta(days=7)}),
                        (sequential[1].location, {'due': timedelta(days=21)}),
                        (sequential[2].location, {'due': timedelta(days=28)})]
        course = modulestore().get_item(course.location)
        self.assertCountEqual(extract_dates_from_course(course), expected_dates)

        # course 5: without due_num_weeks on all sections
        course = self.courses[4]
        expected_dates = [(course.location, {})]
        course = modulestore().get_item(course.location)
        self.assertCountEqual(extract_dates_from_course(course), expected_dates)

        # course 6: due_num_weeks in one of the sections
        course = self.courses[5]
        chapter = course.get_children()[0]
        sequential = chapter.get_children()
        expected_dates = [(course.location, {}),
                        (chapter.location, timedelta(days=28)),
                        (sequential[1].location, {'due': timedelta(days=7)})]
        course = modulestore().get_item(course.location)
        self.assertCountEqual(extract_dates_from_course(course), expected_dates)

        # course 7: a unit with an ORA problem
        course = self.courses[6]
        chapter = course.get_children()[0]
        sequential = chapter.get_children()[0]
        vertical = sequential.get_children()[0]
        expected_dates = [(course.location, {}),
                        (chapter.location, timedelta(days=28)),
                        (sequential.location, {'due': timedelta(days=7)}),
                        (vertical.location, {'due': timedelta(days=7)})]
        course = modulestore().get_item(course.location)
        self.assertCountEqual(extract_dates_from_course(course), expected_dates)

        # course 8: a unit with an ORA problem and a nonORA problem
        course = self.courses[7]
        chapter = course.get_children()[0]
        sequential = chapter.get_children()[0]
        vertical = sequential.get_children()[0]
        problem = vertical.get_children()[1]
        expected_dates = [(course.location, {}),
                        (chapter.location, timedelta(days=28)),
                        (sequential.location, {'due': timedelta(days=14)}),
                        (vertical.location, {'due': timedelta(days=14)}),
                        (problem.location, {'due': timedelta(days=14)})]
        course = modulestore().get_item(course.location)
        self.assertCountEqual(extract_dates_from_course(course), expected_dates)

        # course 9: a section with a subsection that has due_num_weeks and a section without due_num_weeks that has graded content
        course = self.courses[8]
        chapter1 = course.get_children()[0]
        sequential1 = chapter1.get_children()[0]
        vertical1 = sequential1.get_children()[0]
        problem1 = vertical1.get_children()[0]

        chapter2 = course.get_children()[1]
        sequential2 = chapter2.get_children()[0]
        vertical2 = sequential2.get_children()[0]
        problem2 = vertical2.get_children()[0]

        expected_dates = [(course.location, {}),
                        (chapter1.location, timedelta(days=14)),
                        (sequential1.location, {'due': timedelta(days=14)}),
                        (vertical1.location, {'due': timedelta(days=14)}),
                        (problem1.location, {'due': timedelta(days=14)}),
                        (chapter2.location, timedelta(days=28)),
                        (sequential2.location, {'due': timedelta(days=28)}),
                        (vertical2.location, {'due': timedelta(days=28)}),
                        (problem2.location, {'due': timedelta(days=28)})]
        course = modulestore().get_item(course.location)
        self.assertCountEqual(extract_dates_from_course(course), expected_dates)

        # course 10:
        course = self.courses[9]
        chapter1 = course.get_children()[0]
        sequential1 = chapter1.get_children()[0]
        vertical1 = sequential1.get_children()[0]
        problem1 = vertical1.get_children()[0]

        chapter2 = course.get_children()[1]
        sequential2 = chapter2.get_children()[0]
        vertical2 = sequential2.get_children()[0]
        problem2 = vertical2.get_children()[0]

        chapter3 = course.get_children()[2]
        sequential3 = chapter3.get_children()[0]
        vertical3 = sequential3.get_children()[0]
        problem3 = vertical3.get_children()[0]

        chapter4 = course.get_children()[3]
        sequential4 = chapter4.get_children()[0]
        vertical4 = sequential4.get_children()[0]
        problem4 = vertical4.get_children()[0]

        expected_dates = [(course.location, {}),
                        (chapter1.location, timedelta(days=14)),
                        (sequential1.location, {'due': timedelta(days=14)}),
                        (vertical1.location, {'due': timedelta(days=14)}),
                        (problem1.location, {'due': timedelta(days=14)}),
                        (chapter2.location, timedelta(days=28)),
                        (sequential2.location, {'due': timedelta(days=28)}),
                        (vertical2.location, {'due': timedelta(days=28)}),
                        (problem2.location, {'due': timedelta(days=28)}),
                        (chapter3.location, timedelta(days=42)),
                        (sequential3.location, {'due': timedelta(days=42)}),
                        (vertical3.location, {'due': timedelta(days=42)}),
                        (problem3.location, {'due': timedelta(days=42)}),
                        (chapter4.location, timedelta(days=56)),
                        (sequential4.location, {'due': timedelta(days=56)}),
                        (vertical4.location, {'due': timedelta(days=56)}),
                        (problem4.location, {'due': timedelta(days=56)})]
        course = modulestore().get_item(course.location)
        with patch.object(utils, 'get_expected_duration', return_value=timedelta(weeks=8)):
            actual = extract_dates_from_course(course)
        self.assertCountEqual(actual, expected_dates)
