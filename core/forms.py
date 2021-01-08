from django import forms
from core.models import Pair, LabGroup, Student, GroupConstraints
from django.db.models import Q
from django.utils.safestring import mark_safe


class LabGroupForm(forms.Form):
    """A form to display which lab groups a given student can
    apply to
    """
    labGroup = forms.ModelChoiceField(queryset=None,
                                      label="Available groups:")

    def __init__(self, student, *args, **kwargs):
        """A form to display which lab groups a given student can
    apply to

        :param student: The student to check
        :type student: core.models.Student
        """
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

        self.fields['labGroup'].queryset = LabGroup.objects\
            .filter(id__in=groups_with_space)


class LoginForm(forms.ModelForm):
    """The basic Login form.
    """
    username = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'w3-input w3-border w3-margin-bottom',
               'placeholder': 'Your NIE'}),
        label=mark_safe('<b>Username (NIE)</b>'))
    password = forms.CharField(widget=forms.PasswordInput(
        attrs={'class': 'w3-input w3-border w3-margin-bottom',
               'placeholder': 'Your DNI'}),
        label=mark_safe('<b>Password (DNI)</b>'))

    def set_NIE(self, NIE=None):
        """Sets the NIE field to the passed NIE

        :param NIE: The NIE to be set, defaults to None
        :type NIE: str, optional
        """
        self.fields['username'].widget.attrs['value'] = NIE

    class Meta:
        model = Student
        fields = ('username', 'password')


# This is not a form, but it's only used in forms, so it makes
# sense it should be here and not in another module.
class CustomApplyPairModelChoiceField(forms.ModelChoiceField):
    """Makes it easier to print a custom string for our student
    in applypair"""

    def __init__(self, *args, **kwargs):
        """Makes it easier to print a custom string for our student
    in applypair
        """
        super(CustomApplyPairModelChoiceField, self).__init__(*args, **kwargs)

    def label_from_instance(self, obj):
        group = obj.labGroup if obj.labGroup else obj.theoryGroup
        literal = f"({group})>{str(obj.last_name)}, {str(obj.first_name)}"
        return mark_safe(literal)


class PairForm(forms.Form):
    student2 = CustomApplyPairModelChoiceField(queryset=None,
                                               label="")

    def __init__(self, student, *args, **kwargs):
        """PairForm to render the contents of the ApplyPair page

        Args:
            student (Student): The student to check for
        """
        super(forms.Form, self).__init__(*args, **kwargs)

        they_chosen_us = []
        eligible_students = set()

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

        # Check all eligible students from the groups
        # that can join our guy's group
        for student_to_check in Student.objects\
                .filter(Q(theoryGroup__in=groups_that_can_join) |
                        Q(theoryGroup=None)):
            # Skip the current user
            if student_to_check.id == student.id:
                continue
            # Check his pairs
            p = Pair.get_pair(student_to_check)
            if p is not None:
                if p.validated:
                    # Don't add them if they have
                    # a validated pair
                    continue
                # Its his request...
                # ...check if he has chosen us as their mate
                if p.student2 == student:
                    they_chosen_us.append(p.student1.id)
            else:
                # not in a pair, add them to eligible
                eligible_students.add(student_to_check.id)

        # Add the queryset in such a way the students that
        # selected us are shown first on the list
        # queryset = Student.objects.exclude(id=student.id)
        queryset = Student.objects.filter(id__in=they_chosen_us)\
            | Student.objects.filter(id__in=eligible_students)
        self.fields['student2'].queryset = queryset


# This is not a form, but it's only used in forms, so it makes
# sense it should be here and not in another module.
class CustomBreakPairModelChoiceField(forms.ModelChoiceField):
    """Makes it easier to print a custom string for our student
    in Breakpair"""

    def __init__(self, *args, **kwargs):
        super(CustomBreakPairModelChoiceField, self).__init__(*args, **kwargs)

    def label_from_instance(self, obj):
        valid = "Validated" if obj.validated else "Not validated"
        return mark_safe(f'{str(obj.student1)} | {str(obj.student2)} ' +
                         f'| {valid}')


class BreakPairForm(forms.Form):
    myPair = CustomBreakPairModelChoiceField(queryset=None,
                                             label="Available pairs:")

    def __init__(self, student, *args, **kwargs):
        """BreakPairForm to display on the browser which pairs
        can be broken by our user

        Args:
            student (Student): The student who wants to break the pair
        """
        super(forms.Form, self).__init__(*args, **kwargs)

        self.fields['myPair'].queryset = Pair.objects\
            .filter(Q(student1=student) |
                    Q(student2=student))
