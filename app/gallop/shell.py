from products.models import Product
from products.serializers import ProductSerializer
from rest_framework.renderers import JSONRenderer

# This file is to run and test function from shell
# from gallop.shell import *


# Template
def tX():
    import traceback
    print("\n{}\n".format(traceback.extract_stack(None, 2)[1][2]))
    # Code goes here

    # End of code section
    print("\n")


# Display serialized one product
def t1():
    import traceback
    print("\n{}\n".format(traceback.extract_stack(None, 2)[1][2]))
    # Code goes here

    product = Product.objects.all()[0]
    serializer = ProductSerializer()
    data = serializer.to_representation(product)
    renderer = JSONRenderer()

    # End of code section
    print(renderer.render(data))

    print("\n")


t1()
