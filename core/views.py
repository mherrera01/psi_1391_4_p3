from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from core.forms import LabGroupForm, PairForm, LoginForm, BreakPairForm
from core.models import (Student, Pair, OtherConstraints,
                         LabGroup, GroupConstraints)
import datetime

OK_GROUP_JOINED = 0
ERROR_GROUP_CANT_JOIN = 1
ERROR_GROUP_FULL_PARTNER = 2
ERROR_GROUP_FULL = 3

LAB_GROUP_FORM_CACHE = {}


def home(request):
    """
    The landing page for most requests and the index page, which displays
    a brief summary for the user to see, displaying on his browser information
    such as what Theory Group he's in, what Lab Group he's assigned to, his
    pair, etc.
    Author: Miguel Herrera Martinez

    :param request: The user's HttpRequest object, which contains data about
    the user
    :type request: django.http.HttpRequest
    :return: The rendered HTML of the home page, according to his data
    :rtype: django.http.HttpResponse
    """
    context_dict = {}
    if request.user.is_authenticated and not request.user.is_superuser:
        stu = Student.from_user(request.user)
        context_dict['student'] = stu
        pair = Pair.get_pair(stu)
        if pair:
            context_dict['pair'] = pair
        else:
            context_dict['pairs'] = Pair.objects.filter(student2=stu)
    if 'home_msg' in request.session:
        context_dict['msg'] = request.session['home_msg'][0]
        context_dict['isError'] = request.session['home_msg'][1]
        request.session.pop('home_msg')
    return render(request, 'core/home.html', context_dict)


def student_login(request):
    """
    The login page, rendered only if you're not logged in.
    =======================================================
    Author: Miguel Herrera Martinez
    If you're not logged in:
    * A ``GET`` request (*i.e.: opening the page*) will render the login page
    * A ``POST`` will verify if your credentials are valid:
      * If they are, you will be logged in and sent to :meth:`core.views.home`
      * If they are invalid, you will be sent back to the `login` page with an
      error message

    If you're logged in:
    * Any HttpRequest will redirect you back to :meth:`core.views.home`


    :param request: The user's HttpRequest object, which contains data about
    the user
    :type request: django.http.HttpRequest
    :return: The rendered Login page, or the rendered :meth:`core.views.home`
    page
    :rtype: django.http.HttpResponse
    """
    context_dict = {}
    if request.user.is_authenticated:
        request.session['home_msg'] = ["You're already logged in.", True]
        return redirect(reverse('home'))

    context_dict['loginForm'] = LoginForm()
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        context_dict['loginForm'].set_NIE(username)

        user = authenticate(username=username, password=password)

        if user:
            # Log-in the user (we won't disable/ban users)
            login(request, user)
            return redirect(reverse('home'))

        else:
            # Don't log-in if the user's credentials are invalid
            context_dict['msg'] = "Invalid login details. Please, Make sure"\
                + " you are using the correct DNI and NIE."
            context_dict['isError'] = True

    return render(request, 'core/login.html', context_dict)


def student_logout(request):
    """Logs-out an user only if he's authenticated. If he's not, it will just
    show an error message to the user.
    Author: Miguel Herrera Martinez

    :param request: The user's HttpRequest object, which contains data about
    the user
    :type request: django.http.HttpRequest
    :return: The rendered :meth:`core.views.home` page (since he'll be
    redirected to it)
    :rtype: django.http.HttpResponse
    """
    if request.user.is_authenticated:
        logout(request)
    return redirect(reverse('home'))


@login_required
def convalidation(request):
    """
    The convalidation page, where you may skip the practices.
    =======================================================================
    Author: Miguel Herrera Martinez
    It processes a convalidation request by just opening the page, and
    tells the user if he's eligible for convalidation or if he isn't.

    It will also display the requirements to have your practices convalidated

    .. warning::
       Requires being logged in via :meth:`core.views.login`.

    :param request: The user's HttpRequest object, which contains data about
    the user
    :type request: django.http.HttpRequest
    :return: The rendered convalidation page, with the necessary info
    :rtype: django.http.HttpResponse
    """
    context_dict = {}
    oc = OtherConstraints.objects.first()
    stu = Student.from_user(request.user)

    # add the grade variables, used to print
    context_dict['lab_min_grade'] = oc.minGradeLabConv
    context_dict['theory_min_grade'] = oc.minGradeTheoryConv
    context_dict['lab_student_grade'] = stu.gradeLabLastYear
    context_dict['theory_student_grade'] = stu.gradeTheoryLastYear

    # update the convalidation variable if he meets the basic
    # conditions: grades higher than constraints,
    # and the user didn't select a group
    stu.convalidationGranted = stu.gradeLabLastYear > oc.minGradeLabConv\
        and stu.gradeTheoryLastYear > oc.minGradeTheoryConv
    if not stu.convalidationGranted:
        context_dict['why_not_conv'] = "Your last year grades don't meet " + \
            "the requirements!"
    elif stu.labGroup is not None:
        context_dict['why_not_conv'] = "You're already in a group!"
        stu.convalidationGranted = False

    if stu.convalidationGranted:
        # do not convalidate if user has a validated pair
        # or they are the first member of their pair
        p = Pair.get_pair(stu)
        if p is not None:
            if p.validated or p.student1 == stu:
                context_dict['why_not_conv'] = "You're in a validated " + \
                    "pair, or you requested a pair!"
                stu.convalidationGranted = False

    stu.save()
    context_dict['convalidated'] = stu.convalidationGranted

    return render(request, 'core/convalidation.html', context_dict)


@login_required
def applypair(request):
    """
    The Apply Pair page.
    =======================
    Author: Jorge González Gómez
    Rendered as a list where you may select a pair by sending the form as a
    `POST` request or else info about your pair, if you already have one.

    .. note::
       If you try sending a POST request manually using external tools (or
       your own browser) it will get rejected if you already had one.

    :param request: The user's HttpRequest object, which contains data about
    the user
    :type request: django.http.HttpRequest
    :return: The rendered Apply Pair page, with the necessary info
    :rtype: django.http.HttpResponse
    """
    context_dict = {}
    # If he sent an Apply Pair request...
    s = Student.from_user(request.user)
    context_dict['students'] = PairForm(s)
    # To be used in the future, defined to prevent a second useless querie.
    pair = None
    if request.method == "POST":
        # Validate the request (in case he wants to exploit a vulnerability)
        if 'student2' not in request.POST:
            context_dict['msg'] = "Missing \"student2\" in POST request." +\
                "<br\\>Please, don't use a custom client " +\
                "to send modified requests."
            context_dict['isError'] = True
            return render(request, 'core/applypair.html', context_dict)

        try:
            # The student2 is given by the POST request
            student2 = Student.objects.get(id=request.POST['student2'])

            # Constructor will be later used
            pair = Pair(student1=s, student2=student2)

            # Try saving the pair, and check the returned variable
            # since Python overrides allow changing the return
            # type from None to any other type
            status = pair.save()
            if status == Pair.OK:
                # If the pair was created/validated, print
                # an OK message in the home page
                request.session['home_msg'] = ['Pair succesfully %s!' %
                                               ("validated" if pair.validated
                                                else "created"),
                                               False]
                return redirect(reverse('home'))
            else:
                # If the status is not OK, send the message through an
                # error but don't redirect to other page
                context_dict['msg'] = "You already have a pair"\
                    if status == Pair.YOU_HAVE_PAIR\
                    else "The requested user has already selected a pair"
                context_dict['isError'] = True

        except Student.DoesNotExist:
            # If student2 doesn't exist, print it (invalid form)
            context_dict['msg'] = "Student with ID " +\
                f"{request.POST['student2']} does not exist."
            context_dict['isError'] = True

    # GET, or else a "continue" from our POST method
    # 'pair' is our previously defined variable, try fetching
    # it if it's a None object
    if not pair:
        pair = Pair.get_pair(s)
    # If there's a pair, render it properly
    if pair:
        if pair.validated or pair.student1.id == s.id:
            context_dict['pair'] = pair
    return render(request, 'core/applypair.html', context_dict)


# Used in applygroup and groupchange
def change_students_group(stu, lg, context_dict):
    # Check if the requested group exist, and add the
    # user to this group.

    # Get the constraints for this group, if there's any
    canJoin = GroupConstraints.objects.filter(
        theoryGroup=stu.theoryGroup,
        labGroup=lg).exists()
    if canJoin is False:
        context_dict['msg'] = ""
        context_dict['isError'] = True
        # Render the groups, since there's been an error
        context_dict['groups'] = LabGroupForm(stu)
        return ERROR_GROUP_CANT_JOIN

    # Check if his pair *can* be with him too
    pair = Pair.get_pair(stu)
    joinWithPair = False
    if pair:
        joinWithPair = pair.validated
    if joinWithPair:
        fren = pair.student2 if stu == pair.student1\
            else pair.student1
        skipCounterCheck = False
        # First, check if our student is in another group
        if fren.labGroup:
            if fren.labGroup == lg:
                # mark this as true if he's inside
                # our Lab Group already
                skipCounterCheck = True

        # Second, check if there's enough space
        if not skipCounterCheck and lg.counter + 2 > lg.maxNumberStudents\
                and fren.labGroup:
            # They can't join this group...
            # to avoid weird errors, just disallow both
            return ERROR_GROUP_FULL_PARTNER
        # Thirdly, if there is space and he's not on our group,
        # add him without an error
        if not skipCounterCheck and fren.labGroup:
            # But first, remove it from his group if it's not
            # out desired group
            if fren.labGroup != lg:
                # Change groups
                fren.labGroup.remove_student(fren)
        # Finally, add it to his new group.
        lg.add_student(fren)

    # If our student had a group, remove
    # it from the old group
    if stu.labGroup:
        stu.labGroup.remove_student(stu)
    # Assign the group and give him a nice message
    added = lg.add_student(stu)
    if not added:
        return ERROR_GROUP_FULL


@login_required
def applygroup(request):
    """
    The Apply Group page.
    =======================
    Author: Jorge González Gómez
    Rendered as a list where you may select a group by sending the form as a
    `POST` request, or else info about your group, if you already have one.

    .. note::
       It will only display the valid groups to you, based on the
       :class:`core.models.GroupConstraints`
       that reference your :class:`core.models.TheoryGroup`

    :param request: The user's HttpRequest object, which contains data about
    the user
    :type request: django.http.HttpRequest
    :return: The rendered Apply Group page, with the necessary info
    :rtype: django.http.HttpResponse
    """
    context_dict = {}
    stu = Student.from_user(request.user)

    # The student already has a lab group
    # No need to compute the groups
    try:
        now = datetime.datetime.now()
        now = timezone.make_aware(now, timezone.get_current_timezone())
        if OtherConstraints.objects.first().selectGroupStartDate > now:
            context_dict['not_active'] = True
            return render(request, 'core/applygroup.html', context_dict)
    except OtherConstraints.DoesNotExist:
        pass
    # The student selects a lab group
    if request.method == 'POST':
        try:
            lg = LabGroup.objects.get(id=request.POST['labGroup'])
            message_switch = {
                ERROR_GROUP_CANT_JOIN: "Members of the theory group " +
                                       f"{stu.theoryGroup} can't join {lg}",
                ERROR_GROUP_FULL_PARTNER: "This group is full!" +
                                          "You can't join with your partner",
                ERROR_GROUP_FULL: lg.groupName + " is FULL! " +
                                                 "You can't join this group."
            }
            # Check the error message right after calling the function
            message = change_students_group(stu, lg, context_dict)
            if message == OK_GROUP_JOINED:
                request.session['home_msg'] = [str(lg.groupName) +
                                               " has been assigned as " +
                                               "your Lab group.",
                                               False]
                redirect(reverse('home'))
            # If there's a message, it's an error.
            if message in message_switch:
                context_dict['msg'] = message_switch[message]
                context_dict['isError'] = True
        except LabGroup.DoesNotExist:
            # If it doesn't exist, return an error message
            context_dict['msg'] = request.POST['labGroup'] + " does not exist."
            context_dict['isError'] = True
            # Don't return anything, just continue as if it was a regular GET

    # Compute and render the groups if you reach the end of the function
    context_dict['groups'] = LabGroupForm(stu)

    return render(request, 'core/applygroup.html', context_dict)


@login_required
def breakpair(request):
    """
    The Break Pair page.
    =======================
    Author: Jorge González Gómez
    Rendered as a list where you may select a pair by sending the form as a
    `POST` request or else info about your pair, if you already have one.

    .. note::
       If you try sending a POST request manually using external tools (or
       your own browser) it will get rejected if you already had one.

    :param request: The user's HttpRequest object, which contains data about
    the user
    :type request: django.http.HttpRequest
    :return: The rendered Apply Pair page, with the necessary info
    :rtype: django.http.HttpResponse
    """
    context_dict = {}
    stu = Student.from_user(request.user)

    context_dict['pairs'] = BreakPairForm(stu)
    # The student selected the pair to be broken
    if request.method == 'POST':
        # The pair is sent through here
        myPair = request.POST['myPair']
        pair = None
        try:
            pair = Pair.objects.get(id=myPair)
        except Pair.DoesNotExist:
            context_dict['msg'] = "You cannot break a pair " +\
                "that does not exist"
            context_dict['isError'] = True
            return render(request, 'core/breakpair.html', context_dict)

        if pair.student1 != stu and pair.student2 != stu:
            context_dict['msg'] = "You cannot break a pair of which " +\
                "you are not a member"
            context_dict['isError'] = True
            return render(request, 'core/breakpair.html', context_dict)

        pair.break_pair(stu)

    return render(request, 'core/breakpair.html', context_dict)


@user_passes_test(lambda u: u.is_superuser)
def groups(request):
    """The "groups" view, exclusive to superusers.
    Author: Jorge Gonzalez Gomez

    :param request: The user's HttpRequest object, which contains data about
    the user
    :type request: django.http.HttpRequest
    :return: The rendered Apply Pair page, with the necessary info
    :rtype: django.http.HttpResponse
    """
    context_dict = {}

    # Message required if a group does not exist
    if 'groups_msg' in request.session:
        context_dict['msg'] = request.session['groups_msg'][0]
        context_dict['isError'] = request.session['groups_msg'][1]
        request.session.pop('groups_msg')

    # Fetch all the laboratory groups available to show
    context_dict['groups'] = LabGroup.objects.all()

    return render(request, 'core/groups.html', context_dict)


@user_passes_test(lambda u: u.is_superuser)
def group(request, group_name_slug):
    """The single group view, which displays info for a specific group
    Author: Jorge Gonzalez Gomez

    :param request: The user's HttpRequest object, which contains data about
    the user
    :type request: django.http.HttpRequest
    :param group_name_slug: The "slug" version of a group name, which is
    displayed in the browser bar
    :type group_name_slug: str
    :return: The rendered Apply Pair page, with the necessary info
    :rtype: django.http.HttpResponse
    """
    # Get the group and the students from the group slug
    try:
        context_dict = {}
        group = LabGroup.objects.get(slug=group_name_slug)
        context_dict['g'] = group

        students = Student.objects.filter(labGroup=group)
        context_dict['students'] = students
        return render(request, 'core/group.html', context_dict)
    except LabGroup.DoesNotExist:
        request.session['groups_msg'] = ["This group does not exist.", True]
        return redirect(reverse('groups'))


@user_passes_test(lambda u: u.is_superuser)
def groupchange(request):
    """The group change view, which displays a list of all the students
    and lets the superuser change their groups
    Author: Miguel Herrera Martinez

    :param request: The user's HttpRequest object, which contains data about
    the user
    :type request: django.http.HttpRequest
    :return: The rendered Apply Pair page, with the necessary info
    :rtype: django.http.HttpResponse
    """
    context_dict = {}
    if request.method == 'POST':
        try:
            lg = LabGroup.objects.get(id=request.POST['labGroup'])
            stu = Student.objects.get(id=request.POST['student'])
            message_switch = {
                ERROR_GROUP_FULL_PARTNER: "This group is full!" +
                                          "The user can't join with " +
                                          "his partner",
                ERROR_GROUP_FULL: lg.groupName + " is FULL! " +
                "The user can't join this group."
            }
            # Check the error message right after calling the function
            message = change_students_group(stu, lg, context_dict)
            if message == OK_GROUP_JOINED:
                request.session['home_msg'] = [str(lg.groupName) +
                                               " has been assigned as " +
                                               "your Lab group.",
                                               False]
                redirect(reverse('home'))
            # If there's a message, it's an error.
            if message in message_switch:
                context_dict['msg'] = message_switch[message]
                context_dict['isError'] = True
        except LabGroup.DoesNotExist:
            # If it doesn't exist, return an error message
            context_dict['msg'] = request.POST['labGroup'] + " does not exist."
            context_dict['isError'] = True
            # Don't return anything, just continue as if it was a regular GET
        except Student.DoesNotExist:
            context_dict['msg'] = request.POST['student'] + " does not exist."
            context_dict['isError'] = True

    student_from_dict = []
    for student in Student.objects.exclude(is_superuser=True):
        lgForm = None
        if student in LAB_GROUP_FORM_CACHE:
            lgForm = LAB_GROUP_FORM_CACHE[student]
        else:
            lgForm = LabGroupForm(student)
        student_from_dict.append([student, lgForm])
    context_dict['students'] = student_from_dict

    return render(request, 'core/groupchange.html', context_dict)
