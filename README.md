# Google Auth PC

Windows için çevrimdışı, hafif bir 6 haneli doğrulama kodu (TOTP) uygulaması.

## Ne işe yarar

Telefonun elinde olmadığında PC'den 6 haneli doğrulama kodlarını görürsün. İnternet gerektirmez; kodlar cihazında üretilir. Uygulama tepside (sistem tepsisi) durur ve düşük bellek kullanır.

## Kurulum (exe)

`dist\GoogleAuthPC.exe` dosyasına (veya masaüstündeki kopyasına) çift tıkla.

- Aynı anda tek örnek çalışır.
- Uygulama kilitlidir; Windows Hello (parmak izi, yüz veya hesap parolası) ile açılır. İstersen yedek olarak 6 haneli bir PIN de belirleyebilirsin.
- Pencereyi kapatan **X** uygulamayı kapatmaz, tepsiye küçültür.
- Tepsi menüsü: **Aç**, **Kilitle**, **Ayarlar**, **Çıkış**.

## Telefondan aktarma (4 adım)

1. Google Authenticator'ı aç.
2. **Ayarlar → Hesapları aktar → Dışa aktar**'ı seç, hesapları işaretle.
3. Çıkan her QR ekranının görüntüsünü al (hesap çoksa birkaç QR olur).
4. Görüntüleri PC'ye at ve uygulamada **+ Ekle → Görselleri seç** ile ekle (sürükleyip bırakabilirsin de).

Aynı görselleri tekrar eklersen mevcut hesaplar çoğaltılmaz.

## Geliştirme

```powershell
uv venv
uv pip install --python .venv\Scripts\python.exe -e .[dev]
.venv\Scripts\python.exe -m pytest
```
