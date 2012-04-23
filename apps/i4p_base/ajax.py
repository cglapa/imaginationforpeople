from django.db.models import Count
from django.contrib import comments
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_GET

from apps.project_sheet.models import I4pProject, I4pProjectTranslation
from apps.project_sheet.utils import get_project_translations_from_parents



def _slider_make_response(request, queryset):
    count = int(request.GET.get('count', 14))
    project_translations = get_project_translations_from_parents(parents_qs=queryset[:count],
                                                                 language_code=request.LANGUAGE_CODE)
    
    return render_to_response(template_name='home-blocks/slider.html',
                              dictionary={'project_translations': project_translations},
                              context_instance=RequestContext(request))
    
@require_GET
@cache_page(60 * 5)
def slider_bestof(request):
    """
    Get the "count" bestof projects at random
    """
    return _slider_make_response(request,
                                 queryset=I4pProject.objects.filter(best_of=True).order_by('?'))



@require_GET
@cache_page(60 * 5)
def slider_latest(request):
    """
    Get the "count" latests projects, sorted by creation time
    """
    return _slider_make_response(request,
                                 queryset=I4pProject.objects.order_by('-created'))


@require_GET
@cache_page(60 * 5)
def slider_most_commented(request):
    """
    Get the most commented projects
    """
    count = int(request.GET.get('count', 14))
    
    i4pprojecttranslation_type = ContentType.objects.get_for_model(I4pProjectTranslation)
    comment_model = comments.get_model()

    req = comment_model.objects.filter(content_type__pk=i4pprojecttranslation_type.id).values('object_pk').annotate(comment_count=Count('object_pk')).order_by("-comment_count")
    project_translations = I4pProjectTranslation.objects.filter(id__in=[x['object_pk'] for x in req])
    
    return render_to_response(template_name='home-blocks/slider.html',
                              dictionary={'project_translations': project_translations},
                              context_instance=RequestContext(request))








