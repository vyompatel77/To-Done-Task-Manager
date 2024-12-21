
import datetime
import json

from django.shortcuts import render, redirect, get_object_or_404, get_list_or_404
from django.http import HttpResponse, JsonResponse, Http404, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction, IntegrityError
from django.utils import timezone
from django.views.decorators.http import require_POST

from todo.models import List, ListItem, Template, TemplateItem, ListTags, SharedUsers, SharedList

from todo.forms import NewUserForm
from django.conf import settings
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.core.mail import send_mail, BadHeaderError
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.db.models.query_utils import Q
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.core.mail import EmailMessage
from google.oauth2 import id_token
from google.auth.transport import requests


import csv
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from .models import List, ListItem


# import csv
# from django.shortcuts import render, redirect
# from django.http import HttpResponseRedirect
# from django.urls import reverse
# from .models import List, ListItem
# from django.contrib import messages

from dateutil import parser

config = {
    "darkMode": False,
    "primary_color": '#0fa662',
    "hover_color": "#0b8f54",
    "background_color": "#ffffff",
    "text_color": "#000000",
    "side_nav": "#ddd",
    "header_color": "#0fa662"
}


def config_hook(request, template_str):
    config["darkMode"] = not config["darkMode"]
    if config["darkMode"]:
        config["primary_color"] = '#000000'
        config["hover_color"] = '#cccccc'
        config["background_color"] = "#171515"
        config["text_color"] = "#ffffff"
        config["side_nav"] = "#373535"
        config["header_color"] = "#ffffff"

    else:
        config["primary_color"] = '#0fa662'
        config["hover_color"] = '#0b8f54'
        config["background_color"] = "#ffffff"
        config["text_color"] = "#000000"
        config["side_nav"] = "#ddd"
        config["header_color"] = "#0fa662"

    return redirect('todo:' + template_str)

# Render the home page with users' to-do lists


def index(request, list_id=None):
    if not request.user.is_authenticated:
        return redirect("todo:login")

    # Get filter parameters
    due_date = request.GET.get('due_date')
    priority = request.GET.get('priority')

    # Get user's lists and shared lists
    if list_id:
        latest_lists = List.objects.filter(id=list_id)
    else:
        latest_lists = List.objects.filter(
            user_id_id=request.user.id).order_by('-updated_on')

    shared_list = []
    try:
        query_list_str = SharedList.objects.get(
            user_id=request.user.id).shared_list_id
        if query_list_str:
            shared_list_id = query_list_str.split(" ")
            shared_list_id.remove("")
            for list_id in shared_list_id:
                try:
                    query_list = List.objects.get(id=int(list_id))
                    shared_list.append(query_list)
                except List.DoesNotExist:
                    continue
    except SharedList.DoesNotExist:
        pass

    # Get all list items and assign them to their respective lists
    for todo_list in latest_lists:
        items = todo_list.listitem_set.all()
        if due_date or priority:
            if due_date:
                items = items.filter(due_date__lte=due_date)
            if priority:
                items = items.filter(priority=priority)
        todo_list.items = items

    # Filter out lists with no matching items when filters are applied
    if due_date or priority:
        latest_lists = [lst for lst in latest_lists if lst.items.exists()]

    # Apply due date coloring
    cur_date = datetime.date.today()
    for todo_list in latest_lists:
        for item in todo_list.items:
            if item.due_date:
                if item.is_done:
                    item.color = "#808080"  # Gray for completed items
                elif item.due_date < cur_date:
                    item.color = "#FF0000"  # Red for overdue items
                else:
                    item.color = "#000000"  # Black for normal items
            else:
                item.color = "#000000"

    # Get templates and tags
    saved_templates = Template.objects.filter(
        user_id_id=request.user.id).order_by('created_on')
    list_tags = ListTags.objects.filter(
        user_id=request.user.id).order_by('created_on')

    context = {
        "latest_lists": latest_lists,
        "templates": saved_templates,
        "list_tags": list_tags,
        "shared_list": shared_list,
        "selected_list": list_id,
        "current_filters": {
            "due_date": due_date if due_date else "",
            "priority": priority if priority else ""
        },
        "user_name": request.user.first_name if request.user.first_name else request.user.username,
        'config': config
    }

    return render(request, "todo/index.html", context)

# Create a new to-do list from templates and redirect to the to-do list homepage


def todo_from_template(request):
    """
    Creates a new to-do list from a selected template.

    This view function is invoked when a user wants to create a new to-do list based on an existing template.
    It first checks if the user is authenticated. If not, it redirects them to the login page. If the user
    is authenticated, it fetches the specified template, creates a new to-do list with the template's title,
    and then populates the new list with items defined in the template.

    Args:
        request: The HTTP request object containing the user's input data.

    Returns:
        HttpResponse: A redirect to the to-do page after successfully creating the new list and its items.

    Raises:
        Http404: If the specified template does not exist, a 404 error is raised.
    """
    if not request.user.is_authenticated:
        return redirect("/login")
    template_id = request.POST['template']
    fetched_template = get_object_or_404(Template, pk=template_id)
    todo = List.objects.create(
        title_text=fetched_template.title_text,
        created_on=datetime.datetime.now(),
        updated_on=datetime.datetime.now(),
        user_id_id=request.user.id
    )
    for template_item in fetched_template.templateitem_set.all():
        ListItem.objects.create(
            item_name=template_item.item_text,
            item_text="",
            created_on=datetime.datetime.now(),
            finished_on=datetime.datetime.now(),
            due_date=datetime.datetime.now(),
            tag_color=template_item.tag_color,
            list=todo,
            is_done=False,
        )
    return redirect("/todo")


# Create a new Template from existing to-do list and redirect to the templates list page
def template_from_todo(request):

    if not request.user.is_authenticated:
        return redirect("/login")
    todo_id = request.POST['todo']
    fetched_todo = get_object_or_404(List, pk=todo_id)
    new_template = Template.objects.create(
        title_text=fetched_todo.title_text,
        created_on=datetime.datetime.now(),
        updated_on=datetime.datetime.now(),
        user_id_id=request.user.id
    )
    for todo_item in fetched_todo.listitem_set.all():
        TemplateItem.objects.create(
            item_text=todo_item.item_name,
            created_on=datetime.datetime.now(),
            finished_on=datetime.datetime.now(),
            due_date=datetime.datetime.now(),
            tag_color=todo_item.tag_color,
            template=new_template
        )
    return redirect("/templates")


# Delete a to-do list
def delete_todo(request):
    """
    Deletes a specified to-do item.

    This view function is invoked when a user wants to delete a to-do item. 
    It first checks if the user is authenticated; if not, it redirects them to the login page. 
    If the user is authenticated, it retrieves the specified to-do item by its ID and deletes it.

    Args:
        request: The HTTP request object containing the user's input data.

    Returns:
        HttpResponse: A redirect to the to-do page after successfully deleting the specified to-do item.

    Raises:
        Http404: If the specified to-do item does not exist, a 404 error is raised.
    """
    if not request.user.is_authenticated:
        return redirect("/login")
    todo_id = request.POST['todo']
    fetched_todo = get_object_or_404(List, pk=todo_id)
    fetched_todo.delete()
    return redirect("/todo")


# Render the template list page
def template(request, template_id=0):
    """
    Retrieves and displays saved templates for the authenticated user.

    This view function is invoked to render a list of saved templates. It first checks if the user is 
    authenticated; if not, it redirects them to the login page. If a template ID is provided, it fetches
    that specific template; otherwise, it retrieves all templates created by the authenticated user,
    ordered by creation date.

    Args:
        request: The HTTP request object containing the user's input data.
        template_id (int, optional): The ID of the template to retrieve. Defaults to 0.

    Returns:
        HttpResponse: Renders the template page with the list of saved templates.
    """
    if not request.user.is_authenticated:
        return redirect("/login")
    if template_id != 0:
        saved_templates = Template.objects.filter(id=template_id)
    else:
        saved_templates = Template.objects.filter(
            user_id_id=request.user.id).order_by('created_on')
    context = {
        'templates': saved_templates,
        'config': config
    }
    return render(request, 'todo/template.html', context)


# Remove a to-do list item, called by javascript function
@csrf_exempt
def removeListItem(request):
    """
    Removes a to-do list item based on the provided list item ID.

    This view function is invoked via a JavaScript call to remove a specified item from a to-do list. 
    It checks if the user is authenticated; if not, it redirects them to the login page. Upon receiving a 
    POST request, it decodes the JSON body to retrieve the list item ID and attempts to delete the corresponding 
    ListItem from the database. If an integrity error occurs during the deletion, it logs the error message.

    Args:
        request: The HTTP request object containing the user's input data.

    Returns:
        HttpResponse: A redirect to the to-do page after successfully removing the specified list item.

    Raises:
        IntegrityError: If there is a database integrity error while trying to delete the list item.
    """
    if not request.user.is_authenticated:
        return redirect("/login")
    if request.method == 'POST':
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)
        list_item_id = body['list_item_id']
        try:
            with transaction.atomic():
                being_removed_item = ListItem.objects.get(id=list_item_id)
                being_removed_item.delete()
        except IntegrityError as e:
            print(str(e))
            print("unknown error occurs when trying to update todo list item text")
        return redirect("/todo")
    else:
        return redirect("/todo")

# Update a to-do list item, called by javascript function


@csrf_exempt
def updateListItem(request, item_id):
    """
    Update a list item's details including title, note, due date, and completion status.

    Args:
        request: The HTTP request object
        item_id: The ID of the list item to update

    Returns:
        JsonResponse: Contains the updated item details if successful, or error message if failed
    """
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            list_item = ListItem.objects.get(id=item_id)

            # Update fields if they are provided in the request
            if 'title' in body:
                list_item.item_name = body['title']
            if 'note' in body:
                list_item.item_text = body['note']
            if 'due_date' in body:
                try:
                    if body['due_date']:
                        # Parse the date and set it to midnight in the current timezone
                        date_only = datetime.datetime.strptime(
                            body['due_date'], '%Y-%m-%d')
                        list_item.due_date = date_only.date()  # Only store the date part
                    else:
                        # If no due date is provided, set it to a far future date
                        list_item.due_date = datetime.date(2099, 12, 31)
                except (ValueError, TypeError):
                    return JsonResponse({'error': 'Invalid date format'}, status=400)
            if 'is_done' in body:
                list_item.is_done = body['is_done']
                if body['is_done']:
                    list_item.finished_on = datetime.datetime.now()  # Use naive datetime
                else:
                    # If task is not done, set finished_on to a far future date
                    list_item.finished_on = datetime.datetime(
                        2099, 12, 31)  # Use naive datetime
            if 'priority' in body:
                if body['priority'] in ['HIGH', 'MEDIUM', 'LOW']:
                    list_item.priority = body['priority']
                else:
                    return JsonResponse({'error': 'Invalid priority level'}, status=400)

            # Ensure tag_color has a value
            if not list_item.tag_color:
                list_item.tag_color = '#000000'  # Default to black

            list_item.save()
            # Return the updated item details
            return JsonResponse({
                'id': list_item.id,
                'title': list_item.item_name,
                'note': list_item.item_text,
                'due_date': list_item.due_date.isoformat() if list_item.due_date else None,
                'is_done': list_item.is_done,
                'finished_on': list_item.finished_on.isoformat() if list_item.finished_on else None,
                'created_on': list_item.created_on.isoformat(),
                'priority': list_item.priority
            })

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        except ListItem.DoesNotExist:
            return JsonResponse({'error': 'List item not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Only POST method is allowed'}, status=405)


# Add a new to-do list item, called by javascript function
@csrf_exempt
def addNewListItem(request):
    """
    Adds a new to-do list item based on the provided data.

    This view function is invoked to create a new to-do list item. It checks if the user is authenticated;
    if not, it redirects them to the login page. On receiving a POST request, it decodes the JSON body to 
    retrieve the list item details and creates a new ListItem object. If an IntegrityError occurs during 
    the creation process, it logs the error and returns an item ID of -1.

    Args:
        request: The HTTP request object containing the user's input data.

    Returns:
        JsonResponse: Contains the ID of the newly created item or -1 in case of failure.
    """
    if not request.user.is_authenticated:
        return redirect("/login")
    if request.method == 'POST':
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)
        list_id = body['list_id']
        item_name = body['list_item_name']
        # Get note text, default to empty string
        item_text = body.get('item_text', '')
        create_on_time = datetime.datetime.now()
        finished_on_time = create_on_time
        due_date = body['due_date']
        # Default to MEDIUM if not provided
        priority = body.get('priority', 'MEDIUM')
        tags = []

        # Process tags if provided
        if 'tags' in body and body['tags']:
            # Split by comma and strip whitespace
            tags = [tag.strip()
                    for tag in body['tags'].split(',') if tag.strip()]

        # Debug print statements
        print("Received data:")
        print(f"list_id: {list_id}")
        print(f"item_name: {item_name}")
        print(f"item_text: {item_text}")
        print(f"due_date: {due_date}")
        print(f"priority: {priority}")
        print(f"tags: {tags}")

        # Validate priority
        if priority not in ['HIGH', 'MEDIUM', 'LOW']:
            return JsonResponse({'error': 'Invalid priority level', 'item_id': -1})

        print(item_name)
        result_item_id = -1
        # create a new to-do list object and save it to the database
        try:
            with transaction.atomic():
                todo_list_item = ListItem(
                    item_name=item_name,
                    item_text=item_text,
                    created_on=create_on_time,
                    finished_on=finished_on_time,
                    due_date=due_date,
                    list_id=list_id,
                    is_done=False,
                    priority=priority,
                    tags=tags  # Add tags to the item
                )
                todo_list_item.save()
                result_item_id = todo_list_item.id
                print(f"Successfully created item with id: {result_item_id}")
        except IntegrityError as e:
            print(f"IntegrityError: {str(e)}")
            return JsonResponse({'error': str(e), 'item_id': -1})
        except Exception as e:
            print(f"Error: {str(e)}")
            return JsonResponse({'error': str(e), 'item_id': -1})
        # Sending a success response
        return JsonResponse({'item_id': result_item_id})
    else:
        return JsonResponse({'error': 'Only POST method is allowed', 'item_id': -1})


# Mark a to-do list item as done/not done, called by javascript function
@csrf_exempt
def markListItem(request):
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            list_item_id = body['list_item_id']
            is_done = body['is_done']

            with transaction.atomic():
                list_item = ListItem.objects.get(id=list_item_id)
                list_item.is_done = is_done
                list_item.finish_on = datetime.datetime.now() if is_done else None
                list_item.save()

            return JsonResponse({
                'success': True,
                'is_done': list_item.is_done,
                'finish_on': list_item.finish_on.isoformat() if list_item.finish_on else None
            })
        except (KeyError, json.JSONDecodeError) as e:
            return JsonResponse({'success': False, 'error': 'Invalid request data'}, status=400)
        except ListItem.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'List item not found'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    else:
        return JsonResponse({'success': False, 'error': 'Only POST method is allowed'}, status=405)


# Get all the list tags by user id


@csrf_exempt
def getListTagsByUserid(request):
    """
    Retrieves all list tags associated with the authenticated user.

    This view function is called to fetch the list tags created by the authenticated user. It checks 
    if the user is authenticated; if not, it redirects them to the login page. Upon receiving a POST 
    request, it retrieves the user's tags from the database and returns them as a JSON response. 
    If an IntegrityError occurs during the transaction, it logs the error and returns an empty JsonResponse.

    Args:
        request: The HTTP request object containing the user's input data.

    Returns:
        JsonResponse: Contains the list of tags associated with the user or an empty response in case of failure.
    """
    if not request.user.is_authenticated:
        return redirect("/login")
    if request.method == 'POST':
        try:
            with transaction.atomic():
                user_id = request.user.id
                list_tag_list = ListTags.objects.filter(
                    user_id=user_id).values()
                return JsonResponse({'list_tag_list': list(list_tag_list)})
        except IntegrityError:
            print("query list tag by user_id = " + str(user_id) + " failed!")
            JsonResponse({})
    else:
        return JsonResponse({'result': 'get'})  # Sending an success response

# Get a to-do list item by name, called by javascript function


@csrf_exempt
def getListItemByName(request):
    """
    Retrieve a to-do list item by its name.

    This function checks if the user is authenticated, and if so, 
    it processes a POST request to get the item details based on 
    the provided list ID and item name. 

    Args:
        request (HttpRequest): The HTTP request object containing 
                               the user's request data.

    Returns:
        JsonResponse: A JSON response containing the item ID, item 
                      name, list name, and item text if successful, 
                      or a JSON response indicating a failure.
    """
    if not request.user.is_authenticated:
        return redirect("/login")
    if request.method == 'POST':
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)
        list_id = body['list_id']
        list_item_name = body['list_item_name']
        # remove the first " and last "
        # list_item_name = list_item_name

        print("list_id: " + list_id)
        print("list_item_name: " + list_item_name)
        try:
            with transaction.atomic():
                query_list = List.objects.get(id=list_id)
                query_item = ListItem.objects.get(
                    list_id=list_id, item_name=list_item_name)
                # Sending an success response
                return JsonResponse({'item_id': query_item.id, 'item_name': query_item.item_name, 'list_name': query_list.title_text, 'item_text': query_item.item_text})
        except IntegrityError:
            print("query list item" + str(list_item_name) + " failed!")
            JsonResponse({})
    else:
        return JsonResponse({'result': 'get'})  # Sending an success response


# Get a to-do list item by id, called by javascript function
@csrf_exempt
def getListItemById(request):
    """
    Retrieve a to-do list item by its ID.

    This function checks if the user is authenticated and processes 
    a POST request to retrieve the details of a specific item 
    identified by its ID.

    Args:
        request (HttpRequest): The HTTP request object containing 
                               the user's request data.

    Returns:
        JsonResponse: A JSON response containing the item details if successful, 
                     or a JSON response indicating a failure.
    """
    if not request.user.is_authenticated:
        return redirect("/login")
    if request.method == 'POST':
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)
        list_item_id = body['list_item_id']

        try:
            with transaction.atomic():
                item = ListItem.objects.get(id=list_item_id)
                todo_list = List.objects.get(id=item.list_id)

                return JsonResponse({
                    'item_id': item.id,
                    'item_name': item.item_name,
                    'list_name': todo_list.title_text,
                    'item_text': item.item_text,
                    'due_date': item.due_date,
                    'tag_color': item.tag_color
                })
        except (ListItem.DoesNotExist, List.DoesNotExist) as e:
            print(f"Error retrieving item: {str(e)}")
            return JsonResponse({'error': 'Item not found'}, status=404)
        except IntegrityError as e:
            print(f"Database error: {str(e)}")
            return JsonResponse({'error': 'Database error'}, status=500)
    else:
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)


# Create a new to-do list, called by javascript function
@csrf_exempt
def createNewTodoList(request):
    """
    Create a new to-do list.

    This function checks if the user is authenticated and processes 
    a POST request to create a new to-do list with the specified 
    attributes, including sharing it with other users if needed.

    Args:
        request (HttpRequest): The HTTP request object containing 
                               the user's request data.

    Returns:
        HttpResponse: A success response if the list is created 
                      successfully, or an error message if the 
                      request fails or the user is not authenticated.
    """
    if not request.user.is_authenticated:
        return redirect("/login")

    if request.method == 'POST':
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)
        list_name = body['list_title']
        create_on = datetime.datetime.now().timestamp()
        tag_name = body['list_tag']
        shared_user = body.get('shared_user', '')
        user_not_found = []
        print(shared_user)
        create_on_time = datetime.datetime.fromtimestamp(create_on)
        # print(list_name)
        # print(create_on)
        # create a new to-do list object and save it to the database
        try:
            with transaction.atomic():
                user_id = request.user.id
                # print(user_id)
                todo_list = List(user_id_id=user_id, title_text=list_name,
                                 created_on=create_on_time, updated_on=create_on_time, list_tag=tag_name)
                if body.get('create_new_tag', False):
                    # print('new tag')
                    new_tag = ListTags(
                        user_id_id=user_id, tag_name=tag_name, created_on=create_on_time)
                    new_tag.save()

                todo_list.save()
                print(todo_list.id)

                # Progress
                if shared_user:
                    user_list = shared_user.split(' ')

                    k = len(user_list)-1
                    i = 0
                    while i <= k:

                        try:
                            query_user = User.objects.get(
                                username=user_list[i])
                        except User.DoesNotExist:
                            query_user = None

                        if query_user:

                            shared_list_id = SharedList.objects.get(
                                user=query_user).shared_list_id
                            shared_list_id = shared_list_id + \
                                str(todo_list.id) + " "
                            SharedList.objects.filter(user=query_user).update(
                                shared_list_id=shared_list_id)
                            i += 1

                        else:
                            print("No user named " + user_list[i] + " found!")
                            user_not_found.append(user_list[i])
                            user_list.remove(user_list[i])
                            k -= 1

                    shared_user = ' '.join(user_list)
                    new_shared_user = SharedUsers(
                        list_id=todo_list, shared_user=shared_user)
                    new_shared_user.save()

                    print(user_not_found)

                    if user_list:
                        List.objects.filter(
                            id=todo_list.id).update(is_shared=True)

        except IntegrityError as e:
            print(str(e))
            print("unknown error occurs when trying to create and save a new todo list")
            return HttpResponse("Request failed when operating on database")
        # return HttpResponse("Success!")  # Sending an success response
        context = {
            'user_not_found': user_not_found,
        }
        return HttpResponse("Success!")
        # return redirect("index")
    else:
        return HttpResponse("Request method is not a Post")


# Register a new user account
def register_request(request):
    """
    Handles user registration. If the request method is POST, it validates the form data and creates a new user.
    On successful registration, it logs in the user and redirects to the index page. If registration fails, it 
    displays an error message.

    Args:
        request: The HTTP request object.

    Returns:
        HttpResponse: Redirects to the index page or renders the registration form with error messages.
    """
    if request.method == "POST":
        form = NewUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            print(user)

            # Add a empty list to SharedList table
            shared_list = SharedList(user=User.objects.get(
                username=user), shared_list_id="")
            shared_list.save()

            login(request, user)
            messages.success(request, "Registration successful.")
            return redirect("todo:index")
        messages.error(
            request, "Unsuccessful registration. Invalid information.")
    form = NewUserForm()
    return render(request=request, template_name="todo/register.html", context={"register_form": form, 'config': config})

# Social login


@csrf_exempt
def social_login(request):
    """
    Handles social login via Google. This function verifies the token received from Google, retrieves user data, 
    and either logs in an existing user or creates a new user account.

    Args:
        request: The HTTP request object.

    Returns:
        HttpResponse: Redirects to the index page or returns a 403 status on token verification failure.
    """
    token = request.POST.get('credential')

    try:
        # Verify the token with Google's API
        user_data = id_token.verify_oauth2_token(
            token, requests.Request(
            ), "736572233255-usvqanirqiarbk9ffhl6t6tl9br651fn.apps.googleusercontent.com"
        )

        # Extract necessary user information
        email = user_data.get('email')
        first_name = user_data.get('given_name')
        last_name = user_data.get('family_name')

        # Create or retrieve user
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'username': email.split('@')[0],  # Ensure a unique username
                'first_name': first_name,
                'last_name': last_name,
            }
        )

        # Authenticate and log in the user
        if created:
            # Optional: set an unusable password for Google-only login
            user.set_unusable_password()
            user.save()

        # Log the user in
        login(request, user)

        # Optional: Store additional data in session or profile model
        # request.session['profile_picture'] = user_data.get('picture')

        return redirect("todo:index")

    except ValueError as e:
        messages.error(request, e)
        return redirect("todo:index")

# Login a user


def login_request(request):
    """
    Handles user login. If the request method is POST, it validates the login form and authenticates the user.
    On successful authentication, it logs in the user and redirects to the index page. If authentication fails, 
    it displays an error message.

    Args:
        request: The HTTP request object.

    Returns:
        HttpResponse: Redirects to the index page or renders the login form with error messages.
    """
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.info(request, f"You are now logged in as {username}.")
                return redirect("todo:index")
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    form = AuthenticationForm()
    return render(request=request, template_name="todo/login.html", context={"login_form": form, "config": config})


# Logout a user
def logout_request(request):
    """
    Handles user logout. Logs out the user and redirects to the index page with a success message.

    Args:
        request: The HTTP request object.

    Returns:
        HttpResponse: Redirects to the index page with a logout message.
    """
    logout(request)
    messages.info(request, "You have successfully logged out.")
    return redirect("todo:index")


# Reset user password
def password_reset_request(request):
    """
    Handles password reset requests. If the request method is POST, it validates the email and sends a password 
    reset email if the user exists. It renders the password reset form otherwise.

    Args:
        request: The HTTP request object.

    Returns:
        HttpResponse: Renders the password reset form or redirects after sending the email.
    """
    if request.method == "POST":
        password_reset_form = PasswordResetForm(request.POST)
        if password_reset_form.is_valid():
            data = password_reset_form.cleaned_data['email']
            associated_users = User.objects.filter(Q(email=data))
            if associated_users.exists():
                for user in associated_users:
                    subject = "Password Reset Requested"
                    email_template_name = "todo/password/password_reset_email.txt"
                    c = {
                        "email": user.email,
                        'domain': '127.0.0.1:8000',
                        'site_name': 'Website',
                        "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                        "user": user,
                        'token': default_token_generator.make_token(user),
                        'protocol': 'http',
                    }
                    email = render_to_string(email_template_name, c)
                    try:
                        send_email = EmailMessage(
                            subject, email, settings.EMAIL_HOST_USER, [user.email])
                        send_email.fail_silently = False
                        send_email.send()
                    except BadHeaderError:
                        return HttpResponse('Invalid header found')
                    return redirect("/password_reset/done/")
            else:
                messages.error(request, "Not an Email from existing users!")
        else:
            messages.error(request, "Not an Email from existing users!")

    password_reset_form = PasswordResetForm()
    return render(request=request, template_name="todo/password/password_reset.html", context={"password_reset_form": password_reset_form, "config": config})


# Export todo

def export_todo_csv(request):
    # Create the HttpResponse object with CSV headers.
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="todo_lists.csv"'

    # Create a CSV writer object
    writer = csv.writer(response)
    writer.writerow(['List Title', 'Item Name', 'Item Text',
                    'Is Done', 'Created On', 'Due Date'])

    # Fetch data to export
    todo_lists = List.objects.filter(user_id=request.user)
    for todo_list in todo_lists:
        for item in todo_list.listitem_set.all():
            writer.writerow([
                todo_list.title_text,
                item.item_name,
                item.item_text,
                item.is_done,
                item.created_on,
                item.due_date,
            ])
            # item_name=item_name, created_on=create_on_time, finished_on=finished_on_time, due_date=due_date, tag_color=tag_color, list_id=list_id, item_text="", is_done=False

    return response


# Import todo from a csv file

# import csv
# from django.shortcuts import render, redirect
# from django.http import HttpResponseRedirect
# from django.urls import reverse
# from .models import List, ListItem
# from django.contrib import messages
# from datetime import datetime

def import_todo_csv(request):
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        reader = csv.reader(csv_file.read().decode('utf-8').splitlines())
        next(reader)  # Skip the header row

        for row in reader:
            # Assuming CSV format matches [List Title, Item Name, Item Text, Is Done, Created On, Due Date]
            if len(row) < 6:  # Validate row length
                messages.error(
                    request, 'Invalid CSV format. Please check your file.')
                return redirect(reverse('todo:import_todo_csv'))

            list_title, item_name, item_text, is_done, created_on, due_date = row

            # Get or create List by title
            # todo_list, created = List.objects.get_or_create(title_text=list_title)
            todo_list, created = List.objects.get_or_create(title_text=list_title, defaults={
                                                            'created_on': datetime.datetime.now(), 'updated_on': datetime.datetime.now()})

            # Convert string values to proper types
            is_done = is_done.lower() in ['true', '1']
            # created_on = datetime.strptime(created_on, '%Y-%m-%d').date() if created_on else None
            # due_date = datetime.strptime(due_date, '%Y-%m-%d').date() if due_date else None

            created_on = parser.isoparse(created_on)
            due_date = parser.isoparse(due_date) if due_date else None

            # Create the ListItem
            ListItem.objects.create(
                list=todo_list,
                item_name=item_name,
                item_text=item_text,
                is_done=is_done,
                created_on=created_on,
                finished_on=datetime.datetime.now(),
                due_date=due_date,
            )
            # item_name = models.CharField(max_length=50, null=True, blank=True)

        messages.success(request, 'Todos imported successfully!')
        # return HttpResponseRedirect(reverse('todo:home'))

    return redirect("todo:index")

    # return render(request, 'todo/import_csv.html')


# Delete a template


@require_POST
def delete_template(request, template_id):
    """
    Deletes a specified template if the user is authenticated. If the user is not authenticated,
    they are redirected to the login page. If the template exists, it is deleted and the user
    is redirected to the templates list page.

    Args:
        request: The HTTP request object.
        template_id (int): The ID of the template to be deleted.

    Returns:
        HttpResponse: Redirects to the login page if the user is not authenticated, 
                      or redirects to the templates list page after deletion.
    """
    if not request.user.is_authenticated:
        return redirect("/login")
    try:
        template = Template.objects.get(id=template_id)
    except Template.DoesNotExist:
        print("Template doesn't exist!")
    else:
        template.delete()
    return redirect('/templates')


# Filter lists by due date and priority
def filter_lists(request):
    """
    Filter lists and their items based on due date and priority.

    Args:
        request: The HTTP request object containing due_date and priority query parameters

    Returns:
        HttpResponse: Renders the index page with filtered lists and items
    """
    if not request.user.is_authenticated:
        return redirect("/login")

    due_date = request.GET.get('due_date')
    priority = request.GET.get('priority')
    tag = request.GET.get('tag')

    # Get user's lists
    latest_lists = List.objects.filter(
        user_id_id=request.user.id).order_by('-updated_on')
    shared_list = []
    try:
        query_list_str = SharedList.objects.get(
            user_id=request.user.id).shared_list_id
        if query_list_str:
            shared_list_id = query_list_str.split(" ")
            shared_list_id.remove("")
            for list_id in shared_list_id:
                try:
                    query_list = List.objects.get(id=int(list_id))
                    shared_list.append(query_list)
                except List.DoesNotExist:
                    continue
    except SharedList.DoesNotExist:
        pass

    # Filter items based on criteria
    filtered_lists = []
    filtered_items_by_list = {}
    all_lists = list(latest_lists) + shared_list

    for todo_list in all_lists:
        items = list(todo_list.listitem_set.all())
        matching_items = []

        for item in items:
            matches = True

            if priority:
                if item.priority != priority:
                    matches = False
                    continue

            if due_date and due_date.strip():
                try:
                    due_date_obj = datetime.datetime.strptime(
                        due_date, '%Y-%m-%d').date()
                    if item.due_date > due_date_obj:
                        matches = False
                        continue
                except ValueError:
                    pass

            if tag and tag.strip():
                if not item.tags or not isinstance(item.tags, list) or tag not in item.tags:
                    matches = False
                    continue

            if matches:
                matching_items.append(item)

        if matching_items:
            filtered_lists.append(todo_list)
            filtered_items_by_list[todo_list.id] = matching_items

    # Get templates and tags
    saved_templates = Template.objects.filter(
        user_id_id=request.user.id).order_by('created_on')
    list_tags = ListTags.objects.filter(
        user_id=request.user.id).order_by('created_on')

    # Apply due date coloring to matching items
    cur_date = datetime.date.today()
    for items in filtered_items_by_list.values():
        for item in items:
            item.color = "#FF0000" if cur_date > item.due_date else "#000000"

    # Attach filtered items to their lists
    for todo_list in filtered_lists:
        todo_list.items = filtered_items_by_list.get(todo_list.id, [])

    context = {
        'latest_lists': filtered_lists,
        'templates': saved_templates,
        'list_tags': list_tags,
        'shared_list': shared_list,
        'config': config,
        'user': request.user,  # Add the user object to the context
        'current_filters': {
            'due_date': due_date if due_date and due_date.strip() else '',
            'priority': priority if priority else '',
            'tag': tag if tag and tag.strip() else ''
        }
    }

    return render(request, 'todo/index.html', context)


def get_tags_from_all_tasks(request):
    if not request.user.is_authenticated:
        return redirect('/login')

    # Fetch the latest lists and shared lists
    latest_lists = List.objects.filter(
        user_id_id=request.user.id).order_by('-updated_on')
    shared_list = []
    try:
        query_list_str = SharedList.objects.get(
            user_id=request.user.id).shared_list_id
        if query_list_str:
            shared_list_id = query_list_str.split(" ")
            shared_list_id.remove("")
            for list_id in shared_list_id:
                try:
                    query_list = List.objects.get(id=int(list_id))
                    shared_list.append(query_list)
                except List.DoesNotExist:
                    continue
    except SharedList.DoesNotExist:
        pass

    all_lists = list(latest_lists) + shared_list

    # Collect tags from all tasks in these lists
    all_tags = set()  # Use a set to avoid duplicates
    for todo_list in all_lists:
        tasks = todo_list.listitem_set.all()
        for task in tasks:
            if task.tags:
                # Assuming task.tags is a list/array of tags
                all_tags.update(task.tags)

    # Convert the set to a list and sort
    all_tags_list = sorted(list(all_tags))

    # Return as JSON to the frontend
    return JsonResponse({'tags': all_tags_list})
