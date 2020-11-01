from django.db import models
from django.contrib.auth.models import User


class OtherConstraints(models.Model):
    selectGroupStartDate = models.DateTimeField()
    minGradeTheoryConv = models.FloatField()
    minGradeLabConv = models.FloatField()

    def __str__(self):
        return 'Min Grades:\n\tTheory: %.1f | Lab: %.1f' % (minGradeLabConv, minGradeTheoryConv)


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
    groupName = models.CharField(max_length=MAX_LENGTH)
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
    labGroup = models.ForeignKey(LabGroup, null=True, on_delete=models.SET_NULL)
    theoryGroup = models.ForeignKey(TheoryGroup, null=True, on_delete=models.SET_NULL)

    # Properties inherited by User
    # first_name, last_name, email, password

    # Properties of Student
    gradeTheoryLastYear = models.FloatField(default=(-1))
    gradeLabLastYear = models.FloatField(default=(-1))
    convalidationGranted = models.BooleanField(default=False)

    class Meta:
        ordering = ['last_name', 'first_name']
    
    def __str__(self):
        return f'{self.first_name} {self.last_name}'


class Pair(models.Model):
    # Foreign keys of Pair
    student1 = models.OneToOneField(Student,
                                    null=False,
                                    related_name="student1",
                                    on_delete=models.CASCADE)
    student2 = models.ForeignKey(Student, null=False,
                                 related_name="student2",
                                 on_delete=models.CASCADE)

    sbr = "studentBreakRequest" # aux for Flake8
    studentBreakRequest = models.ForeignKey(Student, null=True,
                                            related_name=sbr,
                                            on_delete=models.SET_NULL)

    # Properties of Pair
    validated = models.BooleanField()

    def save(self, *args, **kwargs):
        # See if student2 already has a pair
        # where his student2 matches self.student1
        if self.validated is False:
            try:
                # Check if another pair exists beforehand
                other_pair = Pair.objects.get(student1=self.student2)
                
                # It exists, check if said student wants
                # to be with self.student1 too
                
                # If the statement is false, create
                # this new pair by just continuing
                # after the except

                if other_pair.student2 == self.student1:
                    # Validate the other pair (first created)

                    other_pair.validated = True
                    other_pair.save()
                    return
                
            except Pair.DoesNotExist:
                # There's no other pair. Just continue.
                pass

        if self.studentBreakRequest:
            self.validated = False
            
        super(Pair, self).save(*args, **kwargs)

    def __str__(self):
        return f'{self.student1} - {self.student2}'


class GroupConstraints(models.Model):
    # Foreign keys of GroupConstraints
    theoryGroup = models.ForeignKey(TheoryGroup, null=True,
                                    on_delete=models.SET_NULL)
    labGroup = models.OneToOneField(LabGroup, on_delete=models.CASCADE)

    class Meta:
        ordering = ['theoryGroup', 'labGroup']
        
    def __str__(self):
        return f'{self.theoryGroup} - {self.labGroup}'
