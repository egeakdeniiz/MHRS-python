from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from accounts.models import Kullanici, Rol
from accounts.validators import tc_kimlik_dogrula
from merkez.models import Hastane, Hekim, Il, Ilce, Klinik
from randevu.models import BeklemeTalebi, Bildirim, GeciciTutma, Randevu, RandevuDurum


class IlSerializer(serializers.ModelSerializer):
    class Meta:
        model = Il
        fields = ("id", "ad", "plaka_kodu")


class IlceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ilce
        fields = ("id", "ad", "il")


class HastaneSerializer(serializers.ModelSerializer):
    il = serializers.IntegerField(source="ilce.il_id", read_only=True)
    il_adi = serializers.CharField(source="ilce.il.ad", read_only=True)
    ilce_adi = serializers.CharField(source="ilce.ad", read_only=True)

    class Meta:
        model = Hastane
        fields = ("id", "ad", "tur", "ilce", "ilce_adi", "il", "il_adi", "adres", "telefon")


class KlinikSerializer(serializers.ModelSerializer):
    class Meta:
        model = Klinik
        fields = ("id", "ad", "aciklama")


class HekimSerializer(serializers.ModelSerializer):
    ad_soyad = serializers.CharField(source="__str__", read_only=True)
    uzmanlik_adi = serializers.CharField(source="uzmanlik.ad", read_only=True)

    class Meta:
        model = Hekim
        fields = ("id", "ad_soyad", "unvan", "uzmanlik", "uzmanlik_adi")


class SlotSerializer(serializers.Serializer):
    hekim_id = serializers.IntegerField()
    hekim_adi = serializers.CharField()
    hastane_id = serializers.IntegerField()
    hastane_adi = serializers.CharField()
    klinik_id = serializers.IntegerField()
    klinik_adi = serializers.CharField()
    tarih = serializers.DateField()
    baslangic = serializers.TimeField(format="%H:%M")
    bitis = serializers.TimeField(format="%H:%M")


class RandevuSerializer(serializers.ModelSerializer):
    durum_adi = serializers.CharField(source="get_durum_display", read_only=True)
    hastane_adi = serializers.CharField(source="hastane.ad", read_only=True)
    klinik_adi = serializers.CharField(source="klinik.ad", read_only=True)
    hekim_adi = serializers.CharField(source="hekim.__str__", read_only=True)

    class Meta:
        model = Randevu
        fields = ("id", "tarih", "baslangic_saati", "bitis_saati", "durum", "durum_adi", "hastane", "hastane_adi",
                  "klinik", "klinik_adi", "hekim", "hekim_adi", "olusturma_zamani", "onay_zamani", "iptal_zamani",
                  "iptal_nedeni", "onceki_randevu")
        read_only_fields = fields


class HekimRandevuSerializer(RandevuSerializer):
    vatandas_adi = serializers.CharField(source="vatandas.get_full_name", read_only=True)
    vatandas_tc = serializers.CharField(source="vatandas.maskeli_tc", read_only=True)

    class Meta(RandevuSerializer.Meta):
        fields = RandevuSerializer.Meta.fields + ("vatandas_adi", "vatandas_tc")
        read_only_fields = fields


class RandevuOlusturSerializer(serializers.Serializer):
    hekim = serializers.IntegerField()
    hastane = serializers.IntegerField()
    klinik = serializers.IntegerField()
    tarih = serializers.DateField()
    baslangic = serializers.TimeField()
    bekleme_talebi = serializers.IntegerField(required=False, allow_null=True)


class SlotTutSerializer(serializers.Serializer):
    """Saat seçimi: saat kısa süreliğine vatandaş adına tutulur (onay ekranı)."""
    hekim = serializers.IntegerField()
    hastane = serializers.IntegerField()
    klinik = serializers.IntegerField()
    tarih = serializers.DateField()
    baslangic = serializers.TimeField()
    degistir = serializers.IntegerField(required=False, allow_null=True,
                                        help_text="Değiştirilecek mevcut randevunun id'si (değişiklik akışı)")
    bekleme_talebi = serializers.IntegerField(required=False, allow_null=True)


class GeciciTutmaSerializer(serializers.ModelSerializer):
    hastane_adi = serializers.CharField(source="hastane.ad", read_only=True)
    klinik_adi = serializers.CharField(source="klinik.ad", read_only=True)
    hekim_adi = serializers.CharField(source="hekim.__str__", read_only=True)
    kalan_saniye = serializers.IntegerField(read_only=True)

    class Meta:
        model = GeciciTutma
        fields = ("id", "tarih", "baslangic_saati", "bitis_saati", "hastane", "hastane_adi", "klinik", "klinik_adi",
                  "hekim", "hekim_adi", "degistirilen_randevu", "son_gecerlilik", "kalan_saniye")
        read_only_fields = fields


class RandevuDegistirSerializer(serializers.Serializer):
    hekim = serializers.IntegerField()
    hastane = serializers.IntegerField()
    tarih = serializers.DateField()
    baslangic = serializers.TimeField()


class IptalSerializer(serializers.Serializer):
    neden = serializers.CharField(required=False, allow_blank=True, max_length=255)


class MuayeneDurumSerializer(serializers.Serializer):
    durum = serializers.ChoiceField(choices=[RandevuDurum.TAMAMLANDI, RandevuDurum.GELMEDI])


class BeklemeTalebiSerializer(serializers.ModelSerializer):
    durum_adi = serializers.CharField(source="get_durum_display", read_only=True)
    klinik_adi = serializers.CharField(source="klinik.ad", read_only=True)

    class Meta:
        model = BeklemeTalebi
        fields = ("id", "klinik", "klinik_adi", "il", "ilce", "hastane", "hekim", "baslangic_tarihi",
                  "bitis_tarihi", "durum", "durum_adi", "olusturma_zamani", "son_bildirim_zamani", "bildirim_sayisi")
        read_only_fields = ("durum", "olusturma_zamani", "son_bildirim_zamani", "bildirim_sayisi")


class BildirimSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bildirim
        fields = ("id", "tur", "baslik", "mesaj", "link", "randevu", "bekleme_talebi", "okundu",
                  "eposta_gonderildi", "olusturma_zamani")
        read_only_fields = fields


class KullaniciSerializer(serializers.ModelSerializer):
    rol_adi = serializers.CharField(source="get_rol_display", read_only=True)
    ad_soyad = serializers.CharField(source="get_full_name", read_only=True)
    hastane_adi = serializers.SerializerMethodField()
    maskeli_tc = serializers.CharField(read_only=True)

    class Meta:
        model = Kullanici
        fields = ("id", "username", "first_name", "last_name", "ad_soyad", "email", "telefon", "rol", "rol_adi",
                  "hastane", "hastane_adi", "maskeli_tc", "eposta_bildirim")
        read_only_fields = ("id", "username", "rol", "hastane")

    def get_hastane_adi(self, obj):
        if obj.hastane_id:
            return obj.hastane.ad
        hekim = getattr(obj, "hekim", None)
        atama = hekim.atamalar.filter(aktif=True).select_related("hastane").first() if hekim else None
        return atama.hastane.ad if atama else None


class KayitSerializer(serializers.Serializer):
    tc_kimlik_no = serializers.CharField(max_length=11, validators=[tc_kimlik_dogrula])
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    telefon = serializers.CharField(max_length=20, required=False, allow_blank=True)
    dogum_tarihi = serializers.DateField(required=False)
    password = serializers.CharField(write_only=True)

    def validate_tc_kimlik_no(self, v):
        if Kullanici.objects.filter(username=v).exists() or Kullanici.objects.filter(tc_kimlik_no=v).exists():
            raise serializers.ValidationError("Bu T.C. Kimlik No ile kayıtlı bir hesap var.")
        return v

    def validate_email(self, v):
        if Kullanici.objects.filter(email__iexact=v).exists():
            raise serializers.ValidationError("Bu e-posta adresi kullanımda.")
        return v.lower()

    def validate(self, attrs):
        validate_password(attrs["password"], Kullanici(username=attrs["tc_kimlik_no"], email=attrs["email"],
                                                         first_name=attrs["first_name"]))
        return attrs

    def create(self, vd):
        pw = vd.pop("password")
        u = Kullanici(username=vd["tc_kimlik_no"], rol=Rol.VATANDAS, **vd)
        u.set_password(pw)
        u.save()
        return u
