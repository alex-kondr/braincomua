from django.db import models

# Create your models here.


class Product(models.Model):
    name = models.CharField(max_length=255)
    color = models.CharField(max_length=50, null=True, blank=True)
    memory = models.IntegerField(null=True, blank=True)
    vendor = models.CharField(max_length=255, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_promo = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    images = models.JSONField(default=list)
    sku = models.CharField(max_length=255, null=True, blank=True)
    revs_count = models.IntegerField(null=True, blank=True)
    diagonal = models.DecimalField(max_digits=10, decimal_places=1, null=True, blank=True)
    resolution = models.CharField(max_length=50, null=True, blank=True)
    specifications = models.JSONField(default=dict)

    def __str__(self):
        return self.name