import re
from decimal import Decimal
import datetime

from django.utils import timezone
from django.test import Client, TestCase
from django.urls import reverse

from core.management.commands.populate import Command
from core.models import (Student, OtherConstraints,
                         Pair, TheoryGroup, GroupConstraints,
                         LabGroup)

###################

# students ids began in this number
# this avoid conflicts with superuser
FIRST_STUDENT_ID = 1000

USERNAME_1 = "testUser_1"
PASSWORD_1 = "pass1"
FIRST_NAME_1 = "user1"
LAST_NAME_1 = "name1"
USERNAME_2 = "testUser_2"
PASSWORD_2 = "pass2"
FIRST_NAME_2 = "user2"
LAST_NAME_2 = "name2"
USERNAME_3 = "testUser_3"
PASSWORD_3 = "pass3"
FIRST_NAME_3 = "user3"
LAST_NAME_3 = "name3"
USERNAME_4 = "testUser_4"
PASSWORD_4 = "pass4"
FIRST_NAME_4 = "user4"
LAST_NAME_4 = "name4"

USER_SESSION_ID = "_auth_user_id"
###################
