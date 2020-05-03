from django.db import models

class Tag(models.Model):
    def __str__(self):
        return self.name

    name = models.CharField('name', max_length=255, unique=True)

class Entry(models.Model):
    def __str__(self):
        return self.name

    name = models.CharField('name', max_length=255)
    added_date = models.DateTimeField('date added')
    text = models.TextField('text', blank=True)

    tags = models.ManyToManyField(Tag, blank=True)

