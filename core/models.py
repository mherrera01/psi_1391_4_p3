from django.db import models
from django.contrib.auth.models import User
from django.db.models import Q


class OtherConstraints(models.Model):
    selectGroupStartDate = models.DateTimeField()
    minGradeTheoryConv = models.FloatField()
    minGradeLabConv = models.FloatField()

    def __str__(self):
        return 'Theory: %.1f | Lab: %.1f'\
               % (self.minGradeLabConv, self.minGradeTheoryConv)


class Teacher(models.Model):
    MAX_LENGTH = 128

    # Properties of Student
    first_name = models.CharField(max_length=MAX_LENGTH)
    last_name = models.CharField(max_length=MAX_LENGTH)

    class Meta:
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f'{self.first_name} {self.last_name}'


class LabGroup(models.Model):
    # Foreign keys of LabGroup
    MAX_LENGTH = 128
    teacher = models.ForeignKey(Teacher, null=True, on_delete=models.SET_NULL)

    # Properties of LabGroup
    groupName = models.CharField(max_length=MAX_LENGTH, unique=True, null=True)
    language = models.CharField(max_length=MAX_LENGTH)
    schedule = models.CharField(max_length=MAX_LENGTH)

    maxNumberStudents = models.IntegerField()
    counter = models.IntegerField(default=0)

    class Meta:
        ordering = ['groupName']

    def __str__(self):
        return self.groupName


class TheoryGroup(models.Model):
    MAX_LENGTH = 128

    groupName = models.CharField(max_length=MAX_LENGTH)
    language = models.CharField(max_length=MAX_LENGTH)

    class Meta:
        ordering = ['groupName']

    def __str__(self):
        return self.groupName


class Student(User):
    # Foreign keys of Student
    labGroup = models.ForeignKey(LabGroup, null=True,
                                 on_delete=models.SET_NULL)
    theoryGroup = models.ForeignKey(TheoryGroup, null=True,
                                    on_delete=models.SET_NULL)

    # Properties inherited by User
    # username, first_name, last_name, email, password

    # Properties of Student
    gradeTheoryLastYear = models.FloatField(default=0)
    gradeLabLastYear = models.FloatField(default=0)
    convalidationGranted = models.BooleanField(default=False)

    class Meta:
        ordering = ['last_name', 'first_name']

    def from_user(user: User):
        return Student.objects.get(username=user.username)

    def __str__(self):
        return f'{self.first_name} {self.last_name}'


class Pair(models.Model):
    # Save function return codes
    OK = 0
    # Student1 already has a pair
    YOU_HAVE_PAIR = 1
    # The second student has a pair
    SECOND_HAS_PAIR = 2

    # Foreign keys of Pair
    student1 = models.OneToOneField(Student,
                                    null=False,
                                    related_name="student1",
                                    on_delete=models.CASCADE)
    student2 = models.ForeignKey(Student, null=False,
                                 related_name="student2",
                                 on_delete=models.CASCADE)

    sbr = "studentBreakRequest"  # aux for Flake8
    studentBreakRequest = models.ForeignKey(Student, null=True,
                                            related_name=sbr,
                                            on_delete=models.SET_NULL)

    # Properties of Pair
    validated = models.BooleanField(default=False)

    def get_pair(student: Student):
        try:
            return Pair.objects.get(Q(student1=student) |
                                    Q(student2=student))
        except Pair.DoesNotExist:
            return None

    def save(self, *args, **kwargs):
        if self.validated is False:
            # Check if this user already requested another
            # pair. If he did, don't save this one.

            # If it returned anything not equal to self,
            # he already requested another pair
            pair = Pair.get_pair(self.student1)
            if pair is not None and self != pair:
                return Pair.YOU_HAVE_PAIR

            # See if student2 already has a pair
            # where his student2 matches self.student1

            # Check if another pair exists beforehand
            other_pair = Pair.get_pair(self.student2)

            # It exists, check if said student wants
            # to be with self.student1 too
            if other_pair is not None:

                # If the following statement is false, create
                # this new pair by just continuing
                # after the except
                if other_pair.student2 == self.student1:
                    # Validate the other pair (first created)
                    # and don't save this one
                    other_pair.validated = True
                    other_pair.save()
                    return Pair.OK
                else:
                    return Pair.SECOND_HAS_PAIR

        """
            To be completed in practice 4
        if self.studentBreakRequest:
            self.validated = False
        """
        # Save this current pair
        super(Pair, self).save(*args, **kwargs)
        return Pair.OK

    class Meta:
        ordering = ['student1__id', 'student2__id']

    def __str__(self):
        return f'{self.student1} - {self.student2}'


class GroupConstraints(models.Model):
    # Foreign keys of GroupConstraints
    theoryGroup = models.ForeignKey(TheoryGroup, null=True,
                                    on_delete=models.SET_NULL)
    labGroup = models.OneToOneField(LabGroup, on_delete=models.CASCADE)

    class Meta:
        ordering = ['labGroup', 'theoryGroup']

    def __str__(self):
        return f'{self.theoryGroup} - {self.labGroup}'
