from datetime import time, timedelta

from accounts.models import Kullanici, Rol
from accounts.validators import sentetik_tc_uret
from merkez.models import CalismaPlani, Hastane, HastaneKlinik, Hekim, HekimAtama, Il, Ilce, Klinik, MerkeziKural
from randevu.slotlar import simdi_yerel

_sayac = {"n": 0}


def _yeni_ad(onek):
    _sayac["n"] += 1
    return f"{onek}{_sayac['n']}"


def vatandas_olustur(ad="Test"):
    tc = sentetik_tc_uret()
    while Kullanici.objects.filter(username=tc).exists():
        tc = sentetik_tc_uret()
    u = Kullanici(username=tc, tc_kimlik_no=tc, first_name=ad, last_name="Vatandaş", rol=Rol.VATANDAS,
                  email=f"{tc}@test.local")
    u.set_password("Sifre12345!")
    u.save()
    return u


def hekim_olustur(hastane, klinik):
    u = Kullanici(username=_yeni_ad("hekim"), first_name="Ali", last_name="Hekim", rol=Rol.HEKIM)
    u.set_password("Sifre12345!")
    u.save()
    h = Hekim.objects.create(kullanici=u, uzmanlik=klinik)
    HekimAtama.objects.create(hekim=h, hastane=hastane, klinik=klinik)
    return h


def yonetici_olustur(hastane):
    u = Kullanici(username=_yeni_ad("yonetici"), rol=Rol.HASTANE_YONETICISI, hastane=hastane)
    u.set_password("Sifre12345!")
    u.save()
    return u


class TemelKurulum:
    """setUp'ta il/ilçe/hastane/klinik/hekim ve hedef tarihte tek günlük bir plan kurar."""

    def kur(self, kapasite=None, sure=15, bas=time(9, 0), bit=time(12, 0), mola=(time(10, 0), time(10, 30))):
        MerkeziKural.al()
        self.il = Il.objects.create(ad=_yeni_ad("İl"), plaka_kodu=_sayac["n"] + 100)
        self.ilce = Ilce.objects.create(il=self.il, ad="Merkez")
        self.hastane = Hastane.objects.create(ad=_yeni_ad("Test Hastanesi "), ilce=self.ilce)
        self.klinik = Klinik.objects.create(ad=_yeni_ad("Dermatoloji "))
        HastaneKlinik.objects.create(hastane=self.hastane, klinik=self.klinik)
        self.hekim = hekim_olustur(self.hastane, self.klinik)
        self.hedef = simdi_yerel().date() + timedelta(days=3)
        self.plan = CalismaPlani.objects.create(
            hekim=self.hekim, hastane=self.hastane, klinik=self.klinik, gun=self.hedef.weekday(),
            baslangic_saati=bas, bitis_saati=bit,
            mola_baslangic=mola[0] if mola else None, mola_bitis=mola[1] if mola else None,
            muayene_suresi=sure, gunluk_kapasite=kapasite,
            gecerlilik_baslangic=self.hedef, gecerlilik_bitis=self.hedef,
        )
        return self

    def slot_args(self, saat=time(9, 0)):
        return (self.hekim.pk, self.hastane.pk, self.klinik.pk, self.hedef, saat)
