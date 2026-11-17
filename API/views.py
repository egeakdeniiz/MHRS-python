from datetime import date, timedelta

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics, mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from accounts.denetim import denetim_kaydet
from accounts.mobil import WEB_KODU_SURE, giris_kilitli_mi, kilit_mesaji, web_kodu_uret
from accounts.models import Rol
from merkez.models import Hastane, Hekim, Il, Ilce, Klinik
from panel import raporlar
from randevu import services
from randevu.models import AKTIF_DURUMLAR, BeklemeTalebi, Bildirim, GeciciTutma, Randevu, RandevuDurum
from randevu.services import RandevuHatasi
from randevu.slotlar import bos_slotlari_bul, simdi_yerel

from . import serializers as s
from .permissions import HastaneYoneticisiIzni, HekimIzni, VatandasIzni, YoneticiIzni


def hata(e):
    return Response({"hata": str(e)}, status=status.HTTP_400_BAD_REQUEST)


def _int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _tarih(v):
    try:
        return date.fromisoformat(v) if v else None
    except ValueError:
        return None


# --------------------------------------------------------------------------
# Kimlik
# --------------------------------------------------------------------------
class KayitView(generics.CreateAPIView):
    """Vatandaş kaydı (kimlik doğrulama gerektirmez)."""

    serializer_class = s.KayitSerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes = []  # kimlik gerektirmez; cihazdaki eski oturum çerezi CSRF hatasına yol açmasın

    def perform_create(self, serializer):
        u = serializer.save()
        denetim_kaydet(u, "VATANDAS_KAYIT", u, "API", request=self.request)


class BenView(generics.RetrieveUpdateAPIView):
    """Oturumdaki kullanıcının profili."""

    serializer_class = s.KullaniciSerializer

    def get_object(self):
        return self.request.user


# --------------------------------------------------------------------------
# Merkezi yapı (herkese açık, salt okunur)
# --------------------------------------------------------------------------
class TokenGirisView(ObtainAuthToken):
    """Mobil giriş: token + kullanıcı bilgisi döner. Hatalı deneme kilidi web girişiyle aynıdır."""

    throttle_classes = [AnonRateThrottle]
    authentication_classes = []  # kimlik gerektirmez; cihazdaki eski oturum çerezi CSRF hatasına yol açmasın

    def post(self, request, *args, **kwargs):
        if giris_kilitli_mi(str(request.data.get("username", ""))):
            return Response({"hata": kilit_mesaji()}, status=429)
        ser = self.serializer_class(data=request.data, context={"request": request})
        if not ser.is_valid():
            return Response({"hata": "T.C. Kimlik No / kullanıcı adı veya şifre hatalı."}, status=400)
        kullanici = ser.validated_data["user"]
        token, _ = Token.objects.get_or_create(user=kullanici)
        denetim_kaydet(kullanici, "GIRIS_MOBIL", request=request)
        return Response({"token": token.key, "kullanici": s.KullaniciSerializer(kullanici).data})


class CikisView(APIView):
    """Mobil çıkış: token silinir."""

    @extend_schema(request=None, responses={204: None})
    def post(self, request):
        Token.objects.filter(user=request.user).delete()
        denetim_kaydet(request.user, "CIKIS_MOBIL", request=request)
        return Response(status=204)


class WebKoduView(APIView):
    """Mobil uygulamanın web panelini WebView içinde oturum açık göstermesi için tek kullanımlık kod."""

    @extend_schema(request=None)
    def post(self, request):
        return Response({"kod": web_kodu_uret(request.user), "gecerlilik_saniye": WEB_KODU_SURE})


class IlViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Il.objects.all()
    serializer_class = s.IlSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None


class IlceViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = s.IlceSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None

    @extend_schema(parameters=[OpenApiParameter("il", int)])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        qs = Ilce.objects.all()
        if _int(self.request.query_params.get("il")):
            qs = qs.filter(il_id=_int(self.request.query_params["il"]))
        return qs


class HastaneViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = s.HastaneSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None

    @extend_schema(parameters=[OpenApiParameter("il", int), OpenApiParameter("ilce", int),
                               OpenApiParameter("klinik", int)])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        p = self.request.query_params
        qs = Hastane.objects.filter(aktif=True).select_related("ilce__il")
        if _int(p.get("il")):
            qs = qs.filter(ilce__il_id=_int(p["il"]))
        if _int(p.get("ilce")):
            qs = qs.filter(ilce_id=_int(p["ilce"]))
        if _int(p.get("klinik")):
            qs = qs.filter(hastane_klinikleri__klinik_id=_int(p["klinik"]), hastane_klinikleri__aktif=True)
        return qs.distinct()


class KlinikViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = s.KlinikSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None

    @extend_schema(parameters=[OpenApiParameter("hastane", int)])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        qs = Klinik.objects.filter(aktif=True)
        if _int(self.request.query_params.get("hastane")):
            qs = qs.filter(hastane_klinikleri__hastane_id=_int(self.request.query_params["hastane"]),
                           hastane_klinikleri__aktif=True)
        return qs.distinct()


class HekimViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = s.HekimSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None

    @extend_schema(parameters=[OpenApiParameter("hastane", int), OpenApiParameter("klinik", int)])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        p = self.request.query_params
        qs = Hekim.objects.filter(aktif=True).select_related("kullanici", "uzmanlik")
        if _int(p.get("hastane")) or _int(p.get("klinik")):
            atama = {"atamalar__aktif": True}
            if _int(p.get("hastane")):
                atama["atamalar__hastane_id"] = _int(p["hastane"])
            if _int(p.get("klinik")):
                atama["atamalar__klinik_id"] = _int(p["klinik"])
            qs = qs.filter(**atama)
        return qs.distinct()


# --------------------------------------------------------------------------
# Slot arama
# --------------------------------------------------------------------------
class SlotListView(APIView):
    """Boş randevu slotları. klinik zorunludur; hekim boşsa klinikteki tüm hekimler döner."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        parameters=[OpenApiParameter(n, t, required=(n == "klinik")) for n, t in
                    [("klinik", int), ("il", int), ("ilce", int), ("hastane", int), ("hekim", int),
                     ("baslangic", str), ("bitis", str)]],
        responses=s.SlotSerializer(many=True),
    )
    def get(self, request):
        p = request.query_params
        klinik = _int(p.get("klinik"))
        if not klinik:
            return Response({"hata": "klinik parametresi zorunludur."}, status=400)
        slotlar = bos_slotlari_bul(il=_int(p.get("il")), ilce=_int(p.get("ilce")), hastane=_int(p.get("hastane")),
                                   klinik=klinik, hekim=_int(p.get("hekim")), baslangic=_tarih(p.get("baslangic")),
                                   bitis=_tarih(p.get("bitis")))
        return Response(s.SlotSerializer(slotlar, many=True).data)


# --------------------------------------------------------------------------
# Vatandaş: randevular, bekleme talepleri, bildirimler
# --------------------------------------------------------------------------
class RandevuViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = s.RandevuSerializer
    permission_classes = [VatandasIzni]

    @extend_schema(parameters=[OpenApiParameter("tur", str, enum=["aktif", "gecmis"])])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        qs = Randevu.objects.filter(vatandas=self.request.user).select_related("hastane", "klinik",
                                                                                "hekim__kullanici")
        tur = self.request.query_params.get("tur")
        if tur == "aktif":
            qs = qs.filter(durum__in=AKTIF_DURUMLAR)
        elif tur == "gecmis":
            qs = qs.exclude(durum__in=AKTIF_DURUMLAR)
        return qs

    @extend_schema(request=s.RandevuOlusturSerializer, responses={201: s.RandevuSerializer})
    def create(self, request):
        ser = s.RandevuOlusturSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        talep = None
        if d.get("bekleme_talebi"):
            talep = BeklemeTalebi.objects.filter(pk=d["bekleme_talebi"], vatandas=request.user).first()
        try:
            r = services.randevu_olustur(request.user, d["hekim"], d["hastane"], d["klinik"], d["tarih"],
                                         d["baslangic"], bekleme_talebi=talep, request=request)
        except RandevuHatasi as e:
            return hata(e)
        return Response(s.RandevuSerializer(r).data, status=201)

    @extend_schema(request=s.IptalSerializer, responses=s.RandevuSerializer)
    @action(detail=True, methods=["post"])
    def iptal(self, request, pk=None):
        r = self.get_object()
        ser = s.IptalSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            r = services.randevu_iptal(r, request.user, neden=ser.validated_data.get("neden", ""), request=request)
        except RandevuHatasi as e:
            return hata(e)
        return Response(s.RandevuSerializer(r).data)

    @extend_schema(request=None, responses=s.RandevuSerializer)
    @action(detail=True, methods=["post"])
    def onayla(self, request, pk=None):
        try:
            r = services.randevu_onayla(self.get_object(), request.user, request=request)
        except RandevuHatasi as e:
            return hata(e)
        return Response(s.RandevuSerializer(r).data)

    @extend_schema(request=s.RandevuDegistirSerializer, responses=s.RandevuSerializer)
    @action(detail=True, methods=["post"])
    def degistir(self, request, pk=None):
        r = self.get_object()
        ser = s.RandevuDegistirSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        try:
            yeni = services.randevu_degistir(r, request.user, d["hekim"], d["hastane"], r.klinik_id, d["tarih"],
                                             d["baslangic"], request=request)
        except RandevuHatasi as e:
            return hata(e)
        return Response(s.RandevuSerializer(yeni).data)


class GeciciTutmaViewSet(mixins.RetrieveModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    """Onaylı iki adımlı randevu alma.

    1. POST /gecici-tutmalar/ : seçilen saat merkezi kuraldaki süre kadar (varsayılan 5 dk) tutulur.
    2. POST /gecici-tutmalar/{id}/onayla/ : süre dolmadıysa randevu oluşur (veya değişiklik yapılır).
    DELETE /gecici-tutmalar/{id}/ : vazgeç, saat hemen serbest kalır.
    """

    serializer_class = s.GeciciTutmaSerializer
    permission_classes = [VatandasIzni]

    def get_queryset(self):
        return GeciciTutma.objects.filter(vatandas=self.request.user).select_related("hastane", "klinik",
                                                                                     "hekim__kullanici")

    @extend_schema(request=s.SlotTutSerializer, responses={201: s.GeciciTutmaSerializer})
    def create(self, request):
        ser = s.SlotTutSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        degistir = None
        if d.get("degistir"):
            degistir = get_object_or_404(Randevu, pk=d["degistir"], vatandas=request.user)
        talep = None
        if d.get("bekleme_talebi"):
            talep = BeklemeTalebi.objects.filter(pk=d["bekleme_talebi"], vatandas=request.user).first()
        try:
            tutma = services.slot_tut(request.user, d["hekim"], d["hastane"], d["klinik"], d["tarih"],
                                      d["baslangic"], degistirilen=degistir, bekleme_talebi=talep)
        except RandevuHatasi as e:
            return hata(e)
        return Response(s.GeciciTutmaSerializer(tutma).data, status=201)

    @extend_schema(request=None, responses={201: s.RandevuSerializer})
    @action(detail=True, methods=["post"])
    def onayla(self, request, pk=None):
        try:
            r = services.tutmayi_onayla(_int(pk), request.user, request=request)
        except RandevuHatasi as e:
            return hata(e)
        return Response(s.RandevuSerializer(r).data, status=201)

    def destroy(self, request, *args, **kwargs):
        services.tutma_birak(_int(kwargs.get("pk")), request.user)
        return Response(status=204)


class BeklemeTalebiViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin,
                           viewsets.GenericViewSet):
    serializer_class = s.BeklemeTalebiSerializer
    permission_classes = [VatandasIzni]

    def get_queryset(self):
        return BeklemeTalebi.objects.filter(vatandas=self.request.user).select_related("klinik")

    def create(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        try:
            t = services.bekleme_talebi_olustur(request.user, d["klinik"], d["baslangic_tarihi"], d["bitis_tarihi"],
                                                il=d.get("il"), ilce=d.get("ilce"), hastane=d.get("hastane"),
                                                hekim=d.get("hekim"), request=request)
        except RandevuHatasi as e:
            return hata(e)
        return Response(s.BeklemeTalebiSerializer(t).data, status=201)

    @extend_schema(request=None)
    @action(detail=True, methods=["post"])
    def iptal(self, request, pk=None):
        try:
            t = services.bekleme_talebi_iptal(self.get_object(), request.user, request=request)
        except RandevuHatasi as e:
            return hata(e)
        return Response(s.BeklemeTalebiSerializer(t).data)

    @extend_schema(responses=s.SlotSerializer(many=True))
    @action(detail=True, methods=["get"])
    def uygun_slotlar(self, request, pk=None):
        """Talebe uyan güncel boş slotlar (bildirim sonrası vatandaş buradan seçip onaylar)."""
        return Response(s.SlotSerializer(services.talep_icin_slotlar(self.get_object()), many=True).data)


class BildirimViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = s.BildirimSerializer

    def get_queryset(self):
        qs = Bildirim.objects.filter(kullanici=self.request.user)
        if self.request.query_params.get("okunmamis") == "1":
            qs = qs.filter(okundu=False)
        return qs

    @extend_schema(request=None)
    @action(detail=True, methods=["post"])
    def okundu(self, request, pk=None):
        b = get_object_or_404(Bildirim, pk=pk, kullanici=request.user)
        b.okundu = True
        b.save(update_fields=["okundu"])
        return Response(s.BildirimSerializer(b).data)

    @extend_schema(request=None)
    @action(detail=False, methods=["post"])
    def tumunu_okundu(self, request):
        n = Bildirim.objects.filter(kullanici=request.user, okundu=False).update(okundu=True)
        return Response({"guncellenen": n})


# --------------------------------------------------------------------------
# Hekim
# --------------------------------------------------------------------------
class HekimRandevuViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = s.HekimRandevuSerializer
    permission_classes = [HekimIzni]

    @extend_schema(parameters=[OpenApiParameter("baslangic", str), OpenApiParameter("bitis", str)])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        bugun = simdi_yerel().date()
        p = self.request.query_params
        bas = _tarih(p.get("baslangic")) or bugun
        bit = _tarih(p.get("bitis")) or bas
        return Randevu.objects.filter(hekim=self.request.user.hekim, tarih__range=(bas, bit)) \
            .exclude(durum=RandevuDurum.IPTAL).select_related("vatandas", "hastane", "klinik", "hekim__kullanici") \
            .order_by("tarih", "baslangic_saati")

    @extend_schema(request=s.MuayeneDurumSerializer, responses=s.HekimRandevuSerializer)
    @action(detail=True, methods=["post"])
    def durum(self, request, pk=None):
        r = get_object_or_404(Randevu, pk=pk, hekim=request.user.hekim)
        ser = s.MuayeneDurumSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            r = services.muayene_durumu_isle(r, request.user, ser.validated_data["durum"], request=request)
        except RandevuHatasi as e:
            return hata(e)
        return Response(s.HekimRandevuSerializer(r).data)


# --------------------------------------------------------------------------
# Yönetim
# --------------------------------------------------------------------------
class HastaneRandevuViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """Hastane yöneticisi: yalnızca kendi hastanesinin randevuları (veri izolasyonu)."""

    serializer_class = s.HekimRandevuSerializer
    permission_classes = [HastaneYoneticisiIzni]

    @extend_schema(parameters=[OpenApiParameter(n, t) for n, t in
                               [("baslangic", str), ("bitis", str), ("klinik", int), ("hekim", int), ("durum", str)]])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        bugun = simdi_yerel().date()
        p = self.request.query_params
        bas = _tarih(p.get("baslangic")) or bugun
        bit = _tarih(p.get("bitis")) or bas + timedelta(days=7)
        qs = Randevu.objects.filter(hastane_id=self.request.user.hastane_id, tarih__range=(bas, bit))
        if _int(p.get("klinik")):
            qs = qs.filter(klinik_id=_int(p["klinik"]))
        if _int(p.get("hekim")):
            qs = qs.filter(hekim_id=_int(p["hekim"]))
        if p.get("durum"):
            qs = qs.filter(durum=p["durum"])
        return qs.select_related("vatandas", "hastane", "klinik", "hekim__kullanici").order_by("tarih",
                                                                                               "baslangic_saati")

    @extend_schema(request=s.IptalSerializer, responses=s.HekimRandevuSerializer)
    @action(detail=True, methods=["post"])
    def iptal(self, request, pk=None):
        r = get_object_or_404(Randevu, pk=pk, hastane_id=request.user.hastane_id)
        ser = s.IptalSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            r = services.randevu_iptal(r, request.user, neden=ser.validated_data.get("neden", ""), request=request)
        except RandevuHatasi as e:
            return hata(e)
        return Response(s.HekimRandevuSerializer(r).data)


class RaporOzetView(APIView):
    """Rapor özeti. Hastane yöneticisi yalnızca kendi hastanesini, sistem yöneticisi tümünü görür."""

    permission_classes = [YoneticiIzni]

    @extend_schema(parameters=[OpenApiParameter(n, t) for n, t in
                               [("baslangic", str), ("bitis", str), ("periyot", str), ("hastane", int),
                                ("il", int)]])
    def get(self, request):
        bugun = simdi_yerel().date()
        p = request.query_params
        bas = _tarih(p.get("baslangic")) or bugun - timedelta(days=29)
        bit = _tarih(p.get("bitis")) or bugun
        if bit < bas or (bit - bas).days > 366:
            return Response({"hata": "Geçersiz tarih aralığı."}, status=400)
        u = request.user
        if u.rol == Rol.HASTANE_YONETICISI and not u.is_superuser:
            hastane, il = u.hastane, None
        else:
            hastane = Hastane.objects.filter(pk=_int(p.get("hastane"))).first() if p.get("hastane") else None
            il = Il.objects.filter(pk=_int(p.get("il"))).first() if p.get("il") else None
        r = raporlar.rapor_olustur(bas, bit, p.get("periyot", "gun"), hastane=hastane, il=il)
        r["doluluk"]["bitis"] = r["doluluk"]["bitis"].isoformat()
        r["baslangic"], r["bitis"] = bas.isoformat(), bit.isoformat()
        return Response(r)
