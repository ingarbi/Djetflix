

class CourseGrade():
    student -> FK(student)
    course -> FK(course)


class CourseAttendance():
    student -> FK(student)
    course -> FK(course)
    datetime -> DateTime


class Course():
    students -> M2M( )
    # course_obj.coursegrade_set.all()
    # course_obj.courseattendence_set.all(0)

class Parent():
    name
    # parent_obj.student_set.all()

class Student():
    mother = FK(parent, related_name='mother')
    father = FK(parent, related_name='father')
    # student.course_set.all()
    # student.coursegrade_set.all()
    # student.father
    # student.mother




## Playlist of Playlists


```python
from playlists.models import Playlist
the_office = Playlist.objects.create(title='The Office Series')
# featured video / videos / 
season_1 = Playlist.objects.create(title='The Office Series Season 1', parent=the_office, order=1)
# featured video / videos / 
season_2 = Playlist.objects.create(title='The Office Series Season 2', parent=the_office, order=2)
# featured video / videos / 
season_3 = Playlist.objects.create(title='The Office Series Season 3', parent=the_office, order=3)
# featured video / videos / 
shows = Playlist.objects.filter(parent__isnull=True)
show = Playlist.objects.get(id=1)
# seasons = Playlist.objects.filter(parent=show)