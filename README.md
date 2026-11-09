# 🏥 MHRS Benzeri Merkezi Hastane ve Hekim Randevu Yönetim Sistemi

## Proje Hakkında

Bu proje, Türkiye'de kullanılan Merkezi Hekim Randevu Sistemi (MHRS) örnek alınarak geliştirilen, vatandaşların hastane, klinik ve hekim seçerek çevrim içi randevu oluşturmasını sağlayan merkezi bir hastane ve hekim randevu yönetim sistemidir.

Sistem; vatandaşların randevu işlemlerini gerçekleştirmesini, hekimlerin çalışma takvimlerini ve randevularını yönetmesini, hastane yöneticilerinin hastane operasyonlarını düzenlemesini ve sistem yöneticilerinin merkezi yönetim işlemlerini gerçekleştirmesini amaçlamaktadır.

Proje kapsamında kullanıcı yönetimi, randevu planlama, dinamik kontenjan yönetimi, bekleme listesi, bildirim ve raporlama gibi temel işlevler ele alınmaktadır.

##  Projenin Amacı

- Vatandaşların çevrim içi randevu oluşturabilmesini sağlamak.
- Hastane, klinik ve hekim bilgilerinin merkezi olarak yönetilmesini sağlamak.
- Hekimlerin çalışma takvimlerini ve randevu kontenjanlarını düzenlemek.
- Aynı randevu saatine birden fazla kişinin rezervasyon yapmasını önlemek.
- Boş randevu bulunmadığında bekleme listesi oluşturulmasını sağlamak.
- Kullanıcı rollerine göre yetkilendirme gerçekleştirmek.

##  Temel Özellikler

- Kullanıcı kayıt ve giriş sistemi
- Rol bazlı yetkilendirme
- İl, ilçe ve hastane yönetimi
- Klinik ve hekim yönetimi
- Hekim çalışma takvimi yönetimi
- Dinamik randevu slotu ve kontenjan oluşturma
- Randevu arama, oluşturma, değiştirme ve iptal etme
- Geçmiş randevuları görüntüleme
- Bekleme listesi ve uygunluk bildirimi
- Hekim paneli
- Hastane yönetim paneli
- Merkezi sistem yönetimi
- Randevu raporlama ve analiz

##  Kullanıcı Rolleri

| Kullanıcı Rolü     | Yetkileri                                                                     |
| ------------------ | ----------------------------------------------------------------------------- |
| Vatandaş           | Randevu arama, oluşturma, değiştirme, iptal etme ve bekleme listesi oluşturma |
| Hekim              | Çalışma takvimini ve randevularını görüntüleme, muayene durumunu güncelleme   |
| Hastane Yöneticisi | Klinik, hekim, çalışma takvimi ve kontenjan yönetimi                          |
| Sistem Yöneticisi  | İl, ilçe, hastane, kullanıcı ve merkezi sistem yönetimi                       |

##  Kullanılan Teknolojiler

- **Frontend:** 
- **Backend:** Python – FastAPI
- **Veritabanı:** Microsoft SQL Server (MSSQL)
- **Veritabanı Yönetimi:** SQL Server Management Studio (SSMS)
- **API:**  fastAPI
- **Tasarım:** UML ve sistem mimarisi diyagramları
  
##  Sistem Mimarisi

Proje, katmanlı mimari yaklaşımı temel alınarak tasarlanmıştır.

Mimari yapı aşağıdaki katmanlardan oluşmaktadır:

1. Sunum Katmanı
2. REST API / İletişim Katmanı
3. İş Mantığı Katmanı
4. Veri Erişim Katmanı
5. Veritabanı Katmanı

Bu yapı sayesinde kullanıcı arayüzü, iş kuralları ve veri erişim süreçleri birbirinden ayrılarak daha düzenli ve sürdürülebilir bir yazılım mimarisi hedeflenmektedir.

##  Yazılım Tasarımı ve UML

Proje kapsamında aşağıdaki tasarım çalışmaları hazırlanmıştır:

- UML Use Case Diyagramı
- UML Class Diyagramı
- UML Sequence Diyagramları
  - Randevu Alma
  - Randevu İptal
  - Bekleme Listesi
- Sistem Mimarisi / Component Diyagramı
- ER Diyagramı
- Architecture Decision Record (ADR)
- Kontenjan ve Eş Zamanlı Rezervasyon Algoritması

##  Güvenlik ve Veri Yönetimi

- Kullanıcıların rollerine göre erişim kontrolü sağlanması hedeflenmektedir.
- Hastane yöneticilerinin yalnızca yetkili oldukları hastanenin verilerine erişmesi amaçlanmaktadır.
- Eş zamanlı rezervasyon işlemlerinde kontenjan aşımının önlenmesi hedeflenmektedir.
- Kullanıcı işlemlerinin denetim kayıtlarıyla takip edilmesi planlanmaktadır.

##  Proje Kapsamı ve Sınırlar

Bu proje bağımsız bir test ortamında geliştirilmektedir.

Gerçek MHRS, e-Nabız veya e-Devlet sistemleriyle entegrasyon yapılmamaktadır. Gerçek hasta verileri kullanılmamakta; teşhis, reçete ve hasta dosyası yönetimi proje kapsamı dışında tutulmaktadır.

##  Kurulum ve Çalıştırma

