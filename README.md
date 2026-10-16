# Packwise: AI-Assisted Box Selection System

Packwise is a small Django ecommerce packaging demo. It stores products, shipping boxes, and order lines, then recommends the lowest-cost box for which its deterministic 3D placement search verifies a valid arrangement and sufficient weight capacity. The runtime recommendation is ordinary Python logic; it does not call an AI service.

## Features

- Product and shipping-box management with server-side field validation.
- Orders with up to 20 distinct product lines and 250 total physical units.
- Quantity-adjusted total weight and physical-unit packing checks.
- Rotation through all six length/width/height permutations.
- Cheapest verified box, with equal-cost ties resolved by box name and then database ID.
- Clear no-box and search-inconclusive results.
- Responsive Django-template interface and Django automated tests.

## Technology and prerequisites

Python 3.10 or later, pip, and SQLite (included with most Python installations). The declared dependency is Django 5.2.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Open http://127.0.0.1:8000/. To populate a sample catalog, run `python manage.py seed_demo`; it can be rerun safely. Then choose **New order**, enter a product and quantity on each row, and request a recommendation. Use one consistent unit for every dimension and another consistent unit for every weight. Cost is a non-negative amount in the currency chosen by the business; no currency conversion is performed.

Run checks and tests with:

```bash
python manage.py check
python manage.py test
```

## Recommendation algorithm

The service first rejects an empty order and computes total weight as the sum of `product weight × quantity`. Boxes are considered in ascending cost, then name and ID. Boxes too light for the order are skipped.

For each remaining box, the placement search expands each quantity into physical units, sorts those units by descending volume and longest edge, and recursively attempts every unique axis-aligned orientation. Candidate origins are the box origin and the three face-adjacent coordinates produced by each placed item. A candidate must remain inside the box and be separated from every placed item along at least one axis. Thus a returned arrangement has explicit in-bounds, non-overlapping placements; volume alone never establishes a fit. The first verified box is the lowest-cost one under this search and tie-break order. To bound memory and recursion depth, orders are limited to 250 physical units; larger orders return an inconclusive result without attempting placement.

The search is bounded to 50,000 attempted placements per box. A found placement proves feasibility, but failure to find one is not proof that none exists: this candidate-position strategy can miss an arrangement, and a hard search cap yields an **inconclusive** result. In either case the app refuses to recommend an unverified arrangement. This is a practical deterministic heuristic, not a guaranteed complete solver for 3D bin packing. Items are modeled as axis-aligned cuboids; clearance, padding, fragility, box wall thickness, and support/stability constraints are outside the model.

## Validation rules

Product and internal box dimensions must be greater than zero; product weight and box maximum weight must be greater than zero; cost may be zero but not negative. Dimensions and weight are stored as decimal values with fixed precision. Orders accept 1–20 unique product lines, each with a positive integer quantity, up to 250 physical units total. Django forms validate user input, and model validators also guard model-level validation. (Django model validators run through `full_clean()` and forms; they are not automatically applied on a raw `.save()` call.)

## Project structure

```text
config/                 Django settings and root URLs
packaging/              Models, forms, views, service, tests, migrations and templates
packaging/management/   Repeatable demo-catalog command
.github/workflows/       GitHub Actions test workflow
manage.py
requirements.txt
README.md
AI_USAGE.md
TEST_OUTPUT.md
AUDIT_REPORT.md
LEARNING_REFLECTION.md
```

## Assumptions and security notes

The default settings are for local development. A throwaway secret key is generated at startup unless `DJANGO_SECRET_KEY` is provided. For deployment set a stable private `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=false`, and comma-separated `DJANGO_ALLOWED_HOSTS`, then use an appropriate production server and database. CSRF protection is enabled on POST forms. No authentication/authorization is included because the assignment asks for a local demonstration app.

## Submission items to complete yourself

Export the actual assistant chat transcript using the chat application's export controls and save the real exported file under `submission/` (for example `submission/chat-transcript.html`). Do not create a replacement transcript. After you have completed the project, write your own learning reflection in `LEARNING_REFLECTION.md`. `TEST_OUTPUT.md` records the latest local verification; see `AI_USAGE.md` for the disclosure.
