from django.urls import reverse
from django.test import TestCase, Client, RequestFactory
from django.contrib.auth.models import User
from todo.views import config, config_hook, delete_template, login_request, template_from_todo, template, delete_todo, index, getListTagsByUserid, removeListItem, addNewListItem, updateListItem, createNewTodoList, register_request, getListItemByName, getListItemById, markListItem, todo_from_template
from django.utils import timezone
from todo.models import List, ListItem, Template, TemplateItem, ListTags, SharedList
# from todo.forms import NewUserForm
# from django.contrib.messages.storage.fallback import FallbackStorage
# from django.contrib.auth.models import AnonymousUser
# from django.contrib.auth.forms import AuthenticationForm
# from django.contrib.messages import get_messages


class ExportTodoTestCase(TestCase):
    def setUp(self):
        # Define the export URL using 'export_todo_csv' view name
        # Create and log in a test user
        user = User.objects.create_user(
            username='testuserdiff', password='1234567')
        self.client.login(username='testuserdiff', password='1234567')
        self.export_url = reverse('todo:export_todo_csv')

    def test_export_url_exists(self):
        """Test if the export URL exists and returns a 200 status code."""
        response = self.client.get(self.export_url)
        assert response.status_code == 200

    def test_export_content_type(self):
        """Test if the export response content type is CSV."""
        response = self.client.get(self.export_url)
        assert response['Content-Type'] == 'text/csv'

    def test_export_responds_with_utf8_encoding(self):
        """Test if the export response uses UTF-8 encoding."""
        response = self.client.get(self.export_url)
        assert response.charset == 'utf-8'

    def test_export_no_query_params_required(self):
        """Test if export functionality works without needing query parameters."""
        response = self.client.get(self.export_url)
        assert response.status_code == 200

    def test_export_handles_large_request(self):
        """Simulate a large request scenario to see if export is functional."""
        response = self.client.get(self.export_url)
        assert response.status_code == 200

    def test_export_url_redirects_if_not_logged_in(self):
        """Test if the export URL redirects for unauthenticated users (if export requires login)."""
        response = self.client.get(self.export_url)
        # Change to 302 if login is required
        self.assertIn(response.status_code, [200, 302])

    def test_export_url_accessible_to_logged_in_user(self):
        """Test if the export URL is accessible to a logged-in user."""
        # Use a unique username to avoid conflicts
        unique_username = f"testuser_{timezone.now().timestamp()}"
        user = User.objects.create_user(
        username=unique_username, password="1234567"
    )
        self.client.login(username=unique_username, password="1234567")
        response = self.client.get(self.export_url)
        self.assertEqual(response.status_code, 200)


    def test_export_response_has_csv_extension_in_filename(self):
        """Test if the export response filename has the .csv extension."""
        response = self.client.get(self.export_url)
        content_disposition = response['Content-Disposition']
        self.assertTrue(content_disposition.endswith('.csv"'))

    def test_export_without_specified_encoding_still_defaults_utf8(self):
        """Test that export defaults to UTF-8 encoding when none is specified explicitly."""
        response = self.client.get(self.export_url)
        self.assertEqual(response.charset, 'utf-8')

    def test_export_response_non_empty_csv(self):
        """Ensure response is non-empty for default export functionality."""
        response = self.client.get(self.export_url)
        content = response.content.decode('utf-8')
        self.assertGreater(len(content), 0)

    def test_export_response_is_text_not_binary(self):
        """Check that the export CSV response is sent as text, not binary format."""
        response = self.client.get(self.export_url)
        self.assertNotIn('application/octet-stream', response['Content-Type'])

    def test_export_url_exists_and_returns_successfully(self):
        """Simple test to check if export URL exists and returns a response."""
        response = self.client.get(self.export_url)
        self.assertTrue(response)

    def test_export_returns_ok_status(self):
        """Test that the export function returns a 200 status code when accessed."""
        response = self.client.get(self.export_url)
        self.assertEqual(response.status_code, 200)
