from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

from core.models import (Student, Pair, OtherConstraints,
                         LabGroup, GroupConstraints)


def home(request):
    context_dict = {}
    if request.user.is_authenticated:
        stu = Student.objects.get(username=request.user.username)
        context_dict['student'] = stu
        pair = Pair.get_pair(stu)
        context_dict['pair'] = pair
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
    stu = Student.objects.get(username=request.user.username)

    # add the grade variables, used to print
    context_dict['lab_min_grade'] = oc.minGradeLabConv
    context_dict['theory_min_grade'] = oc.minGradeTheoryConv
    context_dict['lab_student_grade'] = stu.gradeLabLastYear
    context_dict['theory_student_grade'] = stu.gradeTheoryLastYear

    # update the convalidation variable
    stu.convalidationGranted = oc.minGradeLabConv < stu.gradeLabLastYear and\
        stu.gradeTheoryLastYear > oc.minGradeTheoryConv and\
        Pair.get_pair(stu) is None
    stu.save()
    context_dict['convalidated'] = stu.convalidationGranted

    return render(request, 'core/convalidation.html', context_dict)


@login_required
def applypair(request):
    return redirect(reverse('home'))


@login_required
def applygroup(request):
    context_dict = {}
    stu = Student.objects.get(username=request.user.username)

    # The student already has a lab group
    if stu.labGroup is not None:
        context_dict['group'] = stu.labGroup
        return render(request, 'core/applygroup.html', context_dict)

    # The student selects a lab group
    if request.method == 'POST':
        try:
            # Check if the requested group exist, and add the
            # user to this group.
            lg = LabGroup.objects.get(groupName=request.POST['labGroup'])
            # Get the constraints for this group, if they exist
            try:
                gc = GroupConstraints.objects.get(labGroup=lg)
                if stu.theoryGroup != gc.theoryGroup:
                    context_dict['msg'] = "Members of the theory group" +\
                        f"{stu.theoryGroup} can't join {lg}"
                    context_dict['groups'] = LabGroup.objects.all()
                    context_dict['isError'] = True
                    return render(request, 'core/applygroup.html',
                                  context_dict)
            except GroupConstraints.DoesNotExist:
                pass
            stu.labGroup = lg
            stu.save()
            context_dict['group'] = stu.labGroup
            context_dict['msg'] = request.POST['labGroup'] +\
                " has been assigned as your Lab group."
            context_dict['isError'] = False
            return render(request, 'core/applygroup.html', context_dict)
        except LabGroup.DoesNotExist:
            # If it doesn't exist, return an error message
            context_dict['msg'] = request.POST['labGroup'] + " does not exist."
            context_dict['isError'] = True
            # Don't return anything, just continue.

    context_dict['groups'] = LabGroup.objects.all()
    return render(request, 'core/applygroup.html', context_dict)
