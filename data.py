from mongoengine import *
from datetime import datetime
from mongoenginepagination import Document
import os, bcrypt, sys

if os.getenv('USE_MLAB'):
    connect('heroku_app8846523', host=os.getenv('MONGOLAB_URI', 'mongodb://localhost:27017'))
else:
    connect('sandyredux', host='hydr0.com') #Dev server

class Provider(Document):
    # Basic Info
    name = StringField()
    title = StringField()
    orgname = StringField()
    email = StringField()
    phone = StringField()
    #location = GeoPointField() #Not sure if we'll use this, but hey its there

    # More info
    locations = ListField()
    support = ListField()
    grade = ListField()
    delivery = ListField()
    timeframe = StringField()
    cost = ListField()

    active = BooleanField(default=True)

    def nicefield(self, f):
        li = []
        for i in getattr(self, f):
            li.append(i.replace('_', ' ').title())
        return ', '.join(li)

class School(Document):
    contactname = StringField()
    needs = StringField()
    location =StringField()
    schoolname = StringField()
    contactphone = StringField()
    contactemail = StringField()

    active = BooleanField(default=True)

class Admin(Document):
    username = StringField()
    password = StringField()

if __name__ == '__main__':
    if len(sys.argv) >= 3:
        obj = Admin(username=sys.argv[1], password=bcrypt.hashpw(sys.argv[2], bcrypt.gensalt(12)))
        obj.save()
