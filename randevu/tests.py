from datetime import datetime, time, timedelta
from unittest import mock

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from accounts.models import DenetimKaydi
from accounts.validators import sentetik_tc_uret, tc_kimlik_gecerli_mi
from merkez.models import Izin, KapaliZaman, MerkeziKural

from . import services
from .models import BeklemeDurum, BildirimTur, GeciciTutma, Randevu, RandevuDurum
from .services import RandevuHatasi
from .slotlar import Slot, bos_slotlari_bul
from .test_yardimci import TemelKurulum, hekim_olustur, vatandas_olustur


class TcKimlikTesti(TestCase):
    def test_sentetik_numaralar_gecerli(self):
        for _ in range(50):
            self.assertTrue(tc_kimlik_gecerli_mi(sentetik_tc_uret()))

    def test_gecersiz_numaralar(self):
        for tc in ["", "123", "01234567890", "12345678901", "1234567890a"]:
            self.assertFalse(tc_kimlik_gecerli_mi(tc))


class SlotHesaplamaTesti(TemelKurulum, TestCase):
    def setUp(self):
        self.kur()

    def test_mola_ve_muayene_suresi(self):
        slotlar = bos_slotlari_bul(klinik=self.klinik)
        saatler = [s.baslangic for s in slotlar]
        # 09:00-10:00 (4 slot) + 10:30-12:00 (6 slot)
        self.assertEqual(len(saatler), 10)
        self.assertNotIn(time(10, 0), saatler)
        self.assertNotIn(time(10, 15), saatler)
        self.assertIn(time(10, 30), saatler)
        self.assertTrue(all(s.tarih == self.hedef for s in slotlar))

    def test_gunluk_kapasite(self):
        self.plan.gunluk_kapasite = 3
        self.plan.save()
        self.assertEqual(len(bos_slotlari_bul(klinik=self.klinik)), 3)

    def test_dolu_slot_listelenmez(self):
        v = vatandas_olustur()
        services.randevu_olustur(v, *self.slot_args(time(9, 0)))
        saatler = [s.baslangic for s in bos_slotlari_bul(klinik=self.klinik)]
        self.assertNotIn(time(9, 0), saatler)
        self.assertEqual(len(saatler), 9)

    def test_hekim_secmeden_tum_hekimler(self):
        diger = hekim_olustur(self.hastane, self.klinik)
        self.plan.pk = None
        self.plan.hekim = diger
        self.plan.save()
        hekimler = {s.hekim_id for s in bos_slotlari_bul(klinik=self.klinik)}
        self.assertEqual(hekimler, {self.hekim.pk, diger.pk})

    def test_izin_ve_kapali_saat_slotlari_kapatir(self):
        Izin.objects.create(hekim=self.hekim, baslangic_tarihi=self.hedef, bitis_tarihi=self.hedef,
                            baslangic_saati=time(9, 0), bitis_saati=time(10, 0))
        KapaliZaman.objects.create(ad="Bakım", tarih=self.hedef, hastane=self.hastane,
                                   baslangic_saati=time(11, 0), bitis_saati=time(12, 0))
        saatler = [s.baslangic for s in bos_slotlari_bul(klinik=self.klinik)]
        self.assertEqual(saatler, [time(10, 30), time(10, 45)])

    def test_ileri_tarih_limiti(self):
        kural = MerkeziKural.al()
        kural.ileri_tarih_gun_limiti = 1
        kural.save()
        self.assertEqual(bos_slotlari_bul(klinik=self.klinik), [])

    def test_pasif_atama_slot_uretmez(self):
        self.hekim.atamalar.update(aktif=False)
        self.assertEqual(bos_slotlari_bul(klinik=self.klinik), [])


class RandevuOlusturmaTesti(TemelKurulum, TestCase):
    def setUp(self):
        self.kur()
        self.v1 = vatandas_olustur("Bir")
        self.v2 = vatandas_olustur("İki")

    def test_basarili_randevu_bildirim_ve_denetim(self):
        r = services.randevu_olustur(self.v1, *self.slot_args())
        self.assertEqual(r.durum, RandevuDurum.ONAYLANDI)
        self.assertIsNotNone(r.onay_zamani)
        self.assertEqual(r.bitis_saati, time(9, 15))
        self.assertTrue(self.v1.bildirimler.filter(tur=BildirimTur.RANDEVU_OLUSTURULDU).exists())
        self.assertTrue(DenetimKaydi.objects.filter(islem="RANDEVU_OLUSTURULDU", nesne_id=str(r.pk)).exists())

    def test_ayni_slot_ikinci_kisiye_verilmez(self):
        services.randevu_olustur(self.v1, *self.slot_args())
        with self.assertRaisesMessage(RandevuHatasi, "dolu"):
            services.randevu_olustur(self.v2, *self.slot_args())

    def test_veritabani_kisiti_cift_rezervasyonu_engeller(self):
        ortak = dict(hekim=self.hekim, hastane=self.hastane, klinik=self.klinik, tarih=self.hedef,
                     baslangic_saati=time(9, 0), bitis_saati=time(9, 15))
        Randevu.objects.create(vatandas=self.v1, **ortak)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Randevu.objects.create(vatandas=self.v2, **ortak)

    def test_iptal_edilen_slot_tekrar_alinabilir(self):
        ortak = dict(hekim=self.hekim, hastane=self.hastane, klinik=self.klinik, tarih=self.hedef,
                     baslangic_saati=time(9, 0), bitis_saati=time(9, 15))
        Randevu.objects.create(vatandas=self.v1, durum=RandevuDurum.IPTAL, **ortak)
        Randevu.objects.create(vatandas=self.v2, **ortak)  # kısıt yalnızca iptal edilmemişler için

    def test_es_zamanli_yaris_durumu(self):
        """Kontrol anında boş görünen slot, kayıttan hemen önce başkası tarafından alınırsa
        veritabanı kısıtı devreye girer ve kullanıcıya anlaşılır hata döner."""
        bos = Slot(self.hekim.pk, "", self.hastane.pk, "", self.klinik.pk, "", self.hedef, time(9, 0),
                   time(9, 15), dolu=False)
        Randevu.objects.create(vatandas=self.v2, hekim=self.hekim, hastane=self.hastane, klinik=self.klinik,
                               tarih=self.hedef, baslangic_saati=time(9, 0), bitis_saati=time(9, 15))
        with mock.patch("randevu.services.slot_dogrula", return_value=bos):
            with self.assertRaisesMessage(RandevuHatasi, "az önce"):
                services.randevu_olustur(self.v1, *self.slot_args())
        self.assertEqual(Randevu.objects.filter(tarih=self.hedef).count(), 1)

    def test_plan_disi_saat_reddedilir(self):
        with self.assertRaises(RandevuHatasi):
            services.randevu_olustur(self.v1, *self.slot_args(time(9, 7)))
        with self.assertRaises(RandevuHatasi):
            services.randevu_olustur(self.v1, *self.slot_args(time(10, 0)))  # mola

    def test_ayni_klinik_aktif_randevu_limiti(self):
        services.randevu_olustur(self.v1, *self.slot_args(time(9, 0)))
        with self.assertRaisesMessage(RandevuHatasi, "aktif bir randevunuz"):
            services.randevu_olustur(self.v1, *self.slot_args(time(9, 15)))

    def test_gelmeme_cezasi(self):
        Randevu.objects.create(vatandas=self.v1, hekim=self.hekim, hastane=self.hastane, klinik=self.klinik,
                               tarih=self.hedef - timedelta(days=5), baslangic_saati=time(9, 0),
                               bitis_saati=time(9, 15), durum=RandevuDurum.GELMEDI)
        with self.assertRaisesMessage(RandevuHatasi, "gitmediğiniz"):
            services.randevu_olustur(self.v1, *self.slot_args())

    def test_ayrica_katilim_teyidi_istenmez(self):
        r = services.randevu_olustur(self.v1, *self.slot_args())
        self.assertNotIn("teyit", r.vatandas.bildirimler.get(tur=BildirimTur.RANDEVU_OLUSTURULDU).mesaj)


class IptalVeDegisiklikTesti(TemelKurulum, TestCase):
    def setUp(self):
        self.kur()
        self.v1 = vatandas_olustur()
        self.v2 = vatandas_olustur()

    def test_iptal_kontenjani_acar(self):
        r = services.randevu_olustur(self.v1, *self.slot_args())
        services.randevu_iptal(r, self.v1)
        r.refresh_from_db()
        self.assertEqual(r.durum, RandevuDurum.IPTAL)
        self.assertIn(time(9, 0), [s.baslangic for s in bos_slotlari_bul(klinik=self.klinik)])
        services.randevu_olustur(self.v2, *self.slot_args())  # aynı slot yeniden alınabilir

    def test_iptal_son_saat_kurali(self):
        r = services.randevu_olustur(self.v1, *self.slot_args())
        az_once = datetime.combine(self.hedef, time(8, 0))  # randevuya 1 saat kala
        with mock.patch("randevu.services.simdi_yerel", return_value=az_once):
            with self.assertRaisesMessage(RandevuHatasi, "saatten az"):
                services.randevu_iptal(r, self.v1)

    def test_baskasinin_randevusu_iptal_edilemez(self):
        r = services.randevu_olustur(self.v1, *self.slot_args())
        with self.assertRaises(RandevuHatasi):
            services.randevu_iptal(r, self.v2)

    def test_degisiklik_basarili(self):
        r = services.randevu_olustur(self.v1, *self.slot_args(time(9, 0)))
        yeni = services.randevu_degistir(r, self.v1, self.hekim.pk, self.hastane.pk, self.klinik.pk, self.hedef,
                                         time(11, 0))
        r.refresh_from_db()
        self.assertEqual(r.durum, RandevuDurum.IPTAL)
        self.assertEqual(yeni.onceki_randevu_id, r.pk)
        self.assertEqual(yeni.baslangic_saati, time(11, 0))

    def test_degisiklik_basarisizsa_eski_randevu_korunur(self):
        r = services.randevu_olustur(self.v1, *self.slot_args(time(9, 0)))
        services.randevu_olustur(self.v2, *self.slot_args(time(11, 0)))
        with self.assertRaises(RandevuHatasi):
            services.randevu_degistir(r, self.v1, self.hekim.pk, self.hastane.pk, self.klinik.pk, self.hedef,
                                      time(11, 0))
        r.refresh_from_db()
        self.assertEqual(r.durum, RandevuDurum.ONAYLANDI)


class BeklemeListesiTesti(TemelKurulum, TestCase):
    """Senaryo 2 ve 4: boş slot yokken talep, iptalde eşleştirme ve bildirim."""

    def setUp(self):
        self.kur(kapasite=1)
        self.v1 = vatandas_olustur()
        self.v2 = vatandas_olustur()
        self.r = services.randevu_olustur(self.v1, *self.slot_args())

    def test_bos_slot_varken_talep_acilamaz(self):
        self.r.durum = RandevuDurum.IPTAL
        self.r.save()
        with self.assertRaisesMessage(RandevuHatasi, "boş randevu"):
            services.bekleme_talebi_olustur(self.v2, self.klinik, self.hedef, self.hedef)

    def test_iptal_sonrasi_bildirim_ve_vatandas_onayi(self):
        talep = services.bekleme_talebi_olustur(self.v2, self.klinik, self.hedef - timedelta(days=1),
                                                self.hedef + timedelta(days=2))
        self.assertEqual(talep.durum, BeklemeDurum.AKTIF)

        services.randevu_iptal(self.r, self.v1)
        talep.refresh_from_db()
        self.assertEqual(talep.durum, BeklemeDurum.BILDIRILDI)
        self.assertTrue(self.v2.bildirimler.filter(tur=BildirimTur.BEKLEME_UYGUN).exists())
        # Bildirim otomatik randevu oluşturmaz
        self.assertFalse(Randevu.objects.filter(vatandas=self.v2).exists())

        r2 = services.randevu_olustur(self.v2, *self.slot_args(), bekleme_talebi=talep)
        talep.refresh_from_db()
        self.assertEqual(talep.durum, BeklemeDurum.KARSILANDI)
        self.assertEqual(r2.bekleme_talebi_id, talep.pk)

    def test_tercih_edilen_baska_hekim_ise_bildirim_gitmez(self):
        diger = hekim_olustur(self.hastane, self.klinik)
        services.bekleme_talebi_olustur(self.v2, self.klinik, self.hedef, self.hedef, hekim=diger)
        services.randevu_iptal(self.r, self.v1)
        self.assertFalse(self.v2.bildirimler.filter(tur=BildirimTur.BEKLEME_UYGUN).exists())

    def test_fifo_ve_kisi_siniri(self):
        kural = MerkeziKural.al()
        kural.bekleme_bildirim_kisi_sayisi = 1
        kural.save()
        t2 = services.bekleme_talebi_olustur(self.v2, self.klinik, self.hedef, self.hedef)
        v3 = vatandas_olustur()
        t3 = services.bekleme_talebi_olustur(v3, self.klinik, self.hedef, self.hedef)
        services.randevu_iptal(self.r, self.v1)
        t2.refresh_from_db()
        t3.refresh_from_db()
        self.assertEqual(t2.durum, BeklemeDurum.BILDIRILDI)
        self.assertEqual(t3.durum, BeklemeDurum.AKTIF)

    def test_yeni_plan_eklenince_tarama(self):
        talep = services.bekleme_talebi_olustur(self.v2, self.klinik, self.hedef, self.hedef)
        yeni = self.plan
        yeni.pk = None
        yeni.baslangic_saati, yeni.bitis_saati = time(14, 0), time(15, 0)
        yeni.mola_baslangic = yeni.mola_bitis = None
        yeni.gunluk_kapasite = None
        services.plan_kaydet(yeni, None)
        talep.refresh_from_db()
        self.assertEqual(talep.durum, BeklemeDurum.BILDIRILDI)


class TakvimDegisikligiTesti(TemelKurulum, TestCase):
    """Senaryo 3: hekim izni ve çalışma planı değişikliği."""

    def setUp(self):
        self.kur()
        self.v1 = vatandas_olustur()
        self.r = services.randevu_olustur(self.v1, *self.slot_args(time(11, 0)))

    def test_izin_yeni_randevuyu_engeller_mevcuda_bildirim_gonderir(self):
        izin = Izin(hekim=self.hekim, baslangic_tarihi=self.hedef, bitis_tarihi=self.hedef)
        cakisan = services.izin_kaydet(izin, None)
        self.assertEqual([r.pk for r in cakisan], [self.r.pk])
        self.assertTrue(self.v1.bildirimler.filter(tur=BildirimTur.YENIDEN_PLANLAMA).exists())
        self.assertEqual(bos_slotlari_bul(klinik=self.klinik), [])
        with self.assertRaises(RandevuHatasi):
            services.randevu_olustur(vatandas_olustur(), *self.slot_args(time(9, 0)))

    def test_plan_degisikligi_cakisma_uyarisi(self):
        self.plan.bitis_saati = time(10, 0)
        self.plan.mola_baslangic = self.plan.mola_bitis = None
        cakisan = services.plan_degisikligi_cakismalari(self.plan)
        self.assertEqual([r.pk for r in cakisan], [self.r.pk])

    def test_cakismayan_plan_degisikligi(self):
        self.plan.bitis_saati = time(13, 0)
        self.assertEqual(services.plan_degisikligi_cakismalari(self.plan), [])


class MuayeneDurumuTesti(TemelKurulum, TestCase):
    """Senaryo 5: hekim tamamlandı / gelmedi işler."""

    def setUp(self):
        self.kur()
        self.v1 = vatandas_olustur()
        self.r = Randevu.objects.create(vatandas=self.v1, hekim=self.hekim, hastane=self.hastane,
                                        klinik=self.klinik, tarih=self.hedef - timedelta(days=3),
                                        baslangic_saati=time(9, 0), bitis_saati=time(9, 15))

    def test_tamamlandi_ve_gelmedi(self):
        services.muayene_durumu_isle(self.r, self.hekim.kullanici, RandevuDurum.TAMAMLANDI)
        self.r.refresh_from_db()
        self.assertEqual(self.r.durum, RandevuDurum.TAMAMLANDI)
        services.muayene_durumu_isle(self.r, self.hekim.kullanici, RandevuDurum.GELMEDI)
        self.assertTrue(self.v1.bildirimler.filter(tur=BildirimTur.MUAYENE_DURUMU).exists())

    def test_gelecek_tarih_islenemez(self):
        gelecek = services.randevu_olustur(vatandas_olustur(), *self.slot_args())
        with self.assertRaises(RandevuHatasi):
            services.muayene_durumu_isle(gelecek, self.hekim.kullanici, RandevuDurum.TAMAMLANDI)

    def test_baska_hekim_isleyemez(self):
        diger = hekim_olustur(self.hastane, self.klinik)
        with self.assertRaises(RandevuHatasi):
            services.muayene_durumu_isle(self.r, diger.kullanici, RandevuDurum.TAMAMLANDI)


class HatirlatmaTesti(TemelKurulum, TestCase):
    def test_yaklasan_randevuya_hatirlatma(self):
        self.kur()
        v = vatandas_olustur()
        r = services.randevu_olustur(v, *self.slot_args())
        simdi = datetime.combine(self.hedef - timedelta(days=1), time(10, 0))
        with mock.patch("randevu.services.simdi_yerel", return_value=simdi):
            self.assertEqual(services.hatirlatmalari_gonder(), 1)
            self.assertEqual(services.hatirlatmalari_gonder(), 0)  # ikinci kez gönderilmez
        r.refresh_from_db()
        self.assertTrue(r.hatirlatma_gonderildi)


class GeciciTutmaTesti(TemelKurulum, TestCase):
    """Saat seçilince onay için kısa süreli ayrılması; süre dolunca otomatik serbest kalması."""

    def setUp(self):
        self.kur()
        self.v1 = vatandas_olustur("Bir")
        self.v2 = vatandas_olustur("İki")

    def bos_saatler(self):
        return [s.baslangic for s in bos_slotlari_bul(klinik=self.klinik, hastane=self.hastane)
                if s.tarih == self.hedef]

    def suresini_bitir(self, tutma):
        GeciciTutma.objects.filter(pk=tutma.pk).update(son_gecerlilik=timezone.now() - timedelta(seconds=1))

    def test_tutulan_saat_baskasina_dolu_gorunur(self):
        services.slot_tut(self.v1, *self.slot_args())
        self.assertNotIn(time(9, 0), self.bos_saatler())
        with self.assertRaisesMessage(RandevuHatasi, "onaylanıyor"):
            services.slot_tut(self.v2, *self.slot_args())
        with self.assertRaisesMessage(RandevuHatasi, "onaylanıyor"):
            services.randevu_olustur(self.v2, *self.slot_args())

    def test_onaylaninca_randevu_olusur_ve_tutma_silinir(self):
        tutma = services.slot_tut(self.v1, *self.slot_args())
        self.assertFalse(Randevu.objects.exists())
        r = services.tutmayi_onayla(tutma.pk, self.v1)
        self.assertEqual(r.durum, RandevuDurum.ONAYLANDI)
        self.assertEqual((r.vatandas_id, r.baslangic_saati), (self.v1.pk, time(9, 0)))
        self.assertFalse(GeciciTutma.objects.exists())

    def test_suresi_dolan_tutma_saati_serbest_birakir(self):
        tutma = services.slot_tut(self.v1, *self.slot_args())
        self.suresini_bitir(tutma)
        self.assertIn(time(9, 0), self.bos_saatler())
        with self.assertRaisesMessage(RandevuHatasi, "süresi doldu"):
            services.tutmayi_onayla(tutma.pk, self.v1)
        self.assertFalse(Randevu.objects.exists())
        # Başka bir vatandaş artık aynı saati seçebilir
        services.slot_tut(self.v2, *self.slot_args())
        self.assertEqual(GeciciTutma.objects.get().vatandas_id, self.v2.pk)

    def test_bir_kisi_ayni_anda_tek_saat_tutar(self):
        services.slot_tut(self.v1, *self.slot_args(time(9, 0)))
        services.slot_tut(self.v1, *self.slot_args(time(9, 15)))
        self.assertEqual(GeciciTutma.objects.filter(vatandas=self.v1).count(), 1)
        self.assertIn(time(9, 0), self.bos_saatler())
        self.assertNotIn(time(9, 15), self.bos_saatler())

    def test_vazgecince_saat_hemen_acilir(self):
        tutma = services.slot_tut(self.v1, *self.slot_args())
        services.tutma_birak(tutma.pk, self.v1)
        self.assertIn(time(9, 0), self.bos_saatler())

    def test_baskasinin_tutmasi_onaylanamaz_ve_birakilamaz(self):
        tutma = services.slot_tut(self.v1, *self.slot_args())
        with self.assertRaises(RandevuHatasi):
            services.tutmayi_onayla(tutma.pk, self.v2)
        services.tutma_birak(tutma.pk, self.v2)
        self.assertTrue(GeciciTutma.objects.filter(pk=tutma.pk).exists())

    def test_kural_ihlali_saat_seciminde_bildirilir(self):
        services.randevu_olustur(self.v1, *self.slot_args(time(9, 0)))
        with self.assertRaisesMessage(RandevuHatasi, "zaten aktif"):
            services.slot_tut(self.v1, *self.slot_args(time(11, 0)))
        self.assertFalse(GeciciTutma.objects.exists())

    def test_sure_merkezi_kuraldan_gelir(self):
        kural = MerkeziKural.al()
        kural.gecici_tutma_dakika = 10
        kural.save()
        tutma = services.slot_tut(self.v1, *self.slot_args())
        self.assertTrue(590 <= tutma.kalan_saniye <= 600)

    def test_degisiklik_tutma_ile_onaylanir(self):
        r = services.randevu_olustur(self.v1, *self.slot_args(time(9, 0)))
        tutma = services.slot_tut(self.v1, *self.slot_args(time(11, 0)), degistirilen=r)
        yeni = services.tutmayi_onayla(tutma.pk, self.v1)
        r.refresh_from_db()
        self.assertEqual(r.durum, RandevuDurum.IPTAL)
        self.assertEqual((yeni.onceki_randevu_id, yeni.baslangic_saati), (r.pk, time(11, 0)))

    def test_raporlarda_tutmalar_dolu_sayilmaz(self):
        from .slotlar import plan_sorgusu, slot_uret
        services.slot_tut(self.v1, *self.slot_args())
        slotlar = slot_uret(plan_sorgusu(hekim=self.hekim), self.hedef, self.hedef, dolu_dahil=True,
                            tutmalar_dahil=False)
        self.assertFalse(any(s.dolu for s in slotlar))
