from django.test import TestCase
from portfolio_manager.models import *
from datetime import datetime, timedelta
from django.utils import timezone
from decimal import *
from portfolio_manager.serializers import ProjectSerializer
from rest_framework.renderers import JSONRenderer
from portfolio_manager.importer import from_data_array
from dateutil.parser import parse

class ImporterTestCase(TestCase):

    def setUp(self):
        pass

    def test_import_dimension_name(self):
        data = [[u'id', u'__history_date', u'Name   '],
                ['', '', 'TEXT'],
                [u'1', '2013-03-16T17:41:28+00:00', 'foo'],
                ]
        result = from_data_array(data)
        self.assertTrue(result['result'], 'Failed to validate field types in imported data')
        self.assertEqual('Name', Project.objects.get(id=1).dimensions.all()[0].dimension_object.name)

    def test_import_size_money(self):
        data = [[u'id', u'__history_date', u'Name', u'SizeBudget'],
                ['', '', 'TEXT', 'NUM'],
                [u'2', '7/12/2015', 'foo', '100'],
                [u'2', '14/12/2015', u'', '30'],
                [u'2', '6/1/2016', u'','4'],
                [u'2', '8/2/2016', u'','1251'],
                [u'2', '14/3/2015', u'','325']
                ]
        result = from_data_array(data)
        self.assertTrue(result['result'], 'Failed to validate field types in imported data')
        self.assertEqual(5, Project.objects.get(id=2).dimensions.all()[1].dimension_object.history.all().count())
        
    def test_import_name(self):
        data = [[u'id', u'__history_date', u'Name'],
                ['', '', 'TEXT'],
                [u'1', '2013-03-16T17:41:28+00:00', 'foo'],
                [u'1', '2013-03-17T17:41:28+00:00'],
                [u'1', '2013-03-18T17:41:28+00:00', 'baz'],
                [u'2', '2013-03-20T17:41:28+00:00', 'dir '],
                [u'2', '2013-03-19T17:41:28+00:00', 'biz']
                ]
        result = from_data_array(data)
        self.assertTrue(result['result'], 'Failed to validate field types in imported data')
        self.assertEqual(2, Project.objects.all().count())
        self.assertEqual(2, Project.objects.get(id=1).dimensions.all()[0].dimension_object.history.all().count())
        self.assertEqual(2, Project.objects.get(id=2).dimensions.all()[0].dimension_object.history.all().count())
        self.assertEqual('dir', Project.objects.get(id=2).dimensions.all()[0].dimension_object.history.all()[0].value)
        self.assertEqual('biz', Project.objects.get(id=2).dimensions.all()[0].dimension_object.history.all()[1].value)
        self.assertEqual('baz', Project.objects.get(id=1).name)

    def test_import_dmy_startdate_dmy_history_date(self):
        data = [[u'id', u'__history_date', u'StartDate'],
                ['', '', 'DATE'],
                [u'1', '03/18/2013', '5/6/2017'],
                [u'1', '03/16/2013', '3/4/2015']
                ]
        result = from_data_array(data)
        self.assertTrue(result['result'], 'Failed to validate field types in imported data')
        self.assertEqual(2, Project.objects.get(id=1).dimensions.all()[0].dimension_object.history.all().count())
        self.assertEqual(datetime(2017,6,5,tzinfo=pytz.utc), Project.objects.get(id=1).dimensions.all()[0].dimension_object.history.all()[0].value)
        self.assertEqual(datetime(2015,4,3,tzinfo=pytz.utc), Project.objects.get(id=1).dimensions.all()[0].dimension_object.history.all()[1].value)

    def test_import_startdate(self):
        data = [[u'id', u'__history_date', u'StartDate'],
                ['', '', 'DATE'],
                [u'1', '2013-03-16T17:41:28+00:00', '2013-05-16T17:41:28+00:00'],
                [u'1', '2013-03-18T17:41:28+00:00', '2013-07-16T17:41:28+00:00'],
                [u'1', '2013-03-15T17:41:28+00:00', '1/8/2012'],
                [u'1', '2013-03-14T17:41:28+00:00', '2015-01-08T00:00:00+00:00'],
                ]
        result = from_data_array(data)
        self.assertTrue(result['result'], 'Failed to validate field types in imported data')
        self.assertEqual(1, Project.objects.all().count())
        history = Project.objects.get(id=1).dimensions.all()[0].dimension_object.history.all()
        self.assertEqual(4, history.count())
        self.assertEqual(parse('2013-07-16T17:41:28+00:00'), history[0].value)
        self.assertEqual(parse('2013-05-16T17:41:28+00:00'), history[1].value)
        self.assertEqual(datetime(2012, 8, 1, tzinfo=pytz.utc), history[2].value)
        self.assertEqual(datetime(2015, 8, 1, tzinfo=pytz.utc), history[3].value)
        

    def test_import_projectmanager(self):
        data = [[u'id', u'__history_date', u'ProjectManager'],
                ['', '', 'APER'],
                [u'1', '2013-03-16T17:41:28+00:00', 'Pekka '],
                [u'1', '2013-03-18T17:41:28+00:00', 'Matti'],
                [u'1', '2013-03-19T17:41:28+00:00', 'Pekka'],
                ]
        result = from_data_array(data)
        self.assertTrue(result['result'], 'Failed to validate field types in imported data')
        self.assertEqual(1, Project.objects.all().count())
        history = Project.objects.get(id=1).dimensions.all()[0].dimension_object.history.all()
        self.assertEqual(3, history.count())
        self.assertEqual(2, Person.objects.all().count())
        self.assertEqual(Person.objects.get(first_name='Pekka'), history[0].value)
        self.assertEqual(Person.objects.get(first_name='Matti'), history[1].value)
        self.assertEqual(Person.objects.get(first_name='Pekka'), history[2].value)

    def test_import_members(self):
        data = [[u'id', u'__history_date', u'Members'],
                ['', '', 'APERS'],
                [u'1', '2013-03-16T17:41:28+00:00', 'Pekka ,Matti'],
                [u'1', '2013-03-18T17:41:28+00:00', 'Matti'],
                [u'1', '2013-03-19T17:41:28+00:00', 'Taneli  ,Pekka '],
                ]
        result = from_data_array(data)
        self.assertTrue(result['result'], 'Failed to validate field types in imported data')
        self.assertEqual(1, Project.objects.all().count())
        self.assertEqual(3, Person.objects.all().count())
        self.assertEqual(Person.objects.get(first_name='Taneli'), Project.objects.get(id=1).dimensions.all()[0].dimension_object.persons.all()[1])
        self.assertEqual(Person.objects.get(first_name='Pekka'), Project.objects.get(id=1).dimensions.all()[0].dimension_object.persons.all()[0])

    def test_import_projectdependencies(self):
        data = [[u'id', u'__history_date', u'Name', u'ProjectDependencies'],
                ['', '', 'TEXT', 'APROJ'],
                [u'1', '2013-03-16T17:41:28+00:00', 'Project1'],
                [u'2', '2013-03-18T17:41:28+00:00', 'Project2', '1'],
                [u'3', '2013-03-19T17:41:28+00:00', 'Project3', '1, 2'],
                ]
        result = from_data_array(data)
        self.assertTrue(result['result'], 'Failed to validate field types in imported data')
        self.assertEqual(3, Project.objects.all().count())
        self.assertEquals(1, Project.objects.get(id=1).dimensions.all().count())
        self.assertEquals(1, Project.objects.get(id=2).dimensions.all()[1].dimension_object.projects.all().count())
        self.assertEquals(Project.objects.get(pk=1), Project.objects.get(id=2).dimensions.all()[1].dimension_object.projects.all()[0])
        self.assertEquals(2, Project.objects.get(id=3).dimensions.all()[1].dimension_object.projects.all().count())
        self.assertEquals(Project.objects.get(pk=1), Project.objects.get(id=3).dimensions.all()[1].dimension_object.projects.all()[0])
        self.assertEquals(Project.objects.get(pk=2), Project.objects.get(id=3).dimensions.all()[1].dimension_object.projects.all()[1])

    def test_overwrite_project(self):
        project = Project()
        project.id = 1
        project.save()

        d1 = DecimalDimension()
        d1.name = 'budjetti'
        d1.value = 5
        d1.save()

        pd1 = ProjectDimension()
        pd1.project = project
        pd1.dimension_object = d1
        pd1.save()

        data = [[u'id', u'__history_date', u'Name'],
                ['', '', 'TEXT'],
                [u'1', '2013-03-16T17:41:28+00:00', 'foo']]
        result = from_data_array(data)
        self.assertTrue(result['result'], 'Failed to validate field types in imported data')
        self.assertEqual(1, Project.objects.get(id=1).dimensions.all().count())
        self.assertTrue(isinstance(Project.objects.get(id=1).dimensions.all()[0].dimension_object, TextDimension))
        self.assertEqual(0, DecimalDimension.objects.all().count())
        self.assertEqual(1, ProjectDimension.objects.all().count())

    def test_keep_unaffected_projects(self):
        project = Project()
        project.id = 1
        project.save()

        d1 = DecimalDimension()
        d1.name = 'budjetti'
        d1.value = 5
        d1.save()

        pd1 = ProjectDimension()
        pd1.project = project
        pd1.dimension_object = d1
        pd1.save()

        data = [[u'id', u'__history_date', u'Name'],
                ['', '', 'TEXT'],
                [u'2', '2013-03-16T17:41:28+00:00', 'foo']]
        result = from_data_array(data)
        self.assertTrue(result['result'], 'Failed to validate field types in imported data')
        self.assertEqual(2, Project.objects.all().count())
        self.assertEqual(1, Project.objects.get(id=1).dimensions.all().count())
        self.assertTrue(isinstance(Project.objects.get(id=1).dimensions.all()[0].dimension_object, DecimalDimension))

    def test_importer_unknown_column(self):
        data = [[u'id', u'__history_date', u'UnknownDimensionType'],
                ['', '', 'FOO'],
                [u'2', '2013-03-16T17:41:28+00:00', 'foo']]
        result = from_data_array(data)
        # current behaviour in code is that importing returns fail if there are unknown type names in the type row.
        self.assertFalse(result['result'])

    def test_importer_size_money_milestone(self):
        data = [[u'id', u'__history_date', u'Name', u'SizeBudget'],
                ['', '', 'TEXT', 'NUM'],
                [u'1', '2012-03-16T17:41:28+00:00', 'foo', '4'],
                [u'm;1/6/2015', '2013-03-16T17:41:28+00:00', u'', u'5'],
                [u'm;1/7/2016', '2014-03-16T17:41:28+00:00', u'', u'9']]
        result = from_data_array(data)
        self.assertTrue(result['result'], 'Failed to validate field types in imported data')
        milestones = Project.objects.get(id=1).milestones.all()

        self.assertEqual(2, milestones.count())
        self.assertEqual(datetime(2015, 6, 1, tzinfo=pytz.utc), milestones[0].history.all()[0].due_date)
        self.assertEqual(datetime(2016, 7, 1, tzinfo=pytz.utc), milestones[1].history.all()[0].due_date)
        self.assertEqual(1, milestones[0].history.all().count())
        self.assertEqual(parse('2013-03-16T17:41:28+00:00'), milestones[0].history.all()[0].history_date)
        self.assertEqual(5, milestones[0].history.all()[0].dimensions.all()[0].dimension_milestone_object.value)
        self.assertEqual(9, milestones[1].history.all()[0].dimensions.all()[0].dimension_milestone_object.value)
        self.assertEquals(milestones[1].history.all()[0].dimensions.all()[0].project_dimension, Project.objects.get(id=1).dimensions.all()[1])

    def test_dayfirst_in_history_date(self):
        data = [[u'id', u'__history_date', u'Name   '],
                ['', '', 'TEXT'],
                [u'1', '1/8/2015', 'foo'],
                [u'1', '2014-03-09T00:00:00+00:00', 'bar'],
                ]
        result = from_data_array(data)
        self.assertTrue(result['result'], 'Failed to validate field types in imported data')
        actual_history_date = Project.objects.get(pk=1).dimensions.all()[0].dimension_object.history.all()[0].history_date
        self.assertEqual(datetime(2015, 8, 1, tzinfo=pytz.utc),  actual_history_date)
        actual_history_date = Project.objects.get(pk=1).dimensions.all()[0].dimension_object.history.all()[1].history_date
        self.assertEqual(datetime(2014, 9, 3, tzinfo=pytz.utc),  actual_history_date)

    def test_import_owningorganization(self):
        data = [[u'id', u'__history_date', u'OwningOrganization', u'Name', u'SizeBudget'],
                ['', '', 'AORG', 'TEXT', 'NUM'],
                [u'1', '2013-03-16T17:41:28+00:00', 'Org1', 'boo', '4'],
                [u'1', '2013-03-18T17:41:28+00:00', 'Org2', 'biz'],
                [u'1', '2013-03-19T17:41:28+00:00', 'Org1 '],
                ]
        result = from_data_array(data)
        self.assertTrue(result['result'], 'Failed to validate field types in imported data')
        self.assertEqual(1, Organization.objects.get(name='Org1').templates.all().count())
        self.assertEqual(1, Organization.objects.get(name='Org2').templates.all().count())
    
        org1_template = Organization.objects.get(name='Org1').templates.all()[0]
        self.assertEqual('default', org1_template.name)
        self.assertEqual(3, org1_template.dimensions.all().count())
        self.assertEqual('OwningOrganization', org1_template.dimensions.all()[0].name)
        self.assertEqual(ContentType.objects.get(model='associatedorganizationdimension'), org1_template.dimensions.all()[0].content_type)
        self.assertEqual('Name', org1_template.dimensions.all()[1].name)
        self.assertEqual(ContentType.objects.get(model='textdimension'), org1_template.dimensions.all()[1].content_type)
        self.assertEqual('SizeBudget', org1_template.dimensions.all()[2].name)
        self.assertEqual(ContentType.objects.get(model='decimaldimension'), org1_template.dimensions.all()[2].content_type)

        org2_template = Organization.objects.get(name='Org2').templates.all()[0]
        self.assertEqual(3, org2_template.dimensions.all().count())
        self.assertEqual('OwningOrganization', org2_template.dimensions.all()[0].name)
        self.assertEqual(ContentType.objects.get(model='associatedorganizationdimension'), org2_template.dimensions.all()[0].content_type)
        self.assertEqual('Name', org2_template.dimensions.all()[1].name)
        self.assertEqual(ContentType.objects.get(model='textdimension'), org2_template.dimensions.all()[1].content_type)
        self.assertEqual('SizeBudget', org2_template.dimensions.all()[2].name)
        self.assertEqual(ContentType.objects.get(model='decimaldimension'), org2_template.dimensions.all()[2].content_type)

