from django.contrib import admin

from apps.website.models import AboutSection, Achievement, HeroSlide, SuccessfulStudent


@admin.register(HeroSlide)
class HeroSlideAdmin(admin.ModelAdmin):
    list_display = ("title", "order", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("title", "subtitle", "caption")
    ordering = ("order",)


@admin.register(AboutSection)
class AboutSectionAdmin(admin.ModelAdmin):
    list_display = ("headline", "updated_at")

    def has_add_permission(self, request):
        return not AboutSection.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ("title", "year", "metric", "order", "is_active")
    list_filter = ("year", "is_active")
    search_fields = ("title", "description")


@admin.register(SuccessfulStudent)
class SuccessfulStudentAdmin(admin.ModelAdmin):
    list_display = ("full_name", "academic_year", "student_class", "result", "is_featured", "is_active")
    list_filter = ("academic_year", "is_featured", "is_active")
    search_fields = ("full_name", "result", "achievement")
