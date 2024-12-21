import pytest
from django.contrib.auth.models import User
from todo.models import List, ListTags, ListItem, Template, TemplateItem, SharedUsers, SharedList
from datetime import datetime, date
import factory
import uuid


# Factory for creating unique users
class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.LazyAttribute(lambda _: f"user_{uuid.uuid4()}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    password = factory.PostGenerationMethodCall("set_password", "password123")


@pytest.mark.django_db
def test_list_creation():
    user = UserFactory()
    todo_list = List.objects.create(
        title_text="Test List",
        created_on=datetime.now(),
        updated_on=datetime.now(),
        user_id=user
    )
    assert str(todo_list) == "Test List"


@pytest.mark.django_db
def test_list_tags_creation():
    user = UserFactory()
    tag = ListTags.objects.create(
        user_id=user,
        tag_name="Important",
        created_on=datetime.now()
    )
    assert str(tag) == "Important"


@pytest.mark.django_db
def test_list_item_creation():
    user = UserFactory()
    todo_list = List.objects.create(
        title_text="Test List",
        created_on=datetime.now(),
        updated_on=datetime.now(),
        user_id=user
    )
    item = ListItem.objects.create(
        list=todo_list,
        item_name="Test Item",
        item_text="Description of the test item",
        created_on=datetime.now(),
        finished_on=datetime.now(),
        due_date=date.today(),
        tag_color="#FF5733"
    )
    assert str(item) == "Description of the test item: False"


@pytest.mark.django_db
def test_template_creation():
    user = UserFactory()
    template = Template.objects.create(
        title_text="Test Template",
        created_on=datetime.now(),
        updated_on=datetime.now(),
        user_id=user
    )
    assert str(template) == "Test Template"


@pytest.mark.django_db
def test_template_item_creation():
    user = UserFactory()
    template = Template.objects.create(
        title_text="Test Template",
        created_on=datetime.now(),
        updated_on=datetime.now(),
        user_id=user
    )
    item = TemplateItem.objects.create(
        template=template,
        item_text="Template Item",
        created_on=datetime.now(),
        finished_on=datetime.now(),
        due_date=date.today(),
        tag_color="#FFFFFF"
    )
    assert str(item) == "Template Item"


@pytest.mark.django_db
def test_shared_users_creation():
    user = UserFactory()
    todo_list = List.objects.create(
        title_text="Shared List",
        created_on=datetime.now(),
        updated_on=datetime.now(),
        user_id=user
    )
    shared_user = SharedUsers.objects.create(
        list_id=todo_list,
        shared_user="shareduser@example.com"
    )
    assert str(shared_user) == str(todo_list.id)


@pytest.mark.django_db
def test_shared_list_creation():
    user = UserFactory()
    shared_list = SharedList.objects.create(
        user=user,
        shared_list_id="12345"
    )
    assert str(shared_list) == str(user)


@pytest.mark.django_db
def test_list_default_tag():
    todo_list = List.objects.create(
        title_text="List with Default Tag",
        created_on=datetime.now(),
        updated_on=datetime.now()
    )
    assert todo_list.list_tag == "none"


@pytest.mark.django_db
def test_list_item_priority_choices():
    user = UserFactory()
    todo_list = List.objects.create(
        title_text="Priority List",
        created_on=datetime.now(),
        updated_on=datetime.now(),
        user_id=user
    )
    item = ListItem.objects.create(
        list=todo_list,
        item_name="Priority Item",
        item_text="Check priority",
        created_on=datetime.now(),
        finished_on=datetime.now(),
        due_date=date.today(),
        priority="HIGH"
    )
    assert item.priority == "HIGH"


@pytest.mark.django_db
def test_template_item_tag_color():
    user = UserFactory()
    template = Template.objects.create(
        title_text="Colored Template",
        created_on=datetime.now(),
        updated_on=datetime.now(),
        user_id=user
    )
    item = TemplateItem.objects.create(
        template=template,
        item_text="Colored Item",
        created_on=datetime.now(),
        finished_on=datetime.now(),
        due_date=date.today(),
        tag_color="#123ABC"
    )
    assert item.tag_color == "#123ABC"


@pytest.mark.django_db
def test_list_item_tags_field():
    user = UserFactory()
    todo_list = List.objects.create(
        title_text="Tagged List",
        created_on=datetime.now(),
        updated_on=datetime.now(),
        user_id=user
    )
    item = ListItem.objects.create(
        list=todo_list,
        item_name="Tagged Item",
        item_text="Test JSON tags",
        created_on=datetime.now(),
        finished_on=datetime.now(),
        due_date=date.today(),
        tags=["urgent", "work"]
    )
    assert item.tags == ["urgent", "work"]


@pytest.mark.django_db
def test_list_is_shared_default():
    todo_list = List.objects.create(
        title_text="Shared Status",
        created_on=datetime.now(),
        updated_on=datetime.now()
    )
    assert todo_list.is_shared is False


@pytest.mark.django_db
def test_list_tags_optional_fields():
    tag = ListTags.objects.create(
        tag_name="Optional Tag",
        created_on=datetime.now()
    )
    assert tag.user_id is None


@pytest.mark.django_db
def test_shared_list_optional_user():
    shared_list = SharedList.objects.create(
        shared_list_id="12345"
    )
    assert shared_list.user is None


@pytest.mark.django_db
def test_list_item_is_done_default():
    user = UserFactory()
    todo_list = List.objects.create(
        title_text="Done Status",
        created_on=datetime.now(),
        updated_on=datetime.now(),
        user_id=user
    )
    item = ListItem.objects.create(
        list=todo_list,
        item_text="Check is_done default",
        created_on=datetime.now(),
        finished_on=datetime.now(),
        due_date=date.today()
    )
    assert item.is_done is False


@pytest.mark.django_db
def test_template_str_representation():
    user = UserFactory()
    template = Template.objects.create(
        title_text="Test Template Representation",
        created_on=datetime.now(),
        updated_on=datetime.now(),
        user_id=user
    )
    assert str(template) == "Test Template Representation"


@pytest.mark.django_db
def test_shared_users_str_representation():
    user = UserFactory()
    todo_list = List.objects.create(
        title_text="Another Shared List",
        created_on=datetime.now(),
        updated_on=datetime.now(),
        user_id=user
    )
    shared_user = SharedUsers.objects.create(
        list_id=todo_list,
        shared_user="anotheruser@example.com"
    )
    assert str(shared_user) == str(todo_list.id)


@pytest.mark.django_db
def test_list_tags_str_representation():
    tag = ListTags.objects.create(
        tag_name="Important Tag",
        created_on=datetime.now()
    )
    assert str(tag) == "Important Tag"


@pytest.mark.django_db
def test_list_with_no_user():
    todo_list = List.objects.create(
        title_text="No User List",
        created_on=datetime.now(),
        updated_on=datetime.now()
    )
    assert todo_list.user_id is None


@pytest.mark.django_db
def test_shared_users_email_format():
    todo_list = List.objects.create(
        title_text="Email Shared List",
        created_on=datetime.now(),
        updated_on=datetime.now()
    )
    shared_user = SharedUsers.objects.create(
        list_id=todo_list,
        shared_user="validemail@example.com"
    )
    assert "@" in shared_user.shared_user
