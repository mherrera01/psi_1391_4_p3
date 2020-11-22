from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from core.models import (Student, Pair, OtherConstraints,
                         LabGroup, GroupConstraints)
import datetime

HOME_MESSAGE = [None, False]


def home(request):
    context_dict = {}
    if request.user.is_authenticated:
        stu = Student.from_user(request.user)
        context_dict['student'] = stu
        pair = Pair.get_pair(stu)
        context_dict['pair'] = pair
    if 'home_msg' in request.session:
        context_dict['msg'] = request.session['home_msg'][0]
        context_dict['isError'] = request.session['home_msg'][1]
        request.session['msg'] = None
    return render(request, 'core/home.html', context_dict)


def student_login(request):
    context_dict = {}
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(username=username, password=password)

        if user:
            # Check if the user is active
            if user.is_active:
                # Log-in the user
                login(request, user)
                return redirect(reverse('home'))
            else:
                context_dict['msg'] = "This user is disabled"
                context_dict['isError'] = True
                return render(request, 'core/login.html', context_dict)
        else:
            # Bad login details were provided. So we can't log the user in.
            print("Invalid login details: {0}, {1}".format(username, password))
            context_dict['msg'] = "Invalid login details. Please, Make sure"\
                + " you are using the correct DNI and NIE."
            context_dict['isError'] = True
            return render(request, 'core/login.html', context_dict)
    return render(request, 'core/login.html', context_dict)


def student_logout(request):
    if request.user.is_authenticated:
        logout(request)
    return redirect(reverse('home'))


@login_required
def convalidation(request):
    context_dict = {}
    oc = OtherConstraints.objects.first()
    stu = Student.from_user(request.user)

    # add the grade variables, used to print
    context_dict['lab_min_grade'] = oc.minGradeLabConv
    context_dict['theory_min_grade'] = oc.minGradeTheoryConv
    context_dict['lab_student_grade'] = stu.gradeLabLastYear
    context_dict['theory_student_grade'] = stu.gradeTheoryLastYear

    # update the convalidation variable
    p = Pair.get_pair(stu)
    # do not convalidate if user has a validated pair
    # or they are the first member of their pair
    if p is not None and p.validated or p.student1.id == stu.id:
        stu.convalidationGranted = False
    else:
        stu.convalidationGranted = stu.gradeLabLastYear > oc.minGradeLabConv\
            and stu.gradeTheoryLastYear > oc.minGradeTheoryConv

    stu.save()
    context_dict['convalidated'] = stu.convalidationGranted

    return render(request, 'core/convalidation.html', context_dict)


@login_required
def applypair(request):
    context_dict = {}
    # All the students except the currently logged in
    context_dict['students'] = Student.objects\
        .exclude(username=request.user.username)
    # If he sent an Apply Pair request...
    if request.method == "POST":
        # Validate the request (in case he wants to exploit a vulnerability)
        if 'student2' not in request.POST:
            context_dict['msg'] = "Missing \"student2\" in POST request." +\
                "<br\\>Please, don't use a custom client " +\
                "to send modified requests."
            context_dict['isError'] = True
            return render(request, 'core/applypair.html', context_dict)
        if request.POST['student2'] == "":
            context_dict['msg'] = "Please, select an student."
            context_dict['isError'] = True
            return render(request, 'core/applypair.html', context_dict)
        # The student1 is the currently logged user
        student1 = Student.from_user(request.user)
        try:
            # The student2 is given by the POST request
            student2 = Student.objects.get(id=request.POST['student2'])
            # Constructor will be later used
            p = Pair(student1, student2)
            # Try saving the pair, and check the returned variable
            # since Python overrides allow changing the return
            # type from None to any other type
            status = p.save()
            if status == Pair.OK:
                # If the pair was created/validated, print
                # an OK message in the home page
                request.session['home_msg'] = ['Pair succesfully %s!' %
                                               ("validated" if p.validated
                                                else "created"),
                                               False]
                return redirect(reverse('home'))
            # If the status is not OK, send the message through an
            # error but don't redirect to other page
            context_dict['msg'] = "You already have a pair"\
                if status == Pair.YOU_HAVE_PAIR\
                else "The requested user already has a pair"
            context_dict['isError'] = True
            return render(request, 'core/applypair.html', context_dict)
        except Student.DoesNotExist:
            # If student2 doesn't exist, print it (invalid form)
            context_dict['msg'] = "\"student2\" does not exist."
            context_dict['isError'] = True
            return render(request, 'core/applypair.html', context_dict)
    return render(request, 'core/applypair.html', context_dict)


@login_required
def applygroup(request):
    context_dict = {}
    stu = Student.from_user(request.user)

    # The student already has a lab group
    # No need to compute the groups
    if stu.labGroup is not None:
        context_dict['group'] = stu.labGroup
        return render(request, 'core/applygroup.html', context_dict)
    try:
        now = datetime.datetime.now()
        now = timezone.make_aware(now, timezone.get_current_timezone())
        if False and OtherConstraints.objects.first().selectGroupStartDate > now:
            context_dict['not_active'] = True
            return render(request, 'core/applygroup.html', context_dict)
    except OtherConstraints.DoesNotExist:
        pass
    # The student selects a lab group
    if request.method == 'POST':
        try:
            # Check if the requested group exist, and add the
            # user to this group.
            lg = LabGroup.objects.get(id=request.POST['labGroup'])
            # Get the constraints for this group, if they exist
            try:
                gcs = GroupConstraints.objects.filter(labGroup=lg)
                canJoin = False
                for gc in gcs:
                    canJoin |= stu.theoryGroup == gc.theoryGroup
                if canJoin is False:
                    context_dict['msg'] = "Members of the theory group " +\
                        f"{stu.theoryGroup} can't join {lg}"
                    context_dict['isError'] = True
                    # Render the groups, since there's been an error
                    context_dict['groups'] = LabGroup.objects.all()
                    return render(request, 'core/applygroup.html',
                                  context_dict)
            except GroupConstraints.DoesNotExist:
                pass
            stu.labGroup = lg
            stu.save()
            lg.counter += 1
            lg.save()
            # Assign the group and give him a message
            context_dict['group'] = stu.labGroup
            context_dict['msg'] = request.POST['labGroup'] +\
                " has been assigned as your Lab group."
            context_dict['isError'] = False
            # No need to render the groups
            return render(request, 'core/applygroup.html', context_dict)
        except LabGroup.DoesNotExist:
            # If it doesn't exist, return an error message
            context_dict['msg'] = request.POST['labGroup'] + " does not exist."
            context_dict['isError'] = True
            # Don't return anything, just continue as if it was a regular GET

    # Compute and render the groups if you reach the end of the function
    # Compute and render the groups if you reach the end of the function
    context_dict['groups'] = []
    # Fetch all the valid groups and get them from LabGgroup
    for cons in GroupConstraints.objects.filter(theoryGroup=stu.theoryGroup):
        for g in LabGroup.objects.filter(groupName=cons.labGroup):
            context_dict['groups'].append(g)
    return render(request, 'core/applygroup.html', context_dict)
