from django.db import migrations, models
import django.db.models.deletion


LEGACY_CATEGORY_NAME_MAP = {
    'woodworking': 'Woodworking',
    'art': 'Art',
    'handmade_gifts': 'Handmade Gifts',
    'fashion_embroidery': 'Fashion & Embroidery',
    'leathercraft': 'Leathercraft',
    'home_decor': 'Home Decor',
    'pottery_ceramics': 'Pottery & Ceramics',
    'furniture': 'Furniture',
    'jewelry': 'Jewelry',
    'clothing': 'Clothing',
    'decor': 'Decor',
    'other': 'Other',
}


def forwards_copy_category(apps, schema_editor):
    Request = apps.get_model('request', 'Request')
    Category = apps.get_model('workshop', 'Category')

    for request_obj in Request.objects.all().iterator():
        raw_value = (request_obj.category or '').strip()
        if not raw_value:
            continue

        category_name = LEGACY_CATEGORY_NAME_MAP.get(raw_value)
        if not category_name:
            category_name = raw_value.replace('_', ' ').strip().title()

        category_obj, _ = Category.objects.get_or_create(
            name=category_name,
            defaults={'description': 'Imported from request legacy category.'},
        )
        request_obj.category_new_id = category_obj.id
        request_obj.save(update_fields=['category_new'])


def backwards_copy_category(apps, schema_editor):
    Request = apps.get_model('request', 'Request')

    for request_obj in Request.objects.select_related('category_new').all().iterator():
        if request_obj.category_new_id:
            request_obj.category = request_obj.category_new.name.lower().replace(' & ', '_').replace(' ', '_')
            request_obj.save(update_fields=['category'])


class Migration(migrations.Migration):

    dependencies = [
        ('workshop', '0007_remove_workshopprofile_categories_and_more'),
        ('request', '0003_remove_request_reference_image_alter_request_id_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='request',
            name='category_new',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='legacy_requests', to='workshop.category'),
        ),
        migrations.RunPython(forwards_copy_category, backwards_copy_category),
        migrations.RemoveField(
            model_name='request',
            name='category',
        ),
        migrations.RenameField(
            model_name='request',
            old_name='category_new',
            new_name='category',
        ),
        migrations.AlterField(
            model_name='request',
            name='category',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='requests', to='workshop.category'),
        ),
    ]
