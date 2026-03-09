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
        
        # Tarih ve zamanı al
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Tabloya 3 sütun olarak kaydet: Tarih | Tahmini Ders | Kazanım
        sheet.append_row([now, tahmini_ders, kazanim])
        return True
    except Exception as e:
        print(f"Google Sheet'e kaydederken hata: {e}") # Sadece arka planda yazar, ekranı bozmaz
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
        # DİKKAT: O eski hatalı save_to_sheet satırını buradan sildik!
        
        # Gemini İstemcisi oluşturuluyor
        client = genai.Client(api_key=api_key)
        
        prompt = f"""
        Sen MEB müfredatına tam hakim, yaratıcı ve uzman bir öğretmensin.
        Kullanıcının girdiği kazanım: '{kazanim}'
        
        ÖNEMLİ GÜVENLİK KONTROLÜ: 
        Öncelikle bu metnin okul, eğitim veya pedagojik bir konu olup olmadığını kontrol et. Eğer kullanıcı küfür, argo, anlamsız (örn: 'arda mal') veya eğitimle tamamen alakasız bir şey yazdıysa SADECE ŞU GİZLİ KODU YAZ: "HATA_EGITIM_DISI" ve başka hiçbir şey yazma.
        
        Eğer konu eğitimle ilgiliyse, ÖNCE bu kazanımın MEB müfredatında hangi derse ait olduğunu tahmin et. 
        Yanıtının EN BAŞINA tam olarak şu formatta yaz:
        Tahmini Ders: [Dersin Adı]
        
        Ardından şu 3 başlıkta içeriği üret:
        1. Ön Bilgi Ölçme Etkinliği
        2. Kısa Hikaye veya Vaka Analizi
        3. Çalışma Kağıdı Taslağı
        """
        
        with st.spinner("Ders içeriğiniz özenle hazırlanıyor... Lütfen bekleyin."):
            try:
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                )
                
                # TROLL / SAÇMA METİN KONTROLÜ
                if "HATA_EGITIM_DISI" in response.text:
                    st.error("🚨 Lütfen sadece okul, ders veya eğitimle ilgili geçerli bir konu girin. Alakasız girişler reddedildi.")
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
