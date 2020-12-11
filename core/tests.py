from django.test import TestCase

# Create your tests here.

from core.tests_models import ModelTests
from core.tests_services import (ServiceBaseTest, LogInOutServiceTests,
                                 ConvalidationServiceTests, PairServiceTests,
                                 BreakPairServiceTests,
                                 GroupServiceTests)
# We're skipping BreakPairServiceTests since it will throw, anyways
