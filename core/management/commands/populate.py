# Populate database
# This file has to be placed within the
# core/management/commands directory in your project.
# If that directory doesn't exist, create it.
# The name of the script is the name of the custom command,
# that is, populate.py.
#
# execute python manage.py  populate


from django.core.management.base import BaseCommand
from core.models import (OtherConstraints, Pair, Student,
                         GroupConstraints, TheoryGroup,
                         LabGroup, Teacher)
from django.utils import timezone
from collections import OrderedDict
from datetime import timedelta
import argparse

import csv


# The name of this class is not optional must be Command
# otherwise manage.py will not process it properly
#
# Teachers, groups and constraints
# will be hardcoded in this file.
# Students will be read from a cvs file
# last year grade will be obtained from another cvs file
class Command(BaseCommand):
    # helps and arguments shown when command python manage.py help populate
    # is executed.
    help = """populate database
           """

    def add_arguments(self, parser):
        parser.add_argument('model', type=str, help='\nModel to update:' +
                            '\t all -- all models\n' +
                            '\tteacher\n' +
                            '\tlabgroup\n' +
                            '\ttheorygroup\n' +
                            '\tgroupconstraints\n' +
                            '\totherconstrains\n' +
                            '\tstudent -- requires a csv file passed\n' +
                            '\tstudentgrade -- requires different csv file,' +
                            'updates the students\n' +
                            '\tupdate --(only existing students)\n' +
                            '\tpair')

        parser.add_argument('studentinfo', type=str, help="CSV file " +
                            "with student information header= NIE, DNI, " +
                            "Apellidos, Nombre, Teoría\n")
        """
        if NIE or DNI == 0 skip this entry and print a warning
        """
        parser.add_argument('studentinfolastyear', type=str, help="CSV" +
                            "file with student information " +
                            "header= NIE,DNI,Apellidos,Nombre,Teoría, " +
                            "grade lab, grade theory\n")
        return parser

    # handle is another compulsory name, do not change it"
    def handle(self, *args, **kwargs):
        parser = argparse.ArgumentParser(description='Populates the ' +
                                         'database of our Django ' +
                                         'application based on our code\n')
        self.add_arguments(parser)

        parser.parse_args({'model': kwargs['model'],
                           'studentinfo': kwargs['studentinfo'],
                           'studentinfolastyear':
                           kwargs['studentinfolastyear']})

        model = kwargs['model']
        cvsStudentFile = kwargs['studentinfo']
        cvsStudentFileGrades = kwargs['studentinfolastyear']

        # clean database
        if model == 'all':
            self.cleanDataBase()
        if model == 'teacher' or model == 'all':
            self.teacher()
        if model == 'labgroup' or model == 'all':
            self.labgroup()
        if model == 'theorygroup' or model == 'all':
            self.theorygroup()
        if model == 'groupconstraints' or model == 'all':
            self.groupconstraints()
        if model == 'otherconstrains' or model == 'all':
            self.otherconstrains()
        if model == 'student' or model == 'all':
            self.student(cvsStudentFile)
        if model == 'studentgrade' or model == 'all':
            self.studentgrade(cvsStudentFileGrades)
        if model == 'pair' or model == 'all':
            self.pair()

    def cleanDataBase(self):
        # delete all models stored (clean table)
        # in database
        Teacher.objects.all().delete()
        OtherConstraints.objects.all().delete()
        Pair.objects.all().delete()
        Student.objects.all().delete()
        GroupConstraints.objects.all().delete()
        TheoryGroup.objects.all().delete()
        LabGroup.objects.all().delete()

    def teacher(self):
        # create dictionary with teacher data
        teacherD = OrderedDict()

        teacherD[1] = {'id': 1,  # 1261, L 18:00, 1271 X 18-20
                       'first_name': 'No',
                       'last_name': 'Asignado1', }
        teacherD[2] = {'id': 2,  # 1262 X 18-20, 1263/1273 V 17-19
                       'first_name': 'No',
                       'last_name': 'Asignado4', }
        teacherD[3] = {'id': 3,  # 1272 V 17-19, 1291 L 18-20
                       'first_name': 'Julia',
                       'last_name': 'Diaz Garcia', }
        teacherD[4] = {'id': 4,  # 1292/1251V 17:00
                       'first_name': 'Alvaro',
                       'last_name': 'del Val Latorre', }
        teacherD[5] = {'id': 5,  # 1201 X 18:00
                       'first_name': 'Roberto',
                       'last_name': 'Marabini Ruiz', }

        # save in data base
        for id, teacher in teacherD.items():
            t = Teacher.objects.update_or_create(id=id, defaults=teacher)[0]
            t.save()

    def labgroup(self):
        maxNumberStudents = 23

        # create dictionary with lab group data
        labgroupD = OrderedDict()

        labgroupD[1261] = {'id': 1261,  # 1261, L 18:00, 1271 X 18-20
                           'groupName': '1261',
                           'teacher': 1,
                           'schedule': 'Lunes/Monday 18-20',
                           'language': 'español/Spanish',
                           'maxNumberStudents': maxNumberStudents}
        labgroupD[1262] = {'id': 1262,  # 1261, L 18:00, 1271 X 18-20
                           'teacher': 2,
                           'groupName': '1262',
                           'schedule': 'Miércoles/Wednesday 18-20',
                           'language': 'español/Spanish',
                           'maxNumberStudents': maxNumberStudents}
        labgroupD[1263] = {'id': 1263,  # 1261, L 18:00, 1271 X 18-20
                           'teacher': 2,
                           'groupName': '1263',
                           'schedule': 'Viernes/Friday 17-19',
                           'language': 'español/Spanish',
                           'maxNumberStudents': maxNumberStudents}
        labgroupD[1271] = {'id': 1271,  # 1261, L 18:00, 1271 X 18-20
                           'teacher': 1,
                           'groupName': '1271',
                           'schedule': 'Miércoles/Wednesday 18-20',
                           'language': 'español/Spanish',
                           'maxNumberStudents': maxNumberStudents}
        labgroupD[1272] = {'id': 1272,  # 1261, L 18:00, 1271 X 18-20
                           'teacher': 3,
                           'groupName': '1272',
                           'schedule': 'Viernes/Friday 17-19',
                           'language': 'español/Spanish',
                           'maxNumberStudents': maxNumberStudents}
        labgroupD[1291] = {'id': 1291,  # 1261, L 18:00, 1271 X 18-20
                           'teacher': 3,
                           'groupName': '1291',
                           'schedule': 'Lunes/Monday 18-20',
                           'language': 'inglés/English',
                           'maxNumberStudents': maxNumberStudents}
        labgroupD[1292] = {'id': 1292,
                           'teacher': 4,
                           'groupName': '1292',
                           'schedule': 'Viernes/Friday 17-19',
                           'language': 'inglés/English',
                           'maxNumberStudents': maxNumberStudents}
        labgroupD[1201] = {'id': 1201,
                           'teacher': 5,
                           'groupName': '1201',
                           'schedule': 'Miércoles/Wednesday 18-20',
                           'language': 'español/Spanish',
                           'maxNumberStudents': maxNumberStudents}

        # save in data base
        for id, lab in labgroupD.items():
            labTeacher = Teacher.objects.get(id=lab['teacher'])
            lab['teacher'] = labTeacher
            labGroup = LabGroup.objects.update_or_create(id=id,
                                                         defaults=lab)[0]
            labGroup.save()

    def theorygroup(self):
        # create dictionary with theory group data
        theorygroupD = OrderedDict()

        theorygroupD[126] = {'id': 126,
                             'groupName': '126',
                             'language': 'español/Spanish', }
        theorygroupD[127] = {'id': 127,  # 127/120
                             'groupName': '127',
                             'language': 'español/Spanish', }
        theorygroupD[129] = {'id': 129,  # 129/125
                             'groupName': '129',
                             'language': 'inglés/English', }
        theorygroupD[120] = {'id': 120,  # 127/120
                             'groupName': '120',
                             'language': 'español/Spanish', }
        theorygroupD[125] = {'id': 125,  # 129/125
                             'groupName': '125',
                             'language': 'inglés/English', }

        # save in data base
        for id, theory in theorygroupD.items():
            theoryGroup = TheoryGroup.objects\
                .update_or_create(id=id, defaults=theory)[0]
            theoryGroup.save()

    def groupconstraints(self):
        # create dictionary with other constraints data
        groupconstraintsD = OrderedDict()

        # mañana
        groupconstraintsD[1261] = {'theoryGroup': 126, 'labGroup': 1261}
        groupconstraintsD[1262] = {'theoryGroup': 126, 'labGroup': 1262}
        groupconstraintsD[1263] = {'theoryGroup': 126, 'labGroup': 1263}

        # tarde, split ii and doble
        # tarde - no doble
        groupconstraintsD[1271] = {'theoryGroup': 127, 'labGroup': 1271}
        groupconstraintsD[1272] = {'theoryGroup': 127, 'labGroup': 1272}
        # doble - tarde - español - WEds
        groupconstraintsD[1201] = {'theoryGroup': 120, 'labGroup': 1201}

        # english
        # inglés - ii - tarde Friday
        groupconstraintsD[1291] = {'theoryGroup': 129, 'labGroup': 1291}
        # inglés - doble
        groupconstraintsD[1292] = {'theoryGroup': 125, 'labGroup': 1292}
        # doble - tarde - 2nd group
        # groupconstraintsD[1202] = {'theoryGroup' : 120, 'labGroup': 1202}

        # save in data base
        for id, gconstr in groupconstraintsD.items():
            lgroup = LabGroup.objects.get(id=id)
            tgroup = TheoryGroup.objects.get(id=gconstr['theoryGroup'])
            groupConstraints = GroupConstraints.objects\
                .update_or_create(id=id,
                                  defaults={'theoryGroup': tgroup,
                                            'labGroup': lgroup})[0]
            groupConstraints.save()

    def pair(self):
        # first student id is 1000, second 1001, etc.
        # students are ordered alphabeticcally (last_name, first_name)
        """ create two requests
            1000 -> 1100
            1001 -> 1001
            create three verified groups
            1010 - 1110
            1011 - 1111
            1012 - 1112
        """
        pairD = OrderedDict()

        # Mañana
        pairD[1000] = {'student2': 1100, 'validated': False}
        pairD[1001] = {'student2': 1101, 'validated': False}
        pairD[1010] = {'student2': 1110, 'validated': True}
        pairD[1011] = {'student2': 1111, 'validated': True}
        pairD[1012] = {'student2': 1112, 'validated': True}

        # save in data base
        for id, pair in pairD.items():
            student1 = Student.objects.get(id=id)
            student2 = Student.objects.get(id=pair['student2'])
            pair['student2'] = student2
            p = Pair.objects.update_or_create(student1=student1,
                                              defaults=pair)[0]
            p.save()

    def otherconstrains(self):
        """create a single object here with staarting dates
        and maximum and minimum convalidation grades"""
        """ Use the following values:
        selectGroupStartDate = now + 1 day,
        minGradeTheoryConv = 3,
        minGradeLabConv = 7
        """

        # create dictionary with other constraints data
        otherConstraintsD = OrderedDict()

        otherConstraintsD = {'selectGroupStartDate': timezone.now() +
                             timedelta(days=1),
                             'minGradeTheoryConv': 3,
                             'minGradeLabConv': 7}

        OtherConstraints.objects\
            .update_or_create(id=0, defaults=otherConstraintsD)[0].save()

    def student(self, csvStudentFile):
        # read csv file
        # NIE,DNI,Apellidos,Nombre,grupo-teoria
        with open(csvStudentFile, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            currentstudent = 1000
            for row in reader:
                tgroup = TheoryGroup.objects.get(id=row['grupo-teoria'])

                getstu = Student.objects.get_or_create
                username = (row['NIE'])
                username = username.replace(" ", "")
                u = getstu(id=currentstudent,
                           defaults={'username': username,
                                     'last_name': row['Apellidos'],
                                     'first_name': row['Nombre'],
                                     'theoryGroup': tgroup})[0]
                u.set_password(row['DNI'])
                u.save()
                currentstudent += 1

    def studentgrade(self, csvStudentFileGrades):
        # read csv file
        # NIE,DNI,Apellidos,Nombre,grupo-teoria,nota-practicas,nota-teoria
        with open(csvStudentFileGrades, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            currentstudent = 1000
            for row in reader:
                tgroup = TheoryGroup.objects.get(id=row['grupo-teoria'])

                upd = Student.objects.update_or_create
                username = (row['NIE'])
                username = username.replace(" ", "")
                u = upd(username=username,
                        defaults={
                            'first_name': row['Nombre'],
                            'last_name': row['Apellidos'],
                            'gradeTheoryLastYear': row['nota-teoria'],
                            'gradeLabLastYear': row['nota-practicas'],
                            'theoryGroup': tgroup})[0]
                u.set_password(row['DNI'])
                u.save()
                currentstudent += 1
