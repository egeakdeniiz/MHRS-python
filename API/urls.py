from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("iller", views.IlViewSet, basename="il")
router.register("ilceler", views.IlceViewSet, basename="ilce")
router.register("hastaneler", views.HastaneViewSet, basename="hastane")
router.register("klinikler", views.KlinikViewSet, basename="klinik")
router.register("hekimler", views.HekimViewSet, basename="hekim")
router.register("randevular", views.RandevuViewSet, basename="randevu")
router.register("gecici-tutmalar", views.GeciciTutmaViewSet, basename="gecici-tutma")
router.register("bekleme-talepleri", views.BeklemeTalebiViewSet, basename="bekleme-talebi")
router.register("bildirimler", views.BildirimViewSet, basename="bildirim")
router.register("hekim/randevular", views.HekimRandevuViewSet, basename="hekim-randevu")
router.register("yonetim/randevular", views.HastaneRandevuViewSet, basename="yonetim-randevu")

urlpatterns = [
    path("auth/kayit/", views.KayitView.as_view(), name="api_kayit"),
    path("auth/token/", views.TokenGirisView.as_view(), name="api_token"),
    path("auth/cikis/", views.CikisView.as_view(), name="api_cikis"),
    path("auth/web-kodu/", views.WebKoduView.as_view(), name="api_web_kodu"),
    path("auth/ben/", views.BenView.as_view(), name="api_ben"),
    path("slotlar/", views.SlotListView.as_view(), name="api_slotlar"),
    path("yonetim/rapor/", views.RaporOzetView.as_view(), name="api_rapor"),
    path("schema/", SpectacularAPIView.as_view(), name="api_schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="api_schema"), name="api_docs"),
    path("redoc/", SpectacularRedocView.as_view(url_name="api_schema"), name="api_redoc"),
    path("", include(router.urls)),
]
