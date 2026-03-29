from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj == request.user or request.user.is_staff


class IsTeacher(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role in ["teacher", "admin"] or request.user.is_staff


class IsStudent(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role == "student"


class IsParent(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role == "parent"


class IsStudentOrParent(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role in ["student", "parent"]


class IsOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        if hasattr(obj, "user"):
            return obj.user == request.user or request.user.is_staff
        return False


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role == "admin" or request.user.is_staff


class IsClassroomTeacher(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        if hasattr(obj, "teacher"):
            return obj.teacher == request.user or request.user.is_staff
        return False


class IsClassroomMember(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.role == "admin" or request.user.is_staff:
            return True
        if hasattr(obj, "enrollments"):
            return obj.enrollments.filter(student=request.user, is_active=True).exists()
        if hasattr(obj, "classroom"):
            return obj.classroom.enrollments.filter(
                student=request.user, is_active=True
            ).exists()
        return False


class CanManageClassroom(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.role == "admin" or request.user.is_staff:
            return True
        if hasattr(obj, "teacher"):
            return obj.teacher == request.user
        return False
