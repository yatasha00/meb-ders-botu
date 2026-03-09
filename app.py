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
        Sen MEB müfredatına tam hakim, yaratıcı ama aynı zamanda KATI KURALLARI olan bir uzman öğretmensin.
        Kullanıcının girdiği metin: '{kazanim}'
        
        ÖNEMLİ KAZANIM KONTROLÜ (ÇOK DİKKATLİ OKU):
        Görevin, girilen metnin MEB müfredatında yer alan gerçek, mantıklı bir 'kazanım' cümlesi veya resmi bir ünite konusu olup olmadığını denetlemektir. 
        Eğer kullanıcı 'kusmak', 'elma', 'oyun', 'arda mal' gibi tekil/genel kelimeler, eylem bildirmeyen belirsiz kelimeler, argo veya kazanım formatına uymayan gündelik şeyler yazdıysa, KESİNLİKLE İÇERİK ÜRETMEYECEKSİN.
        Bu durumda SADECE ŞU KODU YAZ: "HATA_GECERSIZ_KAZANIM" ve başka hiçbir şey yazma.
        
        (Kabul edilebilir örnekler: 'Hücrenin yapısını açıklar', 'Kuvvet ve Hareket', 'Mondros Ateşkes Antlaşması' vb.)
        
        Eğer metin MEB müfredatına uygun geçerli bir kazanım veya net bir konu ise, ÖNCE bu kazanımın hangi derse ait olduğunu tahmin et. 
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
                    model='gemini-1.5-flash-8b',
                    contents=prompt,
                )
                
                # TROLL / SAÇMA METİN KONTROLÜ
                if "HATA_GECERSIZ_KAZANIM" in response.text or "HATA_EGITIM_DISI" in response.text:
                    st.error("🚨 Hata: Lütfen geçerli ve tam bir MEB kazanımı girin. (Örn: 'Hücrenin yapısını açıklar' veya 'Sözcükte Anlam') Tek kelimelik rastgele ifadeler veya eğitim dışı girişler sistem tarafından reddedilmektedir.")
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
