from django.contrib import admin
from .models import Lesson,Hometask,Exam,Settings,Time,Image,Day,Subject,Plan,Holiday

admin.site.register(Hometask)
admin.site.register(Exam)
admin.site.register(Settings)
admin.site.register(Time)
admin.site.register(Image)
admin.site.register(Day)
admin.site.register(Subject)
admin.site.register(Plan)
admin.site.register(Holiday)

from django_summernote.admin import SummernoteModelAdmin

class LessonAdmin(SummernoteModelAdmin):
    summernote_fields = ('notes',)

admin.site.register(Lesson,LessonAdmin)