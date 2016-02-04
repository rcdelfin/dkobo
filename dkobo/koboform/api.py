from rest_framework import viewsets
from django.core.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from models import SurveyDraft, SurveyPreview
from serializers import ListSurveyDraftSerializer, DetailSurveyDraftSerializer, TagSerializer
from django.shortcuts import render_to_response, HttpResponse, get_object_or_404
from django.contrib.contenttypes.models import ContentType
from taggit.models import Tag
from dkobo.koboform import pyxform_utils


class SurveyAssetViewset(viewsets.ModelViewSet):
    model = SurveyDraft
    serializer_class = ListSurveyDraftSerializer
    exclude_asset_type = False

    def get_queryset(self):
        user = self.request.user
        if user.is_anonymous():
            raise PermissionDenied
        queryset = SurveyDraft.objects.filter(user=user)
        if self.exclude_asset_type:
            queryset = queryset.exclude(asset_type=None)
        else:
            queryset = queryset.filter(asset_type=None)
        return queryset.order_by('-date_modified')

    def create(self, request):
        user = self.request.user
        if user.is_anonymous():
            raise PermissionDenied
        contents = request.data
        tags = contents.get('tags', [])
        if 'tags' in contents:
            del contents['tags']

        survey_draft = request.user.survey_drafts.create(**contents)

        for tag in tags:
            survey_draft.tags.add(tag)

        return Response(ListSurveyDraftSerializer(survey_draft).data)

    def retrieve(self, request, pk=None):
        user = request.user
        queryset = SurveyDraft.objects.filter(user=user)
        survey_draft = get_object_or_404(queryset, pk=pk)
        return Response(DetailSurveyDraftSerializer(survey_draft).data)

class TagViewset(viewsets.ModelViewSet):
    model = Tag
    serializer_class = TagSerializer
    _survey_draft_content_type = ContentType.objects.get_for_model(SurveyDraft)

    def get_queryset(self, *args, **kwargs):
        user = self.request.user
        if user.is_authenticated():
            ids = user.survey_drafts.all().values_list('id', flat=True)
            return Tag.objects.filter(
                taggit_taggeditem_items__object_id__in=ids,
                taggit_taggeditem_items__content_type=self._survey_draft_content_type
            ).distinct()
        else:
            return Tag.objects.none()

    def destroy(self, request, pk):
        if request.user.is_authenticated():
            tag = Tag.objects.get(id=pk)
            items = SurveyDraft.objects.filter(user=request.user, tags__name=tag.name)
            for item in items:
                item.tags.remove(tag)
            return HttpResponse("", status="204")

class LibraryAssetViewset(SurveyAssetViewset):
    exclude_asset_type = True
    serializer_class = DetailSurveyDraftSerializer
    class LibraryAssetPagination(PageNumberPagination):
        page_size = 100
    pagination_class = LibraryAssetPagination


class SurveyDraftViewSet(SurveyAssetViewset):
    exclude_asset_type = False
