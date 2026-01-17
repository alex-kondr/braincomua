import sys
import os
import django

sys.path.append('C:\\Python\\Projects\\braincomua_project')
os.environ['DJANGO_SETTINGS_MODULE'] = 'braincomua_project.settings'
django.setup()