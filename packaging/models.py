from django.core.validators import MinValueValidator
from django.db import models


class Product(models.Model):
    name = models.CharField(max_length=120, unique=True)
    length = models.DecimalField(max_digits=9, decimal_places=2, validators=[MinValueValidator(0.01)])
    width = models.DecimalField(max_digits=9, decimal_places=2, validators=[MinValueValidator(0.01)])
    height = models.DecimalField(max_digits=9, decimal_places=2, validators=[MinValueValidator(0.01)])
    weight = models.DecimalField(max_digits=9, decimal_places=3, validators=[MinValueValidator(0.001)])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name", "id"]

    def __str__(self):
        return self.name


class Box(models.Model):
    name = models.CharField(max_length=120, unique=True)
    internal_length = models.DecimalField(max_digits=9, decimal_places=2, validators=[MinValueValidator(0.01)])
    internal_width = models.DecimalField(max_digits=9, decimal_places=2, validators=[MinValueValidator(0.01)])
    internal_height = models.DecimalField(max_digits=9, decimal_places=2, validators=[MinValueValidator(0.01)])
    max_weight = models.DecimalField(max_digits=9, decimal_places=3, validators=[MinValueValidator(0.001)])
    cost = models.DecimalField(max_digits=9, decimal_places=2, validators=[MinValueValidator(0)])

    class Meta:
        ordering = ["cost", "name", "id"]

    def __str__(self):
        return self.name


class Order(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    products = models.ManyToManyField(Product, through="OrderItem", related_name="orders")

    def __str__(self):
        return f"Order {self.pk}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="order_items")
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    class Meta:
        constraints = [models.UniqueConstraint(fields=["order", "product"], name="one_line_per_product")]

    def __str__(self):
        return f"{self.quantity} × {self.product}"
