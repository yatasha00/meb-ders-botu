import streamlit as st
from google import genai
import gspread
from google.oauth2.service_account import Credentials
import datetime
import json

def save_to_sheet(kazanim):
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
        now = turkiye_saati.strftime("%d.%m.%Y %H:%M")
        
        # Tabloya sadece 2 sütun kaydediyoruz: Tarih | Kazanım
        sheet.append_row([now, kazanim])
        return True
    except Exception as e:
        print(f"Google Sheet'e kaydederken hata: {e}") 
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
        
        # YAPAY ZEKAYA YENİ VE İNŞACI BİLİŞİM TALİMATI
        prompt = f"""
        Sen 'Bilgisayar ve Öğretim Teknolojileri Eğitimi' (BÖTE) alanında uzman, 'İnşacı Öğretim Yaklaşımını' (Constructivism) kusursuz uygulayan bir yapay zeka asistanısın.
        Kullanıcının girdiği Bilişim Teknolojileri konusu/kazanımı: '{kazanim}'
        
        ÖNEMLİ KONTROL: 
        Bu metnin bilgisayar eğitimi, kodlama, algoritma, dijital vatandaşlık veya yazılım ile ilgili geçerli bir konu olup olmadığını kontrol et. Eğer alakasız, tek kelimelik (örn: 'elma', 'kusmak') veya anlamsız bir girişse SADECE ŞU KODU YAZ: "HATA_GECERSIZ_KAZANIM" ve başka hiçbir şey yazma.
        
        Eğer konu Bilişim alanına uygunsa, bu konuyu öğrencilere doğrudan anlatmak yerine, kendi kendilerine keşfederek öğrenecekleri "5E İNŞACI ÖĞRETİM MODELİNE" göre bir ders planı hazırla.
        
        Yanıtını şu 5 başlıkla oluştur:
        1. GİRME (Engage): Öğrencilerin dikkatini çekecek, konuyla ilgili gerçek hayattan bir problem durumu.
        2. KEŞFETME (Explore): Öğrencilerin bilgisayar başında veya kağıt üzerinde deneyerek kavramı keşfedecekleri bir aktivite.
        3. AÇIKLAMA (Explain): Öğretmenin kavrama doğru teknik ismi vereceği ve bulguları özetleyeceği Sokratik sorular.
        4. DERİNLEŞTİRME (Elaborate): Öğrencilerin bu kavramı farklı bir probleme uygulayacakları yeni bir görev.
        5. DEĞERLENDİRME (Evaluate): Öğrencinin süreci yansıtacağı bir değerlendirme yöntemi.
        """
        
        with st.spinner("İnşacı ders planınız özenle hazırlanıyor... Lütfen bekleyin."):
            try:
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                )
                
                # TROLL VEYA GEÇERSİZ KAZANIM KONTROLÜ
                if "HATA_GECERSIZ_KAZANIM" in response.text or "HATA_EGITIM_DISI" in response.text:
                    st.error("🚨 Hata: Lütfen geçerli bir Bilişim Teknolojileri konusu girin. (Örn: 'Döngüler' veya 'Siber Zorbalık'). Alakasız girişler reddedilmektedir.")
                else:
                    # Başarılıysa doğrudan kaydediyoruz (Tahmini ders arama kodunu sildik)
                    save_to_sheet(kazanim)
                    
                    # Sonucu Ekrana Basıyoruz
                    st.success("İnşacı ders planı başarıyla oluşturuldu!")
                    st.markdown("---")
                    st.markdown(response.text)
                
            except Exception as e:
                st.error(f"Bir hata oluştu: {e}")
                            
                    
