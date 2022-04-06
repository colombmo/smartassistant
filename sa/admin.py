from django.contrib import admin
from .models import User, This, That, Brand, Actuator, Rule

admin.site.register(User)
admin.site.register(Brand)
admin.site.register(Actuator)
admin.site.register(This)
admin.site.register(That)
admin.site.register(Rule)
