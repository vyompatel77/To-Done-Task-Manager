# MIT License

# Copyright 2024 Akarsh Reddy Eathamukkala

# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the “Software”), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to
# do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.

from django.urls import path
from . import views

app_name = "todo"


# Urls for to-done app
urlpatterns = [
    path('', views.index, name='index'),
    path('todo', views.index, name='todo'),
    path('todo/<int:list_id>', views.index, name='todo_list_id'),
    path('config_hook/<path:template_str>/',
         views.config_hook, name='config_hook'),
    path('todo/new-from-template', views.todo_from_template,
         name='todo_from_template'),
    path('delete-todo', views.delete_todo, name='delete_todo'),
    path('templates', views.template, name='template'),
    path('templates/<int:template_id>', views.template, name='template'),
    path('templates/new-from-todo', views.template_from_todo,
         name='template_from_todo'),
    path('updateListItem', views.updateListItem, name='updateListItem'),
    path('removeListItem', views.removeListItem, name='removeListItem'),
    path('createNewTodoList', views.createNewTodoList, name='createNewTodoList'),
    path('getListItemByName', views.getListItemByName, name='getListItemByName'),
    path('getListItemById', views.getListItemById, name='getListItemById'),
    path('markListItem', views.markListItem, name='markListItem'),
    path('addNewListItem', views.addNewListItem, name='addNewListItem'),
    path('updateListItem/<int:item_id>',
         views.updateListItem, name='updateListItem'),
    path("register", views.register_request, name="register"),
    path("login", views.login_request, name="login"),
    path("social_login", views.social_login, name="social_login"),
    path("logout", views.logout_request, name="logout"),
    path("password_reset", views.password_reset_request, name="password_reset"),
    path('templates/delete/<int:template_id>',
         views.delete_template, name='delete_template'),
    path('todo/filter', views.filter_lists, name='filter_lists'),
    path('todo/export_todo_csv', views.export_todo_csv, name='export_todo_csv'),
    path('todo/import_todo_csv', views.import_todo_csv, name='import_todo_csv'),
    path('todo/tags', views.get_tags_from_all_tasks, name='get_tags'),
]
