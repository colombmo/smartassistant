from django.db import models

# User
class User(models.Model):
	userId = models.CharField(max_length=100)
	
	def __str__(self):
		return self.userId

# Actuator Brand
class Brand(models.Model):
	name = models.CharField(max_length=100)
	logo = models.ImageField(upload_to="brand_logos/")
	
	def __str__(self):
		return self.name

# Actuator
class Actuator(models.Model):
	brand = models.ForeignKey(Brand, on_delete = models.CASCADE)
	name = models.CharField(max_length=100)
	minimum = models.IntegerField(default=0)
	maximum = models.IntegerField(default=100)
	units = models.CharField(max_length=15, default="%")
	
	def __str__(self):
		return str(self.brand) + "-" + self.name
	
# This
class This(models.Model):
	originalcommand = models.CharField(max_length=1000)
	command = models.CharField(max_length=1000)
	variable = models.CharField(max_length=100)
	category = models.CharField(max_length=100)
	
	def __str__(self):
		return self.originalcommand

# That
class That(models.Model):
	actuator = models.ForeignKey(Actuator, on_delete = models.CASCADE)
	value = models.IntegerField(default=50)
	
	def __str__(self):
		return str(self.actuator) + ": " + str(self.value)

# Rules
class Rule(models.Model):
	# IF this then that
	user = models.ForeignKey(User, on_delete = models.CASCADE)
	this = models.ForeignKey(This, on_delete = models.CASCADE)
	that = models.ForeignKey(That, on_delete = models.CASCADE)
	
	def __str__(self):
		return "IF " + str(self.this) + " THEN " + str(self.that)