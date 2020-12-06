from django import forms
from core.models import Pair, LabGroup, Student, GroupConstraints
from django.db.models import Q
from django.utils.safestring import mark_safe


class LabGroupForm(forms.Form):
    availableGroups = forms.ModelChoiceField(queryset=None,
                                             label="Available groups:")

    def __init__(self, student, *args, **kwargs):
        super(forms.Form, self).__init__(*args, **kwargs)

        # How many users will join?
        joining = 1
        # See if the user has a validated pair or not
        # since that will determine if they can join or not
        p = Pair.get_pair(student)
        if p is not None:
            if p.validated:
                joining = 2

        # Generate an array with the valid groups
        validGroups = [LabGroup.objects.filter(
            Q(groupName=g.labGroup))
            for g in GroupConstraints.objects
            .filter(theoryGroup=student.theoryGroup)]

        # Get the groups with space available
        groups_with_space = []
        for gQuery in validGroups:
            for g in gQuery:
                if g.maxNumberStudents - g.counter > joining:
                    groups_with_space.append(g.id)

        self.fields['availableGroups'].queryset = LabGroup.objects\
            .filter(id__in=groups_with_space)


class LoginForm(forms.ModelForm):
    username = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'w3-input w3-border w3-margin-bottom',
               'placeholder': 'Your NIE'}),
        label=mark_safe('<b>Username (NIE)</b>'))
    password = forms.CharField(widget=forms.PasswordInput(
        attrs={'class': 'w3-input w3-border w3-margin-bottom',
               'placeholder': 'Your DNI'}),
        label=mark_safe('<b>Password (DNI)</b>'))

    def set_NIE(self, NIE=None):
        self.fields['username'] = NIE

    class Meta:
        model = Student
        fields = ('username', 'password')


class PairForm(forms.Form):
    availableStudents = forms.ModelChoiceField(queryset=None,
                                               label="Available students:")

    def __init__(self, student, *args, **kwargs):
        super(forms.Form, self).__init__(*args, **kwargs)

        they_chosen_us = []
        eligible_students = {}

        groups_that_can_join = set()
        # Check all groups that can join the same
        # groups as we do
        if student.labGroup is None:
            for gc in GroupConstraints.objects.filter(
                    theoryGroup=student.theoryGroup):
                groups_that_can_join.add(gc.theoryGroup)
        else:
            for gc in GroupConstraints.objects.filter(
                    labGroup=student.labGroup):
                groups_that_can_join.add(gc.theoryGroup)

        # Check all eligible students
        for student_to_check in Student.objects\
                .filter(theoryGroup__in=groups_that_can_join):
            # Check his pairs
            for p in Pair.get_pair(student_to_check):
                if p.validated:
                    continue
                elif p.student1 != student:
                    # If he has chosen us as their mate
                    if p.student2 == student:
                        they_chosen_us.append(p.student1)
                    continue
            # not in a pair, add them to eligible
            eligible_students.add(student_to_check)

        # Add the queryset in such a way the students that
        # selected us are shown first on the list
        queryset = Student.objects.filter(id__in=they_chosen_us)\
            | Student.objects.filter(id__in=eligible_students)
        self.fields['availableStudents'].queryset = queryset
