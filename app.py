import streamlit as st
from google import genai
import gspread
from google.oauth2.service_account import Credentials
import datetime
import json

# --- Google Sheets Ayarları ---
def save_to_sheet(kazanim):
    try:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        # JSON dosyası yerine Streamlit'in gizli kasasından bilgileri çekiyoruz
        creds_dict = json.loads(st.secrets["google_sheets_sifrem"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        
        sheet = client.open("Ders Planı Kayıtları").sheet1 
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([now, kazanim])
        return True
    except Exception as e:
        st.warning(f"Google Sheet'e kaydederken bir hata oluştu: {e}")
        return False

# --- Sayfa Ayarları ---
st.set_page_config(page_title="MEB Ders Planı Asistanı", page_icon="📚")

st.title("📚 MEB Uyumlu Ders Planı ve Etkinlik Botu")
st.markdown("""
Öğretmenler için zaman kazandıran asistan! Haftanın kazanımını girin; ön bilgi ölçme etkinliği, vaka analizi ve çalışma kağıdınız saniyeler içinde hazır olsun.
""")

# API anahtarını doğrudan Streamlit'in gizli kasasından çekiyoruz
try:
    api_key = st.secrets["gemini_api_key"]
except KeyError:
    st.error("API anahtarı bulunamadı! Lütfen Streamlit Secrets ayarlarını kontrol edin.")
    st.stop()

# Ana ekranda kullanıcıdan kazanım alma
kazanim = st.text_input("Bu Haftanın Kazanımı Nedir?", placeholder="Örn: Dijital Etik, İklim Değişikliği, Cümlenin Ögeleri...")

# Butona tıklandığında çalışacak işlemler
if st.button("Ders İçeriğini Hazırla", type="primary"):

    if not kazanim:
        st.warning("Lütfen bir ders kazanımı girin.")
    else:
        # Kazanımı arka planda Google Sheet'e kaydet
        save_to_sheet(kazanim)

        # Gemini İstemcisi oluşturuluyor
        client = genai.Client(api_key=api_key)
        
        # Yapay zekaya vereceğimiz GÜNCELLENMİŞ talimat
        prompt = f"""
        Sen MEB müfredatına tam hakim, yaratıcı ve uzman bir öğretmensin.
        Bana şu kazanım ile ilgili bir ders planı içeriği hazırla: '{kazanim}'
        
        Lütfen yanıtını aşağıdaki 3 ana başlık altında, açık ve anlaşılır bir dille oluştur:
        
        1. Ön Bilgi Ölçme Etkinliği
        (Öğrencilerin bu konu hakkındaki mevcut bilgilerini ve olası kavram yanılgılarını ortaya çıkaracak, derse merak uyandırarak giriş yapmayı sağlayacak etkileşimli bir etkinlik planla. Bu bir B-İ-Ö tablosu uygulaması, kısa bir sokratik sorgulama, ilgi çekici bir beyin fırtınası sorusu veya kavram karikatürü tarzı bir tartışma olabilir.)
        
        2. Kısa Hikaye veya Vaka Analizi
        (Öğrencilerin ilgisini çekecek, derse giriş veya pekiştirme amaçlı kullanılabilecek, yaş grubuna uygun kısa bir hikaye veya olay kurgusu.)
        
        3. Çalışma Kağıdı Taslağı
        (Öğrencilerin ders sonunda doldurabileceği, açık uçlu sorular, boşluk doldurma veya eşleştirme gibi bölümler içeren yapılandırılmış bir çalışma kağıdı metni.)
        """
        
        with st.spinner("Ders içeriğiniz özenle hazırlanıyor... Lütfen bekleyin."):
            try:
                # Gemini 2.5 Flash modelini kullanarak içerik üretimi
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                )
                
                # Sonucu ekrana yazdırma
                st.success("İçerik başarıyla oluşturuldu ve aramanız veritabanına kaydedildi!")
                st.markdown("---")
                st.markdown(response.text)
                
            except Exception as e:
                st.error(f"Bir hata oluştu: {e}")
