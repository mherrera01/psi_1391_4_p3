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


class Student(User):
    # Foreign keys of Student
    labGroup = models.ForeignKey(LabGroup)
    theoryGroup = models.ForeignKey(TheoryGroup)

    # Properties inherited by User
    # first_name, last_name, email, password

    # Properties of Student
    gradeTheoryLastYear = models.FloatField()
    gradeLabLastYear = models.FloatField()
    convalidationGranted = models.BooleanField()

    class Meta:
        ordering = ['last_name', 'first_name']
    
    def __str__(self):
        return f'{self.first_name} {self.last_name}'


class Pair(models.Model):
    # Foreign keys of Pair
    student1 = models.ForeignKey(Student)
    student2 = models.ForeignKey(Student)
    studentBreakRequest = models.ForeignKey(Student)

    # Properties of Pair
    validated = models.BooleanField()
    
    def __str__(self):
        return f'{self.student1} - {self.student2}'


class LabGroup(models.Model):
    # Foreign keys of LabGroup
    MAX_LENGTH = 128
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    
    # Properties of LabGroup
    groupName = models.CharField(max_length=MAX_LENGTH)
    language = models.CharField(max_length=MAX_LENGTH)
    schedule = models.CharField(max_length=MAX_LENGTH)
    
    maxNumberStudents = models.IntegerField()
    counter = models.IntegerField()

    class Meta:
        ordering = ['groupName']
    
    def __str__(self):
        return self.groupName


class GroupConstraints(models.Model):
    # Foreign keys of GroupConstraints
    theoryGroup = models.ForeignKey(TheoryGroup)
    labGroup = models.ForeignKey(LabGroup)

    class Meta:
        ordering = ['theoryGroup.groupName', 'lab.groupName']
        
    def __str__(self):
        return f'{self.theoryGroup} - {self.labGroup}'


class TheoryGroup(models.Model):
    MAX_LENGTH = 128

    groupName = models.CharField(max_length=MAX_LENGTH)
    language = models.CharField(max_length=MAX_LENGTH)

    class Meta:
        ordering = ['groupName']

    def __str__(self):
        return self.groupName
