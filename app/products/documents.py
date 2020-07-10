from django_elasticsearch_dsl import Document, Index, fields

from .models import Product

product_index = Index('products')


@product_index.doc_type
class ProductDocument(Document):
    name = fields.TextField(
        attr='name',
        fields={
            'suggest': fields.Completion(),
        }
    )
    url = fields.TextField(attr='get_absolute_url_str')

    class Django:
        model = Product
        fields = [
            'id',
            'thumbnail',
        ]

    def get_queryset(self):
        return super().get_queryset()
