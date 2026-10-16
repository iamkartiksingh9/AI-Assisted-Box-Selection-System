from decimal import Decimal
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import TestCase

from .models import Box, Order, OrderItem, Product
from .services import recommend_box


class RecommendationTests(TestCase):
    def setUp(self):
        self.product = Product.objects.create(name="Widget", length=4, width=3, height=2, weight=1)
        self.order = Order.objects.create()
        OrderItem.objects.create(order=self.order, product=self.product, quantity=1)

    def box(self, name, dims=(10, 10, 10), capacity=10, cost=10):
        return Box.objects.create(name=name, internal_length=dims[0], internal_width=dims[1],
                                  internal_height=dims[2], max_weight=capacity, cost=cost)

    def test_single_product_uses_cheapest_suitable_box(self):
        self.box("Costly", cost=12)
        cheap = self.box("Cheap", cost=4)
        result = recommend_box(self.order)
        self.assertEqual(result.box, cheap)
        self.assertEqual(result.cost, Decimal("4.00"))
        self.assertEqual(result.total_weight, Decimal("1.000"))
        self.assertIn("lowest-cost", result.explanation)

    def test_larger_box_selected_if_smaller_does_not_fit(self):
        self.box("Small", dims=(3, 3, 3), cost=1)
        large = self.box("Large", dims=(5, 5, 5), cost=5)
        self.assertEqual(recommend_box(self.order).box, large)

    def test_product_beyond_every_box_is_not_recommended(self):
        self.box("Tiny", dims=(1, 1, 1))
        self.assertIsNone(recommend_box(self.order).box)

    def test_product_fits_without_rotation_and_exactly_matches_box(self):
        exact = self.box("Exact fit", dims=(4, 3, 2))
        result = recommend_box(self.order)
        self.assertEqual(result.box, exact)

    def test_volume_only_fit_does_not_pass_dimension_check(self):
        # The box has more total volume (72) than the product (64), but is too short on every axis.
        self.product.length = 4
        self.product.width = 4
        self.product.height = 4
        self.product.save()
        self.box("Shallow box", dims=(6, 6, 2))
        self.assertIsNone(recommend_box(self.order).box)

    def test_weight_capacity_rejects_box(self):
        self.box("Light capacity", capacity=Decimal("0.5"))
        result = recommend_box(self.order)
        self.assertEqual(result.status, "none")
        self.assertIn("weight capacity", result.explanation)

    def test_box_at_exact_weight_capacity_is_accepted(self):
        exact_capacity = self.box("Exact capacity", capacity=1)
        self.assertEqual(recommend_box(self.order).box, exact_capacity)

    def test_product_fits_after_rotation(self):
        rotated = Product.objects.create(name="Long item", length=8, width=2, height=2, weight=1)
        order = Order.objects.create()
        OrderItem.objects.create(order=order, product=rotated, quantity=1)
        box = self.box("Rotated", dims=(3, 9, 3))
        self.assertEqual(recommend_box(order).box, box)

    def test_multiple_products_are_placed_without_overlap(self):
        other = Product.objects.create(name="Other", length=4, width=3, height=2, weight=1)
        OrderItem.objects.create(order=self.order, product=other, quantity=1)
        box = self.box("Two items", dims=(8, 3, 2))
        self.assertEqual(recommend_box(self.order).box, box)

    def test_products_that_cannot_fit_together_are_rejected(self):
        other = Product.objects.create(name="Other", length=4, width=3, height=2, weight=1)
        OrderItem.objects.create(order=self.order, product=other, quantity=1)
        self.box("Single only", dims=(4, 3, 2))
        self.assertIsNone(recommend_box(self.order).box)

    def test_quantity_affects_weight_and_packing(self):
        line = self.order.items.get()
        line.quantity = 2
        line.save()
        self.box("Capacity one", dims=(20, 3, 2), capacity=1)
        result = recommend_box(self.order)
        self.assertEqual(result.total_weight, Decimal("2.000"))
        self.assertIsNone(result.box)
        self.box("Capacity two", dims=(8, 3, 2), capacity=2)
        self.assertEqual(recommend_box(self.order).box.name, "Capacity two")

    def test_empty_order_is_rejected(self):
        empty = Order.objects.create()
        result = recommend_box(empty)
        self.assertEqual(result.status, "none")
        self.assertIn("no products", result.explanation)

    def test_equal_cost_boxes_tie_break_by_name(self):
        self.box("Zulu", cost=3)
        alpha = self.box("Alpha", cost=3)
        self.assertEqual(recommend_box(self.order).box, alpha)

    def test_no_available_boxes(self):
        result = recommend_box(self.order)
        self.assertIsNone(result.box)
        self.assertIn("No shipping boxes", result.explanation)

    def test_model_validation_rejects_nonpositive_product_dimensions_and_weight(self):
        invalid = Product(name="Bad", length=0, width=-1, height=1, weight=0)
        with self.assertRaises(ValidationError):
            invalid.full_clean()
        invalid_weight = Product(name="Bad weight", length=1, width=1, height=1, weight=-1)
        with self.assertRaises(ValidationError):
            invalid_weight.full_clean()

    def test_model_validation_rejects_invalid_box_capacity_and_cost(self):
        invalid = Box(name="Bad box", internal_length=1, internal_width=1, internal_height=1,
                      max_weight=0, cost=-1)
        with self.assertRaises(ValidationError):
            invalid.full_clean()

    def test_service_refuses_invalid_product_record(self):
        invalid_product = Product.objects.create(name="Bad stored data", length=0, width=1, height=1, weight=1)
        order = Order.objects.create()
        OrderItem.objects.create(order=order, product=invalid_product, quantity=1)
        result = recommend_box(order)
        self.assertIsNone(result.box)
        self.assertIn("invalid product", result.explanation)

    def test_service_ignores_invalid_box_record(self):
        Box.objects.create(name="Invalid capacity", internal_length=10, internal_width=10,
                           internal_height=10, max_weight=0, cost=-2)
        valid = self.box("Valid")
        self.assertEqual(recommend_box(self.order).box, valid)

    def test_service_rejects_zero_quantity_from_stored_data(self):
        line = self.order.items.get()
        line.quantity = 0
        line.save()
        result = recommend_box(self.order)
        self.assertEqual(result.status, "none")
        self.assertIn("invalid product or quantity", result.explanation)

    def test_large_quantity_returns_inconclusive_without_expanding_units(self):
        line = self.order.items.get()
        line.quantity = 251
        line.save()
        self.box("Large capacity", dims=(100, 100, 100), capacity=500)
        result = recommend_box(self.order)
        self.assertEqual(result.status, "inconclusive")
        self.assertIn("250-unit packing limit", result.explanation)

    def test_search_node_limit_never_returns_unverified_box(self):
        self.box("Candidate")
        with patch("packaging.services.MAX_SEARCH_NODES", 0):
            result = recommend_box(self.order)
        self.assertEqual(result.status, "inconclusive")
        self.assertIsNone(result.box)
        self.assertIn("search reached its 0-placement limit", result.explanation)

    def test_order_create_page_requires_products(self):
        response = self.client.get("/orders/new/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Create an order")

    def test_order_form_creates_lines_and_opens_recommendation(self):
        second_product = Product.objects.create(name="Second widget", length=2, width=2, height=2, weight=0.5)
        response = self.client.post("/orders/new/", {
            "items-TOTAL_FORMS": "3", "items-INITIAL_FORMS": "0",
            "items-MIN_NUM_FORMS": "1", "items-MAX_NUM_FORMS": "20",
            "items-0-product": str(self.product.pk), "items-0-quantity": "3",
            "items-1-product": str(second_product.pk), "items-1-quantity": "2",
            "items-2-product": "", "items-2-quantity": "",
        })
        created = Order.objects.exclude(pk=self.order.pk).get()
        self.assertEqual(response.status_code, 302)
        self.assertIn(f"/orders/{created.pk}/recommendation/", response.url)
        self.assertEqual(created.items.count(), 2)
        self.assertEqual(created.items.get(product=self.product).quantity, 3)
        self.assertEqual(created.items.get(product=second_product).quantity, 2)

    def test_order_form_rejects_empty_order(self):
        response = self.client.post("/orders/new/", {
            "items-TOTAL_FORMS": "3", "items-INITIAL_FORMS": "0",
            "items-MIN_NUM_FORMS": "1", "items-MAX_NUM_FORMS": "20",
            "items-0-product": "", "items-0-quantity": "",
            "items-1-product": "", "items-1-quantity": "",
            "items-2-product": "", "items-2-quantity": "",
        })
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(response.status_code, 200)

    def test_order_form_rejects_duplicate_products_with_message(self):
        payload = {
            "items-TOTAL_FORMS": "3", "items-INITIAL_FORMS": "0",
            "items-MIN_NUM_FORMS": "1", "items-MAX_NUM_FORMS": "20",
            "items-0-product": str(self.product.pk), "items-0-quantity": "1",
            "items-1-product": str(self.product.pk), "items-1-quantity": "1",
            "items-2-product": "", "items-2-quantity": "",
        }
        response = self.client.post("/orders/new/", payload)
        self.assertEqual(Order.objects.count(), 1)
        self.assertContains(response, "Choose each product once")

    def test_order_form_rejects_zero_quantity(self):
        payload = {
            "items-TOTAL_FORMS": "3", "items-INITIAL_FORMS": "0",
            "items-MIN_NUM_FORMS": "1", "items-MAX_NUM_FORMS": "20",
            "items-0-product": str(self.product.pk), "items-0-quantity": "0",
            "items-1-product": "", "items-1-quantity": "",
            "items-2-product": "", "items-2-quantity": "",
        }
        response = self.client.post("/orders/new/", payload)
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ensure this value is greater than or equal to 1")

    def test_order_form_rejects_negative_quantity(self):
        payload = {
            "items-TOTAL_FORMS": "3", "items-INITIAL_FORMS": "0",
            "items-MIN_NUM_FORMS": "1", "items-MAX_NUM_FORMS": "20",
            "items-0-product": str(self.product.pk), "items-0-quantity": "-1",
            "items-1-product": "", "items-1-quantity": "",
            "items-2-product": "", "items-2-quantity": "",
        }
        response = self.client.post("/orders/new/", payload)
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(response.status_code, 200)

    def test_order_form_rejects_more_than_unit_limit(self):
        payload = {
            "items-TOTAL_FORMS": "3", "items-INITIAL_FORMS": "0",
            "items-MIN_NUM_FORMS": "1", "items-MAX_NUM_FORMS": "20",
            "items-0-product": str(self.product.pk), "items-0-quantity": "251",
            "items-1-product": "", "items-1-quantity": "",
            "items-2-product": "", "items-2-quantity": "",
        }
        response = self.client.post("/orders/new/", payload)
        self.assertEqual(Order.objects.count(), 1)
        self.assertContains(response, "at most 250 physical units")

    def test_product_creation_and_validation(self):
        response = self.client.post("/products/", {
            "name": "New product", "length": "2", "width": "3", "height": "4", "weight": "0.25",
        })
        self.assertRedirects(response, "/products/")
        self.assertTrue(Product.objects.filter(name="New product").exists())
        invalid = self.client.post("/products/", {
            "name": "Invalid product", "length": "0", "width": "3", "height": "4", "weight": "0.25",
        })
        self.assertEqual(invalid.status_code, 200)
        self.assertFalse(Product.objects.filter(name="Invalid product").exists())

    def test_box_creation_and_validation(self):
        response = self.client.post("/boxes/", {
            "name": "New box", "internal_length": "10", "internal_width": "8",
            "internal_height": "6", "max_weight": "5", "cost": "0",
        })
        self.assertRedirects(response, "/boxes/")
        self.assertTrue(Box.objects.filter(name="New box", cost=0).exists())
        invalid = self.client.post("/boxes/", {
            "name": "Invalid box", "internal_length": "-1", "internal_width": "8",
            "internal_height": "6", "max_weight": "5", "cost": "-1",
        })
        self.assertEqual(invalid.status_code, 200)
        self.assertFalse(Box.objects.filter(name="Invalid box").exists())

    def test_recommendation_view_displays_result_details(self):
        box = self.box("View box", dims=(4, 3, 2), capacity=1, cost=Decimal("2.50"))
        response = self.client.get(f"/orders/{self.order.pk}/recommendation/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, box.name)
        self.assertContains(response, "2.50")
        self.assertContains(response, "1.000")
        self.assertContains(response, "does not overlap")

    def test_missing_order_returns_404(self):
        response = self.client.get("/orders/99999/recommendation/")
        self.assertEqual(response.status_code, 404)

    def test_csrf_protection_rejects_post_without_token(self):
        csrf_client = self.client_class(enforce_csrf_checks=True)
        response = csrf_client.post("/products/", {
            "name": "No token", "length": "2", "width": "3", "height": "4", "weight": "0.25",
        })
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Product.objects.filter(name="No token").exists())
