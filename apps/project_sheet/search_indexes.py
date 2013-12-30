from django.conf import settings
from django.utils.encoding import force_unicode

from haystack import indexes

from apps.forum.models import SpecificQuestion, SpecificQuestionType

from .models import I4pProject, I4pProjectTranslation, Topic, Answer

class I4pProjectIndex(indexes.SearchIndex, indexes.Indexable):
    #text = indexes.MultiValueField(document=True, use_template=False)
    text = indexes.CharField(document=True, use_template=False)
    title = indexes.MultiValueField(indexed=False)
    #baseline = indexes.CharField(model_attr='baseline')
    #For some reason MultiValueField doesn't work properly with whoosh
    #language_codes = indexes.CharField(indexed=True, stored=True)
    language_codes = indexes.MultiValueField(indexed=True, stored=True)
    #slug = indexes.CharField(model_attr='slug')
    #content_auto = indexes.EdgeNgramField(model_attr='title')
    best_of = indexes.BooleanField(model_attr='best_of')
    status = indexes.CharField(model_attr='status', null=True)
    sites = indexes.MultiValueField()
    tags = indexes.MultiValueField(indexed=True, stored=True)
    countries = indexes.MultiValueField(indexed=True, stored=True)
    has_team = indexes.BooleanField()
    has_needs = indexes.BooleanField()
    created = indexes.DateTimeField(model_attr='created')
    
    def get_model(self):
        return I4pProject

    def read_queryset(self, using=None):
        return I4pProject.objects.untranslated().all()
        
    def prepare_sites(self, obj):
        return [obj.id for obj in obj.site.all()]

    def prepare_language_codes(self, obj):
        return obj.get_available_languages()

    def prepare_text(self, obj):
        """
        The textual content of the project
        """
        languages = obj.get_available_languages()
        retval = []
        for language in languages:
            translated_project = self.get_model().objects.language(language).get(pk=obj.pk)
            retval.append(translated_project.title)
            retval.append(translated_project.baseline)
            # Fetch questions
            questions_content = []
            
            for topic in Topic.objects.language(language).filter(site_topics__projects=translated_project):
                questions_content.append(topic.label)
                for question in topic.questions.language(language).all().order_by('weight'):
                    answers = Answer.objects.language(language).filter(project=translated_project, question=question)
                    if len(answers) >= 1:
                        #We only want the question text if there are answers
                        questions_content.append(question.content)
                        questions_content.extend([answer.content for answer in answers])
            retval.extend(questions_content)
        return '\n'.join(retval)
    def prepare_title(self, obj):
        languages = obj.get_available_languages()
        titles = []
        for language in languages:
            translated_project = self.get_model().objects.language(language).get(pk=obj.pk)
            title = (language, translated_project.title)
            titles.append(title)
        return titles
    def prepare_has_team(self, obj):
        """
        If there is at least one user associated with this project
        """
        return obj.members.count() > 0

    def prepare_has_needs(self, obj):
        """
        If the project has expressed needs
        """
        #FIXME:  django-hvad does NOT support foreign keys on translated models
        #At least we don't try to use it until this is ported properly
        translations = I4pProjectTranslation.objects.filter(master=obj.id)
        projectsupport_count = 0
        for translated_project in translations:
			projectsupport_count += SpecificQuestion.objects.filter(type__in=SpecificQuestionType.objects.filter(type="pj-help"), object_id=translated_project.pk).count()
			projectsupport_count += SpecificQuestion.objects.filter(type__in=SpecificQuestionType.objects.filter(type="pj-need"), object_id=translated_project.pk).count()
        return projectsupport_count > 0
        
    def prepare_tags(self, obj):
        """
        Split tags by comma, strip and remove empty
        """
        languages = obj.get_available_languages()
        taglist = []
        for language in languages:
            translated_project = self.get_model().objects.language(language).get(pk=obj.pk)
            taglist.extend(translated_project.themes.split(','))
        return set([tag.strip() for tag in taglist if tag.strip()])

    def prepare_countries(self, obj):
        if obj.locations:
            return [location.country.code for location in obj.locations.all()]
        else:
            return None
