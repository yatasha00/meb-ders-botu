import streamlit as st
from google import genai
import gspread
from google.oauth2.service_account import Credentials
import datetime
import json

# --- Google Sheets Ayarları ---
def save_to_sheet(tahmini_ders, kazanim):
    try:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds_dict = dict(st.secrets["google_sheets_sifrem"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        
        sheet = client.open("Ders Planı Kayıtları").sheet1 
        
        # Sunucu saatini alıp Türkiye saatine (UTC+3) çeviriyoruz
        sunucu_saati = datetime.datetime.now(datetime.timezone.utc)
        turkiye_saati = sunucu_saati + datetime.timedelta(hours=3)
        
        # Türkiye standartlarında Gün.Ay.Yıl Saat:Dakika formatına getiriyoruz
        now = turkiye_saati.strftime("%d.%m.%Y %H:%M")
        
        # Tabloya 3 sütun olarak kaydet: Tarih | Tahmini Ders | Kazanım
        sheet.append_row([now, tahmini_ders, kazanim])
        return True
    except Exception as e:
        print(f"Google Sheet'e kaydederken hata: {e}") # Sadece arka planda yazar, ekranı bozmaz
        return False

# --- Sayfa Ayarları ---
st.set_page_config(page_title="MEB Ders Planı Asistanı", page_icon="📚")

st.title("💻 İnşacı Bilişim Teknolojileri Ders Asistanı")
st.markdown("""
Bilişim öğretmenleri için inşacı yaklaşıma (5E Modeli) uygun ders tasarımı asistanı. 
Soyut programlama kavramlarını (Algoritma, Döngüler, Scratch, Python) öğrencilerinize keşfettirecek projeler ve senaryolar saniyeler içinde hazır!
""")

# API anahtarını doğrudan Streamlit'in gizli kasasından çekiyoruz
try:
    api_key = st.secrets["gemini_api_key"]
except KeyError:
    st.error("API anahtarı bulunamadı! Lütfen Streamlit Secrets ayarlarını kontrol edin.")
    st.stop()

# Ana ekranda kullanıcıdan kazanım alma
kazanim = st.text_area("🎯 Bu Haftanın Bilişim Konusu/Kazanımı Nedir?", placeholder="Örn: Python'da Döngüler, Algoritma Mantığı, Siber Zorbalık, Scratch ile Oyun Tasarımı...")
# Butona tıklandığında çalışacak işlemler
if st.button("Ders İçeriğini Hazırla", type="primary"):
    if not kazanim:
        st.warning("Lütfen bir ders kazanımı girin.")
    else:
        # DİKKAT: O eski hatalı save_to_sheet satırını buradan sildik!
        
        # Gemini İstemcisi oluşturuluyor
        client = genai.Client(api_key=api_key)
        
        prompt = f"""
        Sen 'Bilgisayar ve Öğretim Teknolojileri Eğitimi' (BÖTE) alanında uzman, 'İnşacı Öğretim Yaklaşımını' (Constructivism) kusursuz uygulayan bir yapay zeka asistanısın.
        Kullanıcının girdiği Bilişim Teknolojileri konusu/kazanımı: '{kazanim}'
        
        ÖNEMLİ KONTROL: 
        Bu metnin bilgisayar eğitimi, kodlama, algoritma, dijital vatandaşlık veya yazılım ile ilgili geçerli bir konu olup olmadığını kontrol et. Eğer alakasız veya anlamsız bir girişse SADECE ŞU KODU YAZ: "HATA_GECERSIZ_KAZANIM"
        
        Eğer konu Bilişim alanına uygunsa, bu konuyu öğrencilere doğrudan anlatmak yerine, kendi kendilerine inşa ederek öğrenecekleri "5E İNŞACI ÖĞRETİM MODELİNE" göre bir ders planı hazırla.
        
        Yanıtını şu başlıklarla oluştur:
        
        1. GİRME (Engage): Öğrencilerin dikkatini çekecek, konuyla ilgili gerçek hayattan bir problem durumu veya kışkırtıcı bir soru. (Konuyu söyleme, merak uyandır).
        2. KEŞFETME (Explore): Öğrencilerin bilgisayar başında veya kağıt üzerinde gruplar halinde deneyerek, yanılarak ve tartışarak kavramı kendi kendilerine keşfedecekleri bir aktivite yönergesi.
        3. AÇIKLAMA (Explain): Öğrenciler keşfettikten sonra, öğretmenin kavrama doğru teknik ismi (algoritma, döngü vb.) vereceği ve öğrencilerin bulgularını özetleyeceği Sokratik soru örnekleri.
        4. DERİNLEŞTİRME (Elaborate): Öğrencilerin yeni öğrendikleri bu kavramı farklı bir probleme veya mini bir kodlama projesine (Scratch/Python vb.) uygulayacakları yeni bir görev.
        5. DEĞERLENDİRME (Evaluate): Öğrencinin süreci ve ortaya çıkardığı ürünü yansıtacağı (öz değerlendirme veya akran değerlendirmesi) bir rubrik veya açık uçlu değerlendirme soruları.
        """
        
        with st.spinner("Ders içeriğiniz özenle hazırlanıyor... Lütfen bekleyin."):
            try:
                response = client.models.generate_content(
                    model='gemini-2.5',
                    contents=prompt,
                )
                
                # TROLL / SAÇMA METİN KONTROLÜ
                # TROLL VEYA GEÇERSİZ KAZANIM KONTROLÜ
                if "HATA_GECERSIZ_KAZANIM" in response.text or "HATA_EGITIM_DISI" in response.text:
                    st.error("🚨 Hata: Lütfen geçerli bir Bilişim Teknolojileri konusu girin. (Örn: 'Algoritma kavramını açıklar' veya 'Siber Zorbalık'). Alakasız veya tek kelimelik girişler reddedilmektedir.")
                else:
                    # 1. Dersi yapay zekanın metninden cımbızla alıyoruz
                    tahmini_ders = "Bilinmeyen Ders"
                    for satir in response.text.split('\n'):
                        if "Tahmini Ders:" in satir:
                            tahmini_ders = satir.split("Tahmini Ders:")[1].strip()
                            break
                            
                    # 2. ŞİMDİ Google Sheets'e kaydediyoruz (Sadece düzgün konuları ve 2 bilgiyle)
                    save_to_sheet(tahmini_ders, kazanim)
                    
                    # 3. Sonucu Ekrana Basıyoruz
                    st.success(f"İçerik başarıyla oluşturuldu! (Algılanan Ders: {tahmini_ders})")
                    st.markdown("---")
                    st.markdown(response.text)
                
            except Exception as e:
                st.error(f"Bir hata oluştu: {e}")
