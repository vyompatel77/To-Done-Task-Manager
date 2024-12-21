from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from todo.models import List, ListItem
import csv
from io import StringIO
import datetime


class ImportTodoCSVTestCase(TestCase):

    def setUp(self):
        self.url = reverse('todo:import_todo_csv')
        # Ensure database is clean before starting each test
        List.objects.all().delete()
        ListItem.objects.all().delete()

    def tearDown(self):
        # Explicitly clear all data after each test
        List.objects.all().delete()
        ListItem.objects.all().delete()

    # Utility function to generate CSV files for testing
    def generate_csv_file(self, rows):
        file = StringIO()
        writer = csv.writer(file)
        writer.writerow(['List Title', 'Item Name', 'Item Text', 'Is Done', 'Created On', 'Due Date'])
        writer.writerows(rows)
        file.seek(0)
        return SimpleUploadedFile("test.csv", file.read().encode('utf-8'), content_type="text/csv")

    def test_successful_import_with_minimal_data(self):
        csv_file = self.generate_csv_file([
            ['Minimal List', 'Minimal Item', 'Minimal Text', 'true', '2024-01-01', '2024-02-01']
        ])
        self.client.post(self.url, {'csv_file': csv_file})
        self.assertTrue(List.objects.filter(title_text="Minimal List").exists())
        self.assertTrue(ListItem.objects.filter(item_name="Minimal Item").exists())

    def test_import_with_all_false_is_done(self):
        csv_file = self.generate_csv_file([
            ['Test List', 'Item 1', 'Text for item 1', 'false', '2024-10-01', '2024-12-01'],
            ['Test List', 'Item 2', 'Text for item 2', 'false', '2024-10-01', '2024-12-01']
        ])
        self.client.post(self.url, {'csv_file': csv_file})
        self.assertEqual(ListItem.objects.filter(is_done=False).count(), 2)

    def test_import_with_dates_only(self):
        csv_file = self.generate_csv_file([
            ['Test List', 'Item 1', 'Text for item 1', 'true', '2024-10-01', '2024-12-01']
        ])
        self.client.post(self.url, {'csv_file': csv_file})
        items = ListItem.objects.filter(item_name="Item 1")
        self.assertEqual(items.count(), 1)
        self.assertEqual(items.first().created_on.date(), datetime.date(2024, 10, 1))

    def test_import_with_empty_csv(self):
        csv_file = self.generate_csv_file([])
        self.client.post(self.url, {'csv_file': csv_file})
        self.assertEqual(ListItem.objects.count(), 0)

    def test_blank_is_done_field(self):
        csv_file = self.generate_csv_file([
            ['List Blank Is Done', 'Item Blank Is Done', 'Some Text', '', '2024-01-01', '2024-03-01']
        ])
        self.client.post(self.url, {'csv_file': csv_file})
        self.assertTrue(ListItem.objects.filter(is_done=False).exists())

    def test_case_insensitive_boolean_in_is_done_field(self):
        csv_file = self.generate_csv_file([
            ['Case Insensitive Boolean List', 'Boolean Item', 'Boolean Text', 'TRUE', '2024-01-01', '2024-04-01']
        ])
        self.client.post(self.url, {'csv_file': csv_file})
        self.assertTrue(ListItem.objects.filter(is_done=True).exists())

    def test_numeric_title_text_field(self):
        csv_file = self.generate_csv_file([
            ['12345', 'Item Numeric Title', 'Text for Numeric Title', 'false', '2024-01-01', '2024-04-01']
        ])
        self.client.post(self.url, {'csv_file': csv_file})
        self.assertTrue(List.objects.filter(title_text="12345").exists())

    def test_special_characters_in_item_name(self):
        csv_file = self.generate_csv_file([
            ['Special Char List', '@Special#Item!', 'Some text here', 'true', '2024-01-01', '2024-05-01']
        ])
        self.client.post(self.url, {'csv_file': csv_file})
        self.assertTrue(ListItem.objects.filter(item_name="@Special#Item!").exists())

    def test_multiple_rows_in_csv(self):
        csv_file = self.generate_csv_file([
            ['Multi List', 'Item One', 'Text One', 'true', '2024-01-01', '2024-04-01'],
            ['Multi List', 'Item Two', 'Text Two', 'false', '2024-01-02', '2024-05-01']
        ])
        self.client.post(self.url, {'csv_file': csv_file})
        self.assertEqual(List.objects.filter(title_text="Multi List").count(), 1)
        self.assertEqual(ListItem.objects.filter(list__title_text="Multi List").count(), 2)

    def test_successful_import_with_valid_data(self):
        csv_file = self.generate_csv_file([
            ['Test List', 'Item 1', 'Text for item 1', 'true', '2024-10-01', '2024-12-01']
        ])
        self.client.post(self.url, {'csv_file': csv_file})
        self.assertTrue(ListItem.objects.filter(item_name="Item 1").exists())

    def test_import_with_missing_item_text(self):
        csv_file = self.generate_csv_file([
            ['Test List', 'Item 1', '', 'true', '2024-10-01', '2024-12-01']
        ])
        self.client.post(self.url, {'csv_file': csv_file})
        self.assertTrue(ListItem.objects.filter(item_name="Item 1").exists())

    def test_import_with_non_boolean_is_done(self):
        csv_file = self.generate_csv_file([
            ['Test List', 'Item 1', 'Text for item 1', 'maybe', '2024-10-01', '2024-12-01']
        ])
        self.client.post(self.url, {'csv_file': csv_file})
        self.assertTrue(ListItem.objects.filter(item_name="Item 1", is_done=False).exists())

    def test_import_with_one_valid_row(self):
        csv_file = self.generate_csv_file([
            ['Test List', 'Single Item', 'Single Text', 'true', '2024-10-01', '2024-12-01']
        ])
        self.client.post(self.url, {'csv_file': csv_file})
        self.assertTrue(ListItem.objects.filter(item_name="Single Item").exists())
