"""Deterministic, bounded 3D placement search for order packing."""
from dataclasses import dataclass
from decimal import Decimal
from itertools import permutations

from django.core.exceptions import ValidationError
from .constants import MAX_ORDER_UNITS, MAX_SEARCH_NODES
from .models import Box, Order


@dataclass
class RecommendationResult:
    box: Box | None
    total_weight: Decimal
    cost: Decimal | None
    explanation: str
    status: str  # "recommended", "none", or "inconclusive"


def _orientations(product):
    return sorted(set(permutations((product.length, product.width, product.height))))


def _can_place(position, size, placed):
    x, y, z = position
    length, width, height = size
    for px, py, pz, pl, pw, ph in placed:
        separated = (x + length <= px or px + pl <= x or
                     y + width <= py or py + pw <= y or
                     z + height <= pz or pz + ph <= z)
        if not separated:
            return False
    return True


def _fits(box, products):
    """Return True if placement is proven, False if exhaustively rejected, None if capped."""
    bounds = (box.internal_length, box.internal_width, box.internal_height)
    items = []
    for line in products:
        for _ in range(line.quantity):
            items.append(line.product)
    items.sort(key=lambda p: (-p.length * p.width * p.height,
                              -max(p.length, p.width, p.height), p.name, p.pk))
    placed = []
    visited = 0

    def search(index):
        nonlocal visited
        if index == len(items):
            return True
        product = items[index]
        candidates = {(Decimal(0), Decimal(0), Decimal(0))}
        for x, y, z, length, width, height in placed:
            candidates.update({(x + length, y, z), (x, y + width, z), (x, y, z + height)})
        for size in _orientations(product):
            if any(dimension > bound for dimension, bound in zip(size, bounds)):
                continue
            for position in sorted(candidates):
                x, y, z = position
                if x + size[0] > bounds[0] or y + size[1] > bounds[1] or z + size[2] > bounds[2]:
                    continue
                if not _can_place(position, size, placed):
                    continue
                visited += 1
                if visited > MAX_SEARCH_NODES:
                    return None
                placed.append((*position, *size))
                outcome = search(index + 1)
                if outcome is True:
                    return True
                placed.pop()
                if outcome is None:
                    return None
        return False

    return search(0)


def recommend_box(order: Order) -> RecommendationResult:
    """Find cheapest box that the placement search verifies; tie-break by name then ID."""
    lines = list(order.items.select_related("product").order_by("product__name", "product_id"))
    total_weight = sum((line.product.weight * line.quantity for line in lines), Decimal("0"))
    if not lines:
        return RecommendationResult(None, total_weight, None, "This order has no products.", "none")
    try:
        for line in lines:
            line.full_clean()
            line.product.full_clean()
    except ValidationError:
        return RecommendationResult(None, total_weight, None,
                                    "This order contains invalid product or quantity data.", "none")

    boxes = list(Box.objects.order_by("cost", "name", "id"))
    if not boxes:
        return RecommendationResult(None, total_weight, None, "No shipping boxes are available.", "none")
    total_units = sum(line.quantity for line in lines)
    if total_units > MAX_ORDER_UNITS:
        return RecommendationResult(None, total_weight, None,
            f"This order has {total_units} physical units, above the {MAX_ORDER_UNITS}-unit packing limit. "
            "The result is inconclusive; no box is recommended.", "inconclusive")

    saw_weight_candidate = False
    invalid_box_count = 0
    for box in boxes:
        try:
            box.full_clean()
        except ValidationError:
            invalid_box_count += 1
            continue
        if box.max_weight < total_weight:
            continue
        saw_weight_candidate = True
        fits = _fits(box, lines)
        if fits is None:
            return RecommendationResult(None, total_weight, None,
                f"Packing search reached its {MAX_SEARCH_NODES:,}-placement limit for {box.name}. "
                "The result is inconclusive; no box is recommended.", "inconclusive")
        if fits:
            return RecommendationResult(box, total_weight, box.cost,
                f"{box.name} is the lowest-cost box verified by the 3D placement search. "
                "Every item is within the box and does not overlap; equal costs are ordered by box name, then ID.",
                "recommended")
    explanation = ("No box passed the 3D placement and weight checks. The bounded search can miss a valid "
                   "arrangement, so this means no box was verified, not that impossibility is mathematically proven.")
    if not saw_weight_candidate:
        explanation = ("No available valid box has enough weight capacity for this order."
                       if invalid_box_count else "No available box has enough weight capacity for this order.")
    elif invalid_box_count:
        explanation += f" {invalid_box_count} invalid box record(s) were ignored."
    return RecommendationResult(None, total_weight, None, explanation, "none")
