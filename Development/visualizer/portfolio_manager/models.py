from __future__ import unicode_literals

from django.db import models
from simple_history.models import HistoricalRecords

class Organization (models.Model):
    name = models.CharField(max_length=50, primary_key=True)
    history = HistoricalRecords()
    def __str__(self):
        return str(self.name)

    def __unicode__(self):
        return self.name

class Project (models.Model):
    name = models.CharField(max_length=50)
    parent = models.ForeignKey('Organization',on_delete=models.CASCADE)
    history = HistoricalRecords()
