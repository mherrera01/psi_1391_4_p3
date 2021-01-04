from django.db import models
from django.contrib.auth.models import User
from django.template.defaultfilters import slugify
from django.db.models import Q


class OtherConstraints(models.Model):
    """
    Global constraints, stored as a single object
    ==============================================
    Author: Miguel Herrera Martinez

    .. note::
       This is stored as a single object, which means you need to fetch it
       with: ``OtherConstraints.objects.first()``. An exception of type
       `OtherConstraints.DoesNotExist` will be raised if
       there's no "Other Constraints"

    :param selectGroupStartDate: The day when the Apply Group page will be open
    :type selectGroupStartDate: django.db.models.DateTimeField
    :param minGradeTheoryConv: The minimum Theory grade from last year to be
    convalidated
    :type minGradeTheoryConv: django.db.models.FloatField
    :param minGradeLabConv: The minimum Lab grade from last year to be
    convalidated
    :type minGradeLabConv: django.db.models.FloatField
    """
    selectGroupStartDate = models.DateTimeField()
    minGradeTheoryConv = models.FloatField()
    minGradeLabConv = models.FloatField()

    def __str__(self):
        """The string representation for OtherConstraints
        Author: Miguel Herrera Martinez

        :return: `Theory: X.X | Lab: Y.Y` where X.X is the theory group's
        minimum grade and Y-Y is the lab's minimum grade
        :rtype: str
        """
        return 'Theory: %.1f | Lab: %.1f'\
               % (self.minGradeLabConv, self.minGradeTheoryConv)


class Teacher(models.Model):
    """The teacher's info.
    Author: Jorge González Gómez

    :param id: Teacher's ID
    :type id: django.db.models.IntegerField
    :param first_name: Teacher's first name
    :type first_name: django.db.models.CharField
    :param last_name: Teacher's last name
    :type last_name: django.db.models.CharField
    """
    MAX_LENGTH = 128

    # Properties of Teacher
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

    slug = models.SlugField(unique=True)

    class Meta:
        ordering = ['groupName']

    def remove_student(self, student):
        """Removes a student from the current group
        Author: Miguel Herrera Martinez

        :param student: The Student to remove
        :type student: Student
        :return: True if he was removed, False if he wasn't.
        :rtype: bool
        """
        if student.labGroup is not self:
            return False
        student.labGroup = None
        student.save()
        self.counter -= 1
        self.save()
        return True

    def add_student(self, student):
        """Adds a student to the current group
        Author: Miguel Herrera Martinez

        :param student: The Student to add
        :type student: Student
        :return: True if he was added, False if the group is full.
        :rtype: bool
        """
        if self.counter + 1 > self.maxNumberStudents:
            return False
        student.labGroup = self
        student.save()
        self.counter += 1
        self.save()
        return True

    def save(self, *args, **kwargs):
        self.slug = slugify(self.groupName)
        super(LabGroup, self).save(*args, **kwargs)

    def __str__(self):
        return self.groupName


class TheoryGroup(models.Model):
    """ Defines the Theory Group model
    Author: Miguel Herrera Martinez

    :param groupName: The group's name
    :type groupName: django.db.models.CharField
    :param language: The group's language
    :type language: django.db.models.CharField
    """
    MAX_LENGTH = 128

    groupName = models.CharField(max_length=MAX_LENGTH)
    language = models.CharField(max_length=MAX_LENGTH)

    class Meta:
        ordering = ['groupName']

    def __str__(self):
        return self.groupName


class Student(User):
    """The student's info.
    Author: Jorge González Gómez

    :param id: Student's internal Django ID
    :type id: django.db.models.IntegerField
    :param labGroup: His assigned :class:`core.models.LabGroup`
    :type labGroup: core.models.LabGroup
    :param theoryGroup: His assigned :class:`core.models.theoryGroup`
    :type theoryGroup: core.models.TheoryGroup
    :param username: Student's username (his NIE)
    :type username: django.db.models.CharField
    :param first_name: Student's first name
    :type first_name: django.db.models.CharField
    :param last_name: Student's last name
    :type last_name: django.db.models.CharField
    :param email: Student's email
    :type email: django.db.models.CharField
    :param password: Student's password (his DNI)
    :type password: django.db.models.CharField
    :param gradeTheoryLastYear: His Theory grade from last year.
    :type gradeTheoryLastYear: django.db.models.FloatField
    :param gradeLabLastYear: His Lab grade from last year.
    :type gradeLabLastYear: django.db.models.FloatField
    :param convalidationGranted: If he has been given a convalidation this year
    :type convalidationGranted: django.db.models.BooleanField
    """
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
        """Gets a student from any `django.contrib.auth.models.User` user.
        Author: Jorge González Gómez

        :param user: The user to convert to student
        :type user: django.contrib.auth.models.User
        :return: The `Student` object for the user, or an exception if it's
        not found
        :rtype: Student
        """
        return Student.objects.get(id=user.id)

    def __str__(self):
        return f'{self.first_name} {self.last_name}'


class Pair(models.Model):
    """The Pair model, containing info about a certain pair
    Author: Jorge González Gómez

    :param student1: The first student of the pair
    :type student1: core.models.Student
    :param student2: The second student of the pair
    :type student2: core.models.Student
    :param studentBreakRequest: If different than `None`, represents who wants
    to break the pair
    :type studentBreakRequest: core.models.Student
    :param validated: If the pair is validated or if it isn't
    :type validated: django.db.models.BooleanField
    """

    # Save function return codes
    # OK if it has been saved succesfully
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

    _sbr = "studentBreakRequest"  # aux for Flake8
    studentBreakRequest = models.ForeignKey(Student, null=True,
                                            related_name=_sbr,
                                            on_delete=models.SET_NULL)

    # Properties of Pair
    validated = models.BooleanField(default=False)

    def get_pair(student: Student):
        """Gets the pair for a student, be it if he's
        the second or the first student
        Author: Jorge González Gómez

        :param student: The class:`core.models.Student` to query
        :type student: core.models.Student
        :return: The pair, or `None` if he doesn't have a pair
        :rtype: core.models.Pair
        """
        try:
            return Pair.objects.get(Q(student1=student) |
                                    (Q(student2=student)
                                     & Q(validated=True)))
        except Pair.DoesNotExist:
            return None

    def save(self, *args, **kwargs):
        """
        Does all the logic required by the "Apply Pair" service.
        This is to mantain consistency and to modularize the practice, and
        not depend on a HTTP service or not to depend on copy-pasting code,
        enhancing code reusability
        Author: Jorge González Gómez

        :return: * `Pair.OK` if everything went good.
                 * `Pair.YOU_HAVE_PAIR` if student1 has another requested pair.
                 * `Pair.SECOND_HAS_PAIR` if student2 has another pair
        :rtype: int
        """
        if self.validated is False:
            # Check if this user already requested another
            # pair. If he did, don't save this one.

            # If it returned anything not equal to self,
            # he already requested another pair
            try:
                own_pair = Pair.objects.get(student1=self.student1)
                if own_pair.student2 != self.student2:
                    # you have a different pair
                    return Pair.YOU_HAVE_PAIR
            except Pair.DoesNotExist:
                pass
            # See if student2 already has a pair
            # where his student2 matches self.student1

            # Check if another pair exists beforehand
            other_pair = Pair.get_pair(self.student2)

            # It exists, check if said student wants
            # to be with self.student1 too
            if other_pair is not None:
                if other_pair.id == self.id:
                    # Same pair, just skip the logic
                    pass
                # If the following statement is false, create
                # this new pair by just continuing
                # after the except
                elif other_pair.student2 == self.student1:
                    # Validate the other pair (first created)
                    # and don't save this one
                    other_pair.validated = True
                    other_pair.save()
                    return Pair.OK
                else:
                    # the other guy has another request
                    # (doesn't matter if it's not validated)
                    return Pair.SECOND_HAS_PAIR
        # Save this current pair
        super(Pair, self).save(*args, **kwargs)
        return Pair.OK

    def break_pair(self, student):
        """Method to break a pair.
        Author: Miguel Herrera Martínez

        Args:
            student (Student): The student who breaks the pair
        """
        if self.validated:
            self.studentBreakRequest = student
            self.validated = False
            super(Pair, self).save()
        else:
            self.delete()

    class Meta:
        ordering = ['student1__id', 'student2__id']

    def __str__(self):
        return f'{self.student1} - {self.student2}'


class GroupConstraints(models.Model):
    """The group constraints, used to see who can join a
    `LabGroup` in particular
    Author: Jorge González Gómez

    :param theoryGroup: The required theory group
    :type theoryGroup: core.models.TheoryGroup
    :param labGroup: The constrained Lab group
    :type labGroup: core.models.LabGroup
    """
    # Foreign keys of GroupConstraints
    theoryGroup = models.ForeignKey(TheoryGroup, null=True,
                                    on_delete=models.SET_NULL)
    labGroup = models.OneToOneField(LabGroup, on_delete=models.CASCADE)

    class Meta:
        ordering = ['labGroup', 'theoryGroup']

    def __str__(self):
        return f'{self.theoryGroup} - {self.labGroup}'
