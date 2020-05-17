from django.db import models

from django_dag.models import *

class Tree(models.Model):
    def __str__(self):
        return self.name

    name = models.CharField('name', max_length=255, unique=True)

class Tag(node_factory('TagEdge')):
    def __str__(self):
        return self.name

    name = models.CharField('name', max_length=255, unique=True)

    # This needs to be added after Tree model has been migrated
    # tree = models.ForeignKey(Tree, on_delete=models.CASCADE, default='default_tree')

class TagEdge(edge_factory(Tag, concrete = False)):
    pass

class Entry(models.Model):
    def __str__(self):
        return self.name

    name = models.CharField('name', max_length=255)
    added_date = models.DateTimeField('date added')
    text = models.TextField('text', blank=True)

    tags = models.ManyToManyField(Tag, blank=True)

