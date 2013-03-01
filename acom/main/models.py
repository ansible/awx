from django.db import models

class CommonModel(models.Model):
    ''' common model for all object types that have these standard fields '''

    class Meta:
        abstract = True

    name = models.TextField()
    description = models.TextField()
    creation_date = models.DateField()
    db_table = 'inventories'
      
class Inventory(CommonModel):

    class Meta:
        db_table = 'inventory'

    id = models.AutoField(primary_key=True)


