from django.db import migrations

def generate_skus(apps, schema_editor):
    Product = apps.get_model('products', 'Product')
    for product in Product.objects.filter(sku__isnull=True):
        product.sku = f"SKU-{product.id:05d}"
        product.save(update_fields=["sku"])

class Migration(migrations.Migration):

    dependencies = [
        ('products', '0004_alter_category_options_product_sku_and_more'),
    ]

    operations = [
        migrations.RunPython(generate_skus),
    ]