# coding=utf-8
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import LiveServerTestCase
from django.urls import reverse
from selenium.webdriver.firefox.webdriver import WebDriver as Firefox 
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from portfolio_manager.models import *
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from decimal import *
from pyvirtualdisplay import Display

WAIT = 7


class SeleniumTestCase(StaticLiveServerTestCase):

    def open(self, url):
        self.selenium.get("%s%s" % (self.live_server_url, url))


class CustomFirefoxWebDriver(Firefox):

    def find_css(self, css_selector):
        elems = self.find_elements_by_css_selector(css_selector)
        found = len(elems)
        if found == 1:
            return elems[0]
        elif not elems:
            raise NoSuchElementException(css_selector)
        return elems

    def wait_for_css(self, css_selector, timeout=WAIT):
        return WebDriverWait(self, timeout).until(lambda driver : driver.find_css(css_selector))


#class BrowserTestCase(StaticLiveServerTestCase):
class BrowserTestCase(SeleniumTestCase):

    fixtures = ['organizations', 'project_templates', 'persons_browser_testing', 'projects_browser_testing']

    def setUp(self):
        
        # Start xvfb for Firefox
        #self.vdisplay = Display(visible=0, size=(1024, 768))
        #self.vdisplay.start()

        self.selenium = CustomFirefoxWebDriver()
        self.selenium.maximize_window()
        super(BrowserTestCase, self).setUp()

    def tearDown(self):
        
        super(BrowserTestCase, self).tearDown()

        self.selenium.quit()
        #self.vdisplay.stop()

    def find(self, id_prop):
        return self.selenium.find_element_by_id(id_prop)

    def assert_that_element_appears(self, element_id):
        try:
            WebDriverWait(self.selenium, WAIT).until(EC.visibility_of_element_located((By.ID, element_id)))
            found = True
        except TimeoutException:
            found = False
        self.assertTrue(found, "Element with id '%s' failed to appear." % element_id)

    def assert_that_element_disappears(self, element_id):
        try:
            WebDriverWait(self.selenium, WAIT).until(EC.invisibility_of_element_located((By.ID, element_id)))
            gone = True
        except TimeoutException:
            gone = False
        self.assertTrue(gone, "Element with id '%s' is still there." % element_id)

    def test_add_organization(self):

        self.open(reverse('admin_tools'))

        add_organization_name = 'Örganizaatio'

        # Insert values to "Add organization form and submit"
        self.find('orgName').send_keys(add_organization_name)
        self.find('org-form').submit()

        # Wait for notification that reports success
        self.selenium.wait_for_css('#conf-modal-body > h3');

        # Check the notification message
        self.assertTrue('Organization created: '+add_organization_name in self.selenium.page_source)
        
        # Check that organization was property added to db
        organization = Organization.objects.get(pk=add_organization_name)
        self.assertIsInstance(organization, Organization)
        templates = organization.templates.all()
        self.assertEquals(1, templates.count())
        template = templates[0]
        self.assertEquals('default', template.name)
        self.assertEquals(3, template.dimensions.all().count())
        template_dimensions = template.dimensions.all()
        self.assertEquals(DecimalDimension, template_dimensions[0].content_type.model_class())
        self.assertEquals('SizeBudget', template_dimensions[0].name)
        self.assertEquals(DateDimension, template_dimensions[1].content_type.model_class())
        self.assertEquals('EndDate', template_dimensions[1].name)
        self.assertEquals(AssociatedPersonDimension, template_dimensions[2].content_type.model_class())
        self.assertEquals('ProjectManager', template_dimensions[2].name)


    def test_add_organization_add_project(self):
        """ Test adding new organization and new project under that organization"""


        self.open(reverse('admin_tools'))

        organization_name = 'Great organization'
        self.find('orgName').send_keys(organization_name)
        self.find('org-form').submit()

        # Wait for modal to open
        self.selenium.wait_for_css('#conf-modal-body > h3')
 
        self.open(reverse('admin_tools')) # Reload organizations in "Add project" modal

        # Fill in "Add project" form on Admin tools page and submit it
        project_name = "Great project"
        self.find('id_name').send_keys(project_name)
        Select(self.find('id_organization')).select_by_value(organization_name)
        self.find('pre-add-project-form').submit()

        # Wait for add project page to open up
        self.assert_that_element_appears('id_add_project_form-name')

        organization = Organization.objects.get(pk=organization_name)

        # Fill in the details of new project and hit submit

        project_size_budget = '135151.00'
        template_dimension = organization.templates.all()[0].dimensions.all()[0]
        self.find('id_'+str(template_dimension.id)+'_form-value').send_keys(project_size_budget)
       
        project_end_date = '1/8/2015'
        template_dimension = organization.templates.all()[0].dimensions.all()[1]
        self.find('id_'+str(template_dimension.id)+'_form-value').send_keys(project_end_date)
        
        project_project_manager = Person.objects.get(id=2)
        template_dimension = organization.templates.all()[0].dimensions.all()[2]
        Select(self.find('id_'+str(template_dimension.id)+'_form-value')).select_by_value(str(project_project_manager.id))
        
        self.find('add-project-form').submit()

        # Wait until user is redirected to "Show project" page and check that page contains
        # correct information
        self.assert_that_element_appears('project-dimension-panels')


        self.assertEquals(project_name, self.find('project-name').text)
        self.assertEquals(organization_name, self.find('projectparent').text)
        self.assertEquals('Aug. 1, 2015, midnight', self.find('EndDate').text)
        self.assertEquals(str(project_project_manager), self.find('ProjectManager').text)
        self.assertEquals(project_size_budget, self.find('SizeBudget').text)

    def test_add_project_from_admin_tools(self):
        self.open(reverse('admin_tools'))
        self._test_add_project()

    def test_add_project_from_homepage(self):

        self.open(reverse('homepage'))
        self.find('add-project-btn').click()

        # Wait until pre add project form is loaded
        self.assert_that_element_appears('id_name')

        self._test_add_project()

    def _test_add_project(self):

        project_name = "FooBar"
        project_organization = Organization.objects.get(pk='org1')

        # Fill in details of new project and click "Continue"
        self.find('id_name').send_keys(project_name)
        Select(self.find('id_organization')).select_by_value(project_organization.pk)
        self.find('pre-add-project-form').submit()

        # Wait for "Add project" page to load
        self.assert_that_element_appears('id_add_project_form-name')

        # Check that project name and organization are propertly transmitted from pre add project form
        self.assertEquals(project_name, self.find('id_add_project_form-name').get_attribute('value'))
        self.assertEquals(project_organization.pk, self.find('id_add_project_form-organization').get_attribute('value'))

        # Fill in the detail of new project and submit
        project_phase = "Pre-study"
        template_dimension = project_organization.templates.all()[0].dimensions.all()[0]
        self.find('id_'+str(template_dimension.id)+'_form-value').send_keys(project_phase)
       
        project_size = '135151.00'
        template_dimension = project_organization.templates.all()[0].dimensions.all()[1]
        self.find('id_'+str(template_dimension.id)+'_form-value').send_keys(project_size)
        self.find('add-project-form').submit()

        # Wait for "Show project" to load
        self.assert_that_element_appears('project-dimension-panels')

        # Check that "Show project" page contains correct information
        self.assertEquals(project_name, self.find('project-name').text)
        self.assertEquals(project_organization.pk, self.find('projectparent').text)
        self.assertEquals(project_phase, self.find('Phase').text)
        self.assertEquals(project_size, self.find('Size').text)

        # Check that correct information is loaded to db
        project = Project.objects.get(name=project_name)
        self.assertIsInstance(project, Project)
        self.assertEquals(project_organization, project.parent)
        dimensions = project.dimensions.all()
        self.assertEquals(2, dimensions.count())
        self.assertIsInstance(dimensions[0].dimension_object, TextDimension)
        self.assertEquals(project_phase, dimensions[0].dimension_object.value)
        self.assertIsInstance(dimensions[1].dimension_object, DecimalDimension)
        self.assertEquals(Decimal(project_size), dimensions[1].dimension_object.value)

    def _test_modify_project_X_dimension(self, project_id, dimension_name, new_value_field_id, modal_id, form_id, new_value, cmp_value):
        
        self.open(reverse('show_project', args=(project_id,)))

        # Click the "Modify" button of the dimension
        self.selenium.find_css('button[data-field="'+dimension_name+'"]').click()

        # Wait for modal to open up
        self.assert_that_element_appears(new_value_field_id)

        # Update form value and submit
        self.find(new_value_field_id).send_keys(new_value)
        self.selenium.find_css('#'+form_id+' button[type="submit"]').click()

        # Wait for modal to close
        self.assert_that_element_disappears(new_value_field_id)

        # Check that dimension value was updated
        self.assertEquals(cmp_value, self.find(dimension_name).text)

    def test_modify_project_text_dimension(self):
        self._test_modify_project_X_dimension(1, 'Phase', 'newTextValue', 'modify-text-modal', 'modify-text-form', 'Done', 'Done')

    def test_modify_project_decimal_dimension(self):
        self._test_modify_project_X_dimension(1, 'SizeBudget', 'newDecValue', 'modify-dec-modal', 'modify-dec-form', '38', '38')

    def test_modify_project_date_dimension(self):
        self._test_modify_project_X_dimension(1, 'EndDate', 'date', 'modify-date-modal', 'modify-date-form', "1/9/2019", "2019-09-01T00:00:00Z")

    def test_modify_project_associated_person_dimension(self):

        self.open(reverse('show_project', args=(1,)))

        # Click "Modify" button of ProjectManager dimension
        self.selenium.find_css('button[data-field="ProjectManager"]').click()

        # Wait for modal to open up
        self.assert_that_element_appears('person')

        # Select another person from dropdown and submit the form
        Select(self.find('person')).select_by_value('2')
        self.selenium.find_css('#modify-per-form button[type="submit"]').click()

        #Wait for modal to close
        self.assert_that_element_disappears('modify-per-modal')

        # Check that dimension value is updated
        self.assertEquals(str(Person.objects.get(id=2)), self.find('ProjectManager').text)


    def test_modify_project_associated_persons_dimension_remove(self):
        
        self.open(reverse('show_project', args=(1,)))

        # Click "Modify" of Members dimension
        self.selenium.find_css('button[data-field="Members"].multiple-modify-button').click()

        # Wait for modal to open up
        self.assert_that_element_appears('add-person-to-project-form')

        # Click to remove the only associated person
        self.selenium.find_css('button.remove-multiple-persons[data-id="1"]').click()

        # Wait for person to disappear from the modal
        self.assert_that_element_disappears('#multiple-person-1')

        # Close modal
        self.selenium.find_css('#multiple-items-modal button.close[data-dismiss="modal"]').click()

        # Wait for modal to close
        self.assert_that_element_disappears('multiple-items-modal')

        # Click "Click to see to all"
        self.selenium.find_css('#Members button').click()

        # Wait for modal to open up
        self.assert_that_element_appears('multiple-items-modal')

        # Modal should not list any members
        self.assertEquals(0, len(self.selenium.find_elements_by_css_selector('#multiple-well-ul li')))

    def test_modify_project_associated_persons_dimension_add(self):
        
        self.open(reverse('show_project', args=(1,)))

        # Click "Modify" of Members dimension
        self.selenium.find_css('button[data-field="Members"].multiple-modify-button').click()

        # Wait for modal to open up
        self.assert_that_element_appears('add-person-to-project-form')

        # Select person to add and click '+'
        Select(self.find('add-person-to-project')).select_by_value('2')
        self.selenium.find_css('#add-person-to-project-form button.btn-success').click()

        # Wait for alert
        WebDriverWait(self.selenium, WAIT).until(EC.alert_is_present(), 'Timed out waiting for popup to appear.')

        alert = self.selenium.switch_to_alert()
        self.assertTrue('Successfully' in alert.text)
        alert.accept()
     
        # Wait for modal to close
        self.assert_that_element_disappears('multiple-items-modal')

        # Click "Click to see to all"
        self.selenium.find_css('#Members button').click()

        # Wait for modal to open up
        self.assert_that_element_appears('multiple-items-modal')

        # Modal should not list any members
        self.assertEquals(2, len(self.selenium.find_elements_by_css_selector('#multiple-well-ul li')))

    def test_modify_project_associated_projects_dimension_remove(self):

        self.open(reverse('show_project', args=(1,)))

        # Click "Modify" of Dependencies dimension
        self.selenium.find_css('button[data-field="Dependencies"].multiple-modify-button').click()

        # Wait for modal to open up
        self.assert_that_element_appears('add-project-to-project-form')

        # Click to remove the only associated project
        self.selenium.find_css('button.remove-multiple-projects[data-id="1"]').click()

        # Wait for project to disappear from the modal
        self.assert_that_element_disappears('#multiple-project-1')

        # Close modal
        self.selenium.find_css('#multiple-items-modal button.close[data-dismiss="modal"]').click()

        # Wait for modal to close
        self.assert_that_element_disappears('multiple-items-modal')

        # Click "Click to see to all"
        self.selenium.find_css('#Dependencies button').click()

        # Wait for modal to open up
        self.assert_that_element_appears('multiple-items-modal')

        # Modal should not list any members
        self.assertEquals(0, len(self.selenium.find_elements_by_css_selector('#multiple-well-ul li')))

    def test_modify_project_associated_projects_dimension_add(self):
        
        self.open(reverse('show_project', args=(1,)))

        # Click "Modify" of Dependencies dimension
        self.selenium.find_css('button[data-field="Dependencies"].multiple-modify-button').click()

        # Wait for modal to open up
        self.assert_that_element_appears('add-project-to-project-form')

        # Select project to add and click '+'
        Select(self.find('add-project-to-project')).select_by_value('2')
        self.selenium.find_css('#add-project-to-project-form button.btn-success').click()

        # Wait for alert
        WebDriverWait(self.selenium, WAIT).until(EC.alert_is_present(),'Timed out waiting for popup to appear.')

        alert = self.selenium.switch_to_alert()
        self.assertTrue('Successfully' in alert.text)
        alert.accept()
     
        # Wait for modal to close
        self.assert_that_element_disappears('multiple-items-modal')

        # Click "Click to see to all"
        self.selenium.find_css('#Dependencies button').click()

        # Wait for modal to open up
        self.assert_that_element_appears('multiple-items-modal')

        # Modal should not list any members
        self.assertEquals(2, len(self.selenium.find_elements_by_css_selector('#multiple-well-ul li')))

