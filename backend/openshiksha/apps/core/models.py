"""
Core models for OpenShiksha

Modern implementation of core business models.
Will be populated based on legacy models with improvements.
"""

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


# Custom User model (placeholder - will be expanded)
class User(AbstractUser):
    """
    Custom user model extending Django's AbstractUser

    Will support multiple user types:
    - Student
    - Teacher
    - Parent
    - School Admin
    - Open Student
    """

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.username


# TODO: Models will be created based on legacy code study
# Priority models to implement:
# - School, Board, Standard, Subject, Chapter
# - Question, QuestionSubpart
# - Assignment, Submission
# - ClassRoom, SubjectRoom
# - Home (parent-child relationship)
# - Announcement
# - UserInfo (user profiles)

# Example placeholder for future implementation:
"""
class School(models.Model):
    name = models.CharField(max_length=255)
    board = models.ForeignKey('Board', on_delete=models.PROTECT)
    # ... other fields

class Question(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    standard = models.ForeignKey('Standard', on_delete=models.PROTECT)
    subject = models.ForeignKey('Subject', on_delete=models.PROTECT)
    chapter = models.ForeignKey('Chapter', on_delete=models.PROTECT)
    tags = models.ManyToManyField('QuestionTag')

    # NEW: JSON field for Cabinet metadata
    container_metadata = models.JSONField(null=True, blank=True)

class QuestionSubpart(models.Model):
    question = models.ForeignKey(Question, related_name='subparts', on_delete=models.CASCADE)
    index = models.PositiveIntegerField()

    # NEW: JSON field for variable constraints
    variable_constraints = models.JSONField(null=True, blank=True)
"""
