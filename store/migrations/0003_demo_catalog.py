from django.db import migrations


def create_demo_catalog(apps, schema_editor):
    Category = apps.get_model("store", "Category")
    Product = apps.get_model("store", "Product")

    demo_data = [
        (
            "Fruits & Vegetables",
            "fruits-vegetables",
            [
                ("Fresh Tomatoes 1kg", 40),
                ("Potatoes 5kg", 120),
                ("Onions 2kg", 70),
                ("Bananas 1 Dozen", 60),
                ("Apples 1kg", 150),
            ],
        ),
        (
            "Dairy & Bakery",
            "dairy-bakery",
            [
                ("Toned Milk 1L", 55),
                ("Bread Loaf 400g", 35),
                ("Butter 100g", 60),
                ("Curd 500g", 45),
                ("Paneer 200g", 90),
            ],
        ),
        (
            "Staples & Atta",
            "staples-atta",
            [
                ("Wheat Atta 5kg", 260),
                ("Basmati Rice 5kg", 520),
                ("Toor Dal 1kg", 160),
                ("Chana Dal 1kg", 140),
                ("Sugar 1kg", 50),
            ],
        ),
        (
            "Oils & Masala",
            "oils-masala",
            [
                ("Refined Oil 1L", 150),
                ("Mustard Oil 1L", 170),
                ("Garam Masala 100g", 65),
                ("Red Chilli Powder 200g", 80),
                ("Turmeric Powder 200g", 70),
            ],
        ),
        (
            "Snacks & Beverages",
            "snacks-beverages",
            [
                ("Potato Chips 100g", 30),
                ("Namkeen Mixture 500g", 120),
                ("Soft Drink 2L", 95),
                ("Tea 500g", 230),
                ("Instant Coffee 100g", 250),
            ],
        ),
    ]

    for cat_name, slug, products in demo_data:
        category, _ = Category.objects.get_or_create(
            slug=slug,
            defaults={"name": cat_name, "is_active": True},
        )
        for prod_name, price in products:
            Product.objects.get_or_create(
                name=prod_name,
                category=category,
                defaults={
                    "slug": prod_name.lower().replace(" ", "-"),
                    "description": prod_name,
                    "price": price,
                    "stock": 50,
                    "available": True,
                    "featured": False,
                },
            )


class Migration(migrations.Migration):

    dependencies = [
        ("store", "0002_offer"),
    ]

    operations = [
        migrations.RunPython(create_demo_catalog, migrations.RunPython.noop),
    ]
