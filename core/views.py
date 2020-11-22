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

    # update the convalidation variable if he meets the basic
    # conditions: grades higher than constraints,
    # and the user didn't select a group
    stu.convalidationGranted = stu.gradeLabLastYear > oc.minGradeLabConv\
        and stu.gradeTheoryLastYear > oc.minGradeTheoryConv
    if stu.labGroup is not None:
        stu.convalidationGranted = False

    if stu.convalidationGranted:
        # do not convalidate if user has a validated pair
        # or they are the first member of their pair
        p = Pair.get_pair(stu)
        if p is not None:
            if p.validated:
                stu.convalidationGranted = False
            elif p.student1.id == stu.id:
                stu.convalidationGranted = False
    stu.save()
    context_dict['convalidated'] = stu.convalidationGranted

    return render(request, 'core/convalidation.html', context_dict)


@login_required
def applypair(request):
    context_dict = {}
    # All the students except the currently logged in, and
    # those who are in an already validated pair
    valid_students = []
    for student in Student.objects.exclude(id=request.user.id):
        s_pair = Pair.get_pair(student)
        if s_pair:
            if s_pair.validated:
                continue
        valid_students.append(student)
    context_dict['students'] = valid_students
    # If he sent an Apply Pair request...
    s = Student.from_user(request.user)
    # To be used in the future, defined to prevent a second useless querie.
    pair = None
    if request.method == "POST":
        # Validate the request (in case he wants to exploit a vulnerability)
        if 'student2' not in request.POST:
            print("missing student2 in POST request")
            context_dict['msg'] = "Missing \"student2\" in POST request." +\
                "<br\\>Please, don't use a custom client " +\
                "to send modified requests."
            context_dict['isError'] = True
            return render(request, 'core/applypair.html', context_dict)
        # Validate, part two.
        if request.POST['student2'] == "":
            context_dict['msg'] = "Please, select an student."
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
            context_dict['msg'] = "\"student2\" does not exist."
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
        if OtherConstraints.objects.first().selectGroupStartDate > now:
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
                canJoin = GroupConstraints.objects.filter(
                    theoryGroup=stu.theoryGroup,
                    labGroup=lg).exists()
                if canJoin is False:
                    context_dict['msg'] = "Members of the theory group " +\
                        f"{stu.theoryGroup} can't join {lg}"
                    context_dict['isError'] = True
                    # Render the groups, since there's been an error
                    context_dict['groups'] = []
                    # Fetch all the valid groups and get them from LabGgroup
                    for cons in GroupConstraints.objects\
                            .filter(theoryGroup=stu.theoryGroup):
                        for g in LabGroup.objects\
                                .filter(groupName=cons.labGroup):
                            context_dict['groups'].append(g)
                    return render(request, 'core/applygroup.html',
                                  context_dict)
            except GroupConstraints.DoesNotExist:
                pass
            # Check if his pair *can* be with him too
            pair = Pair.get_pair(stu)
            if pair:
                fren = pair.student2 if stu == pair.student1\
                    else pair.student1
                if fren.labGroup:
                    if fren.labGroup != stu.labGroup:
                        # Can't join.
                        context_dict['msg'] = "Your selected partner is"\
                            + " in a different lab group (invalid)"
                        context_dict['isError'] = True
                else:
                    # Check if he can join your group
                    friendCanJoin = GroupConstraints.objects.filter(
                                theoryGroup=stu.theoryGroup,
                                labGroup=lg).exists()
                    if not friendCanJoin:
                        context_dict['msg'] = "Members of the "\
                            + "theory group " +\
                            f"{stu.theoryGroup} can't join {lg}"
                        context_dict['isError'] = True
                    else:
                        # If he can, force him into your
                        # lab group.
                        if lg.counter + 2 > lg.maxNumberStudents:
                            # They can't join this group...
                            # to avoid weird errors, just disallow both
                            context_dict['msg'] = "This group is full!"\
                                + "<br \\>You can't join with your partner"
                            context_dict['isError'] = True
                        else:
                            lg.add_student(fren)
            # Check if we added an error message, just so
            # we know the pair joined/can't join the group
            if 'msg' in context_dict:
                for cons in GroupConstraints.objects\
                        .filter(theoryGroup=stu.theoryGroup):
                    for g in LabGroup.objects\
                            .filter(groupName=cons.labGroup):
                        context_dict['groups'].append(g)
                return render(request, 'core/applygroup.html',
                              context_dict)
            # Assign the group and give him a nice message
            added = lg.add_student(stu)
            if not added:
                context_dict['msg'] = lg.groupName +\
                    " is FULL! You can't join this group."
                context_dict['isError'] = False
            else:
                context_dict['group'] = stu.labGroup
                context_dict['msg'] = lg.groupName +\
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
