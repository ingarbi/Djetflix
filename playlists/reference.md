

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