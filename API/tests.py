from datetime import timedelta

from rest_framework.test import APITestCase

from randevu.models import Randevu, RandevuDurum
from randevu.test_yardimci import TemelKurulum, vatandas_olustur, yonetici_olustur


class ApiRandevuAkisiTesti(TemelKurulum, APITestCase):
    def setUp(self):
        self.kur()
        self.v = vatandas_olustur()

    def test_herkese_acik_listeler(self):
        self.assertEqual(self.client.get("/api/iller/").status_code, 200)
        yanit = self.client.get(f"/api/hekimler/?klinik={self.klinik.pk}&hastane={self.hastane.pk}")
        self.assertEqual([h["id"] for h in yanit.json()], [self.hekim.pk])

    def test_slot_icin_giris_gerekir(self):
        self.assertIn(self.client.get(f"/api/slotlar/?klinik={self.klinik.pk}").status_code, (401, 403))

    def test_ara_al_onayla_iptal(self):
        self.client.force_authenticate(self.v)
        slotlar = self.client.get(f"/api/slotlar/?klinik={self.klinik.pk}").json()
        self.assertEqual(len(slotlar), 10)
        s = slotlar[0]
        yanit = self.client.post("/api/randevular/", {"hekim": s["hekim_id"], "hastane": s["hastane_id"],
                                                      "klinik": s["klinik_id"], "tarih": s["tarih"],
                                                      "baslangic": s["baslangic"]}, format="json")
        self.assertEqual(yanit.status_code, 201, yanit.content)
        rid = yanit.json()["id"]
        # Onay ekranından geçildiği için randevu doğrudan "Onaylandı" durumunda oluşu
        self.assertEqual(yanit.json()["durum"], "ONAYLANDI")
        # Aynı slotu ikinci kez almak 400 döner
        v2 = vatandas_olustur()
        self.client.force_authenticate(v2)
        tekrar = self.client.post("/api/randevular/", {"hekim": s["hekim_id"], "hastane": s["hastane_id"],
                                                       "klinik": s["klinik_id"], "tarih": s["tarih"],
                                                       "baslangic": s["baslangic"]}, format="json")
        self.assertEqual(tekrar.status_code, 400)
        self.assertIn("hata", tekrar.json())
        # Başkasının randevusu görünmez
        self.assertEqual(self.client.get(f"/api/randevular/{rid}/").status_code, 404)
        self.client.force_authenticate(self.v)
        self.assertEqual(self.client.post(f"/api/randevular/{rid}/iptal/", {"neden": "Test"}).status_code, 200)
        self.assertEqual(Randevu.objects.get(pk=rid).durum, RandevuDurum.IPTAL)

    def test_kayit_ve_token(self):
        from accounts.validators import sentetik_tc_uret

        tc = sentetik_tc_uret()
        yanit = self.client.post("/api/auth/kayit/", {"tc_kimlik_no": tc, "first_name": "Api", "last_name": "Test",
                                                      "email": "api@test.local", "password": "GucluSifre!2024"})
        self.assertEqual(yanit.status_code, 201, yanit.content)
        token = self.client.post("/api/auth/token/", {"username": tc, "password": "GucluSifre!2024"})
        self.assertIn("token", token.json())

    def test_hekim_ve_yonetici_uclari_rol_kontrolu(self):
        self.client.force_authenticate(self.v)
        self.assertEqual(self.client.get("/api/hekim/randevular/").status_code, 403)
        self.assertEqual(self.client.get("/api/yonetim/randevular/").status_code, 403)
        self.assertEqual(self.client.get("/api/yonetim/rapor/").status_code, 403)
        self.client.force_authenticate(self.hekim.kullanici)
        self.assertEqual(self.client.get("/api/hekim/randevular/").status_code, 200)
        self.client.force_authenticate(yonetici_olustur(self.hastane))
        yanit = self.client.get("/api/yonetim/rapor/", {"baslangic": (self.hedef - timedelta(days=3)).isoformat(),
                                                        "bitis": self.hedef.isoformat()})
        self.assertEqual(yanit.status_code, 200)
        self.assertIn("ozet", yanit.json())

    def test_api_dokumantasyonu(self):
        self.assertEqual(self.client.get("/api/schema/").status_code, 200)


class ApiGeciciTutmaTesti(TemelKurulum, APITestCase):
    """Mobil uygulamanın kullandığı iki adımlı akış: saat tut -> onayla / vazgeç."""

    def setUp(self):
        self.kur()
        self.v = vatandas_olustur()
        self.client.force_authenticate(self.v)

    def _tut(self, saat="09:00"):
        return self.client.post("/api/gecici-tutmalar/", {"hekim": self.hekim.pk, "hastane": self.hastane.pk,
                                                          "klinik": self.klinik.pk, "tarih": self.hedef.isoformat(),
                                                          "baslangic": saat}, format="json")

    def test_tut_ve_onayla(self):
        yanit = self._tut()
        self.assertEqual(yanit.status_code, 201, yanit.content)
        veri = yanit.json()
        self.assertGreater(veri["kalan_saniye"], 0)
        slotlar = self.client.get(f"/api/slotlar/?klinik={self.klinik.pk}").json()
        self.assertNotIn("09:00", [s["baslangic"] for s in slotlar])
        onay = self.client.post(f"/api/gecici-tutmalar/{veri['id']}/onayla/")
        self.assertEqual(onay.status_code, 201, onay.content)
        self.assertEqual(Randevu.objects.get().pk, onay.json()["id"])

    def test_vazgec(self):
        tid = self._tut().json()["id"]
        self.assertEqual(self.client.delete(f"/api/gecici-tutmalar/{tid}/").status_code, 204)
        slotlar = self.client.get(f"/api/slotlar/?klinik={self.klinik.pk}").json()
        self.assertIn("09:00", [s["baslangic"] for s in slotlar])

    def test_baskasi_ayni_saati_tutamaz(self):
        self._tut()
        self.client.force_authenticate(vatandas_olustur())
        self.assertEqual(self._tut().status_code, 400)


class MobilGirisTesti(TemelKurulum, APITestCase):
    """Mobil uygulama: token girişi, kilit, çıkış ve WebView için tek kullanımlık web kodu."""

    def setUp(self):
        self.kur()
        self.v = vatandas_olustur()

    def test_token_girisi_kullanici_bilgisi_doner(self):
        yanit = self.client.post("/api/auth/token/", {"username": self.v.username, "password": "Sifre12345!"})
        self.assertEqual(yanit.status_code, 200, yanit.content)
        self.assertEqual(yanit.json()["kullanici"]["rol"], "VATANDAS")
        self.assertIn("token", yanit.json())

    def test_hatali_denemeler_kilitler(self):
        for _ in range(5):
            self.assertEqual(self.client.post("/api/auth/token/", {"username": self.v.username,
                                                                   "password": "yanlis"}).status_code, 400)
        yanit = self.client.post("/api/auth/token/", {"username": self.v.username, "password": "Sifre12345!"})
        self.assertEqual(yanit.status_code, 429)

    def test_cikis_tokeni_siler(self):
        token = self.client.post("/api/auth/token/", {"username": self.v.username,
                                                      "password": "Sifre12345!"}).json()["token"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token}")
        self.assertEqual(self.client.post("/api/auth/cikis/").status_code, 204)
        self.assertIn(self.client.get("/api/auth/ben/").status_code, (401, 403))

    def test_web_kodu_tek_kullanimlik(self):
        self.client.force_authenticate(self.v)
        kod = self.client.post("/api/auth/web-kodu/").json()["kod"]
        self.client.force_authenticate(None)
        yanit = self.client.get("/mobil-giris/", {"kod": kod, "sonra": "/randevularim/"})
        self.assertRedirects(yanit, "/randevularim/", fetch_redirect_response=False)
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.v.pk)
        # İkinci kullanım ve bozuk kod reddedilir
        self.client.logout()
        self.assertRedirects(self.client.get("/mobil-giris/", {"kod": kod}), "/giris/", fetch_redirect_response=False)
        self.assertRedirects(self.client.get("/mobil-giris/", {"kod": kod + "x"}), "/giris/",
                             fetch_redirect_response=False)

    def test_web_kodu_dis_siteye_yonlendirmez(self):
        self.client.force_authenticate(self.v)
        kod = self.client.post("/api/auth/web-kodu/").json()["kod"]
        self.client.force_authenticate(None)
        yanit = self.client.get("/mobil-giris/", {"kod": kod, "sonra": "https://kotu.example.com/"})
        self.assertRedirects(yanit, "/", fetch_redirect_response=False)

    def test_web_cerezi_varken_token_ile_islem_csrf_istemez(self):
        """Uygulama içi web paneli açıldıktan sonra cihazda oturum çerezi kalsa da token ile randevu alınabilir."""
        from rest_framework.test import APIClient

        istemci = APIClient(enforce_csrf_checks=True)
        istemci.login(username=self.v.username, password="Sifre12345!")  # web oturum çerezi
        token = istemci.post("/api/auth/token/", {"username": self.v.username,
                                                  "password": "Sifre12345!"}).json()["token"]
        istemci.credentials(HTTP_AUTHORIZATION=f"Token {token}")
        s = istemci.get(f"/api/slotlar/?klinik={self.klinik.pk}").json()[0]
        yanit = istemci.post("/api/randevular/", {"hekim": s["hekim_id"], "hastane": s["hastane_id"],
                                                  "klinik": s["klinik_id"], "tarih": s["tarih"],
                                                  "baslangic": s["baslangic"]}, format="json")
        self.assertEqual(yanit.status_code, 201, yanit.content)
