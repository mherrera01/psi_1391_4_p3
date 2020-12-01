from django import forms
from core.models import Pair, LabGroup, Student, GroupConstraints
from django.contrib.auth.models import User
from django.db.models import Q


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
    password = forms.CharField(widget=forms.PasswordInput())

    class Meta:
        model = Student
        fields = ('username', 'password')


class PairForm(forms.Form):
    availableStudents = forms.ModelChoiceField(queryset=None,
                                               label="Available students:")

    def __init__(self, student, *args, **kwargs):
        super(forms.Form, self).__init__(*args, **kwargs)
        # TODO
        students_to_skip = []
        for p in Pair.objects.all():
            if p.validated:
                students_to_skip.append(p.student1)
                students_to_skip.append(p.student2)
        self.fields['availableStudents'].queryset = Student.objects\
            .exclude(id__in=students_to_skip)
