from core.models import OtherConstraints, Pair, Student
import os
import django

from django.utils import timezone
from datetime import timedelta
from django.utils.timezone import make_aware, make_naive

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'labassign.settings')
django.setup()

if __name__ == 'main':

    # checks if a user (Student) with id=1000 exists, otherwise create
    # and persist it. In the following we will refer to this
    # user as user 1000. Remember that Django automatically adds to
    # all tables of the model a id attribute that acts as a key primary.
    stugoc = Student.objects.get_or_create
    user1000 = stugoc(id=1000,
                      defaults={'username': 'user_1000',
                                'password': 'alumnodb'})

    # checks if a user with id=1001 exists, otherwise create and persist it.
    # In the future we will refer to this user as user 1001.
    user1001 = stugoc(id=1001,
                      defaults={'username': 'user_1001',
                                'password': 'alumnodb'})

    # creates a pair (Pair) using as student1 and student2
    # users user 1000 and user 1001 respectively.
    # Persist the result in the database.
    Pair.objects.get_or_create(student1=user1000, student2=user1001)

    # searches for all the pairs (Pair) where user 1000 appears as student1.
    # Print the result of the search by screen.
    pairs = Pair.objects.filter(student1=user1000)
    print(pairs)

    # modifies the value of validate in the pairs resulting
    # from the previous search so that it is set to True.
    # The modification should be persisted in the database
    for pair in pairs:
        pair.validated = True

    # creates an object of type OtherConstraints with the value of
    # selectGroupStartDate equal to the current time plus one day.
    occ = OtherConstraints.objects.get_or_create
    now_plus_one_day = make_aware(timezone.now() + timedelta(days=1))
    o = occ(selectGroupStartDate=now_plus_one_day,
            defaults={'minGradeTheoryConv': 3,
                      'minGradeLabConv': 7})

    # performs a search that returns all the objects of type OtherConstraints
    # and for the first of the returned objects compares the
    # value of selectGroupStartDate with the current moment.
    # Print the result of the comparison per screen so that it is
    # indicated whether selectGroupStartDate is a date in the past
    # or in the future.
    # The code created must be valid for any value in selectGroupStartDate.
    constraints = OtherConstraints.objects.all().first()
    time_from_constraint = make_naive(constraints.selectGroupStartDate)
    if time_from_constraint > timezone.now():
        print("Constraint's group selection expires after today")
    else:
        print("Constraint's group selection is due (expired)")
