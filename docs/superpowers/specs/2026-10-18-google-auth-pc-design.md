# Tasarım: Google Auth PC — Windows Masaüstü Kod (TOTP) Uygulaması

- Tarih: 2026-10-18
- Durum: Onaylandı (mockup'larla doğrulandı; kullanıcı "kodlamaya başla" dedi)
- Mockup'lar: `Google-Auth-PC/.superpowers/brainstorm/275-1792342981/content/` (layout.html, lock-import.html, portrait.html, themes.html)
- Proje klasörü: `C:\Users\batuh\Desktop\Google-Auth-PC`
- Depo: https://github.com/batuhansavas-yilmaz/Google-Auth-PC

## Amaç ve neden

Kullanıcı iki adımlı doğrulama kodlarına (TOTP, 6 haneli) ihtiyaç duyduğunda telefon bazen elinin altında olmuyor (kapalı, şarjda vb.). Kod girişleri ise bilgisayarda yapılıyor. Hedef: Windows'ta her zaman hazır, hafif, telefon uygulaması kadar tanıdık bir kod üreticisi — Google Authenticator'ın masaüstü karşılığı.

## Başarı tanımı

- Telefona uzanmadan PC'de birkaç saniyede kod alınır (tepsi → aç → doğrula → kopyala).
- Boşta RAM hedefi ~40-60 MB; Windows açılışında kendiliğinden başlar, sistem tepsisinde sessizce durur.
- Google Authenticator'daki tüm hesaplar tek hamlede PC'ye aktarılabilir.
- Telefondaki mevcut kurulum bozulmaz (hiçbir hesap telefondan silinmez).

## Hedefler (kapsam)

1. Windows masaüstü uygulaması; tamamen çevrimdışı çalışır (TOTP için ağ gerekmez; uygulama hiç ağ erişimi yapmaz).
2. Ana ekran (B düzeni, dikey pencere): üst barda "Hesap ara…" alanı ve "+ Ekle" düğmesi; altında kart listesi. Kart: avatar (servis baş harfi), hesap adı + servis adı, 6 haneli kod ("836 421" 3+3, eş aralıklı, mono), geri sayım halkası (içinde kalan saniye), "Kopyala" düğmesi. Koda veya Kopyala'ya tıklayınca kod panoya kopyalanır ve "Kopyalandı" geri bildirimi gösterilir.
3. Pencere: açılışta ~400×820 px (ekran yüksekliğinin en fazla %85'i), dikey/telefon oranı; yeniden boyutlandırılabilir; boyut ve konum hatırlanır.
4. Tema: Windows açık/koyu modunu otomatik izler; Ayarlar'dan "Otomatik / Açık / Koyu" seçilebilir. Tüm ekranlar (ana, kilit, içe aktarma, ayarlar) temayı izler.
5. Kilit: program açılınca kodlar kilitli gelir ("Kodlar kilitli"). "Windows ile doğrula" Chrome'un parola ekranı benzeri bir Windows doğrulaması açar (Windows Hello: PIN / parmak izi / yüz). Windows Hello kullanılamıyorsa bir kez belirlenen 6 haneli uygulama PIN'i (dokunmatik tuş takımı) devreye girer. Pencere kapanınca yeniden kilitlenir.
6. Toplu içe aktarma ("Tek hamlede"): Google Authenticator → "Hesapları aktar → Dışa aktar" QR'larının ekran görüntüleri PC'ye aktarılır; uygulama görselleri okur (çoklu seçim; mümkünse sürükle-bırak), otpauth-migration (protobuf) yükünü çözer ve tüm hesapları tek seferde ekler. Tekrar aktarımda mükerrer oluşmaz. Sonuç özeti gösterilir ("N hesap bulundu — N eklendi (zaten ekli olanlar atlandı)").
7. Tek tek ekleme: "Tek tek ekle" sekmesi; kurulum anahtarı (secret) yapıştırma + isim/servis alanları.
8. Hesap yönetimi: hesap ekleme, adını/servisini düzenleme, silme; arama tüm listeyi filtreler.
9. Sistem tepsisi: sol tık pencereyi (kilitli) açar; sağ tık menüsü: Aç / Kilitle / Ayarlar / Çıkış. X ile kapatmak pencereyi gizler (uygulama tepsiden çıkmaz).
10. Windows açılışında otomatik başlama (varsayılan açık; Ayarlar'dan kapatılabilir).
11. İlk açılışta kısa "telefondan nasıl aktarırım" yönlendirmesi (4 adım).
12. Basit Ayarlar ekranı: tema (Otomatik/Açık/Koyu), açılışta başlama aç/kapa, PIN belirle/değiştir, içe aktarma kısayolu, sürüm bilgisi.

## Kapsam dışı / anti-hedefler

- Otomatik canlı senkron yok (Google üçüncü partiye API vermiyor). Aktarım manueldir ve istenildiğinde tekrarlanır (~1 dk).
- Microsoft hesapları ve bildirimli onaylar yok (kullanıcı kapsamdan çıkardı; üçüncü parti için teknik olarak zaten imkânsız).
- Kamera ile QR okuma yok (PC'de kamera yok).
- İnternet/bulut/senkronizasyon yok; tüm veriler yalnız bu makinede kalır.
- Electron/tarayıcı motoru gibi ağır çatılar yok (RAM hedefi).
- Telefondaki hesaplar silinmez/değiştirilmez; hiçbir işlem telefondaki kurulumu etkilemez.
- Kripto para/Steam gibi özel karakter setleri gerekmez; standart TOTP kapsamdadır.

## Kısıtlar

- Windows 10/11; kullanıcının makinesinde Python 3.14 kurulu (`C:\Python314`), uv ile CPython 3.12 de mevcut (uyumluluk yedeği).
- Planlanan bağımlılıklar: `customtkinter` (UI), `pyotp` (TOTP), `pystray` + `Pillow` (tepsi/ikon), `opencv-python` (yalnızca içe aktarma sırasında tembel yüklenir). DPAPI `ctypes` ile. Windows Hello için küçük bir WinRT köprüsü paketi (pywinrt/`winsdk`) kullanılabilir; paket kurulamaz/çalışmazsa saf `ctypes` CredUI istemi, o da olmazsa uygulama PIN'ine düşülür (kurulum adımında uygulayıcı doğrular).
- Dağıtım: PyInstaller ile exe (paketleme detayı uygulayıcı kararı).
- Kullanıcı non-teknik; tüm arayüz metinleri Türkçe ve sade olmalı.

## Kararlar (tasarım sahibinin çağrıları)

- Arayüz: B düzeni + dikey pencere + sistem teması (mockup: layout.html / portrait.html / themes.html).
- TOTP: `pyotp`; standart TOTP (SHA1/6/30). Farklı parametreli kayıtlar yüklenebilir; üretilemeyen tür kullanıcıya bildirilir ve satırda "desteklenmiyor" olarak gösterilir.
- Kimlik mükerrerliği: gizli anahtar (secret) kimliktir. Aynı secret zaten varsa kayıt atlanır; mevcut kayıt (kullanıcı düzenlemeleri dahil) korunur. Aktarım özeti atlananları sayar.
- Kısmi/çoklu QR seti: okunabilen tüm görseller aktarılır; okunamayan görseller tek tek raporlanır; Google 10'ar hesaplık birden fazla QR üretirse hepsi sırayla bırakılabilir. Eksik batch için uyarı gösterilir.
- Depolama: `%APPDATA%\GoogleAuthPC\` altında; hesap dosyası (`accounts.json`) DPAPI `CryptProtectData` ile şifreli tek blob; ayarlar (`config.json`) düz (hassas veri içermez). PIN, PBKDF2 (tuzlu hash) olarak saklanır.
  - Not: DPAPI veriyi kullanıcı oturumuna bağlı şifreler; PIN ek bir şifreleme katmanı değildir, ekrana bakılmasını engelleyen arayüz kilididir. Bu bilinçli bir sadelik tercihidir.
- PIN unutulursa: yerel veriler sıfırlanır ve telefondan yeniden aktarılır (kullanıcıya bu dille açıklanır). PIN kurtarma yoktur.
- Windows Hello iptal edilirse kilitli kalınır (atlatma yok). PIN: Windows Hello varsa ilk kurulumda **opsiyonel yedek** olarak önerilir (atlama serbest); Hello yoksa/kullanılamıyorsa ilk kurulumda **zorunlu**. Kilit ekranında birincil düğme "Windows ile doğrula"; PIN tanımlıysa ikincil "PIN kullan" bağlantısı görünür. Ayarlar'da PIN her zaman belirlenebilir/değiştirilebilir; Hello sonradan devre dışı kalır ve PIN yoksa kilit ekranı PIN belirlemeye yönlendirir.
- Kilit kapsamı: kilitliyken yalnız kilit ekranı görünür (liste, arama, ekleme, içe aktarma, ayarlar erişilemez). Doğrulama sonrası o pencere oturumu boyunca her şey erişilebilir; pencere kapanınca yeniden kilitlenir. Tepsi "Ayarlar" → pencere kilitli açılır; doğrulama sonrası doğrudan Ayarlar ekranına iner. Tepsi "Kilitle" → pencereyi anında kilitler.
- Yeniden kilitlenme: pencere kapatıldığında anında; isteğe bağlı hareketsizlik kilidi ayarı (varsayılan kapalı).
- Tek örnek çalışma: ikinci kez başlatılırsa mevcut pencere öne getirilir ve kilitli tutulur (aynı veri dosyasına eşzamanlı yazım engellenir).
- Uygulama adı: "Google Auth PC" (pencere başlığı, tepsi ipucu, exe adı). Veri klasörü adı: `GoogleAuthPC`; GitHub deposu: `batuhansavas-yilmaz/Google-Auth-PC`.
- Tüm arayüz dili Türkçe; kod içi tanımlayıcılar İngilizce.

## Doğrulama yaklaşımı (özet)

- Birim testler (pytest): TOTP üretimi bilinen test vektörleriyle; otpauth-migration çözücü örnek yüklerle; mükerrer birleştirme mantığı; PIN hash doğrulama; depolama şifrele/çöz turu.
- Elle duman testi: kilit açma (Hello ve PIN), koda tıklayıp kopyalama, 30 sn yenilenme ve halka, tepsi menüsü, X ile gizleme, otomatik başlatma, örnek QR görseliyle aktarma, aynı görseli ikinci kez aktarınca mükerrer oluşmaması, tema değişimi, yeniden başlatmada boyut hatırlama.
- RAM ölçümü: boşta (tepside) Görev Yöneticisi'nden; hedef ~40-60 MB; `opencv` yalnızca aktarma sırasında import edilir.

## Uygulayıcıya bırakılanlar

- Dosya/modül yapısı ve iç mimari; bağımlılık sürümleri ve Python 3.14 (gerekirse 3.12) uyum testi.
- Sürükle-bırak desteği (`tkinterdnd2` değerlendirmesi; olmazsa "Görsel dosyası seç…" düğmesi tek yol olarak kalır — tıklanabilir bırakma alanı).
- İkon tasarımı, hata mesajları, "Kopyalandı" geri bildirim biçimi, geri sayım halkası çizimi (customtkinter canvas), erişilebilirlik küçük detayları.
- Paketleme (PyInstaller) ve otomatik başlatma teknik yolu (HKCU Run anahtarı veya Başlangıç klasörü kısayolu).
- İlk açılış akışının sırası (PIN belirleme, tanıtım, örnek ekranlar).
- Test dosyalarının organizasyonu ve CI'sız yerel çalıştırma talimatları.
