_STUDENT_LESSON_URL = "https://lk.100points.ru/student/lesson/{}"


# What a student opens: the platform shows the lesson with its homework to those who have access.
def platform_lesson_url(lesson_id: int) -> str:
    return _STUDENT_LESSON_URL.format(lesson_id)
