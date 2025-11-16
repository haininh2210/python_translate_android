from deep_translator import GoogleTranslator
from bs4 import BeautifulSoup
import os
import time

# ==== CẤU HÌNH NGÔN NGỮ ====
SOURCE_LANG = 'auto'   # để auto detect
# Đặt file này vào root project, cùng hàng với 'app'
# TARGET_LANGS ngôn ngữ cần được dịch
# sau khi dịch xong sẽ tự thêm file strings vào res/value-[code ngôn ngữ]/
# Nếu ngôn ngữ đích đã tồn tại sẽ đổi tên file đã có thành strings_old
# ['vi'] or ['pt-BR', 'vi', 'id']
TARGET_LANGS = ['ja', 'ko']
# input file đang lấy mặc định 
INPUT_FILE = os.path.join('app', 'src', 'main', 'res', 'values', 'strings.xml')

# Mapping từ mã Android sang mã Google Translate
# Một số ngôn ngữ có mã khác nhau giữa Android và Google Translate
ANDROID_TO_GOOGLE_LANG_MAP = {
    'in': 'id',  # Indonesia: Android dùng 'in', Google Translate dùng 'id'
}


def get_google_translate_lang(android_lang: str) -> str:
    """Chuyển đổi mã ngôn ngữ Android sang mã Google Translate.
    
    Args:
        android_lang: Mã ngôn ngữ Android (có thể có region, ví dụ: 'in', 'in-rID')
    
    Returns:
        Mã ngôn ngữ cho Google Translate (ví dụ: 'id' cho 'in')
    """
    # Xử lý đặc biệt cho zh-CN và zh-TW
    code = android_lang.replace('_', '-').strip()
    # Đảm bảo đúng định dạng chữ hoa cho zh-CN, zh-TW
    if code.lower() == 'zh-cn':
        return 'zh-CN'
    if code.lower() == 'zh-tw':
        return 'zh-TW'
    # Xử lý trường hợp có region (ví dụ: 'in-rID' -> 'in')
    lang_code = code.split('-')[0]
    # Nếu có mapping thì dùng, không thì giữ nguyên
    return ANDROID_TO_GOOGLE_LANG_MAP.get(lang_code, lang_code)


def android_values_folder(lang_code: str) -> str:
    """Convert a language code to an Android values folder name.

    Examples:
      'vi' -> 'values-vi'
      'pt-BR' or 'pt_BR' -> 'values-pt-rBR'
    """
    if not lang_code:
        return 'values'
    code = lang_code.replace('_', '-').strip()
    # Xử lý đặc biệt cho zh-CN và zh-TW
    if code.lower() == 'zh-cn':
        return 'values-zh-rCN'
    if code.lower() == 'zh-tw':
        return 'values-zh-rTW'
    parts = code.split('-')
    if len(parts) == 1:
        return f'values-{parts[0]}'
    # language-region
    lang = parts[0]
    region = parts[1].upper()
    return f'values-{lang}-r{region}'


def load_existing_translations(path: str) -> dict:
    """Load existing translations from target file if it exists.
    
    Returns a dict mapping string name -> translated text.
    """
    if not os.path.exists(path):
        return {}
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'xml')
        
        existing = {}
        for s in soup.find_all('string'):
            name = s.get('name')
            if name and s.string:
                existing[name] = s.string.strip()
        
        print(f"📖 Đã tải {len(existing)} trường đã dịch từ file đích")
        return existing
    except Exception as e:
        print(f"⚠️ Không thể đọc file đích hiện có: {e}")
        return {}


def escape_apostrophe(text: str) -> str:
    """Escape apostrophe (') to \' for Android strings.xml compatibility."""
    return text.replace("'", "\\'")


def backup_if_exists(path: str):
    """If path exists, rename it to strings_old.xml (append timestamp if needed)."""
    if not os.path.exists(path):
        return
    dirpath = os.path.dirname(path)
    backup_path = os.path.join(dirpath, 'strings_old.xml')
    if os.path.exists(backup_path):
        ts = time.strftime('%Y%m%d%H%M%S')
        backup_path = os.path.join(dirpath, f'strings_old_{ts}.xml')
    os.replace(path, backup_path)


def translate_for_target(android_lang: str):
    # android_lang là mã Android (ví dụ: 'in')
    # Dùng android_lang để tạo thư mục (giữ nguyên 'in')
    values_folder = android_values_folder(android_lang)
    res_dir = os.path.join('app', 'src', 'main', 'res', values_folder)
    os.makedirs(res_dir, exist_ok=True)
    target_file = os.path.join(res_dir, 'strings.xml')
    
    # Chuyển đổi sang mã Google Translate để dịch (ví dụ: 'in' -> 'id')
    google_lang = get_google_translate_lang(android_lang)
    
    # Load existing translations from target file
    existing_translations = load_existing_translations(target_file)
    
    # Re-parse the original file for each language so we don't reuse translated text
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'xml')

    strings = soup.find_all('string')
    translator = GoogleTranslator(source=SOURCE_LANG, target=google_lang)

    print(f"\nDịch sang: {android_lang} (Google Translate: {google_lang}) — Tổng số dòng: {len(strings)}")
    translated_count = 0
    reused_count = 0
    skipped_count = 0

    # Remove elements marked translatable="false" from the soup so they are not copied to output
    removed = 0
    for s in list(strings):
        if s.has_attr('translatable') and s['translatable'].lower() == 'false':
            print(f"🗑️ Loại bỏ khỏi output do translatable=false: name='{s.get('name')}'")
            s.decompose()
            removed += 1

    if removed:
        # re-find strings after removal
        strings = soup.find_all('string')

    for s in strings:
        string_name = s.get('name')
        # Check if this string already exists in target file
        if string_name and string_name in existing_translations:
            s.string.replace_with(existing_translations[string_name])
            reused_count += 1
            print(f"♻️ Sử dụng lại bản dịch: name='{string_name}' -> '{existing_translations[string_name]}'")
            continue

        # Nếu là text đơn giản, dịch như cũ
        if s.string:
            original_text = s.string.strip()
            if not original_text:
                continue
            try:
                translated_text = translator.translate(original_text)
                translated_text = escape_apostrophe(translated_text)
                s.string.replace_with(translated_text)
                translated_count += 1
                print(f"[{translated_count}/{len(strings)}] ✓ {original_text} -> {translated_text}")
            except Exception as e:
                print(f"❌ Lỗi dịch '{original_text}': {e}")
        else:
            # Nếu có thẻ HTML bên trong, dịch từng phần text, giữ nguyên thẻ
            def translate_html(node):
                for child in node.children:
                    if hasattr(child, 'string') and child.string:
                        text = child.string.strip()
                        if text:
                            try:
                                translated = translator.translate(text)
                                translated = escape_apostrophe(translated)
                                child.string.replace_with(translated)
                            except Exception as e:
                                print(f"❌ Lỗi dịch '{text}': {e}")
                    elif hasattr(child, 'children'):
                        translate_html(child)
            try:
                translate_html(s)
                translated_count += 1
                print(f"[{translated_count}/{len(strings)}] ✓ (HTML) {s.get_text()}")
            except Exception as e:
                print(f"❌ Lỗi dịch HTML '{s.get_text()}': {e}")

    # backup_if_exists(target_file)
    with open(target_file, 'w', encoding='utf-8') as f:
        f.write(str(soup))

    print(f"✅ Đã lưu: {os.path.abspath(target_file)}")
    print(f"📊 Thống kê: Dịch mới: {translated_count} | Tái sử dụng: {reused_count} | Bỏ qua: {skipped_count} | Tổng: {len(strings)}")


if __name__ == '__main__':
    # Basic checks
    if not os.path.exists(INPUT_FILE):
        print(f"Không tìm thấy file nguồn: {INPUT_FILE}. Hãy đặt file strings.xml ở cùng thư mục với script này.")
        raise SystemExit(1)

    # Nhập danh sách mã ngôn ngữ từ người dùng
    lang_input = input("Nhập danh sách mã ngôn ngữ (cách nhau bởi dấu phẩy, ví dụ: vi,ja,ko): ")
    user_langs = [x.strip() for x in lang_input.split(',') if x.strip()]

    if not user_langs:
        print("Bạn chưa nhập mã ngôn ngữ nào!")
        raise SystemExit(1)

    for tgt in user_langs:
        translate_for_target(tgt)

    print('\nTất cả ngôn ngữ đã xử lý.')

#Ngôn ngữ,Mã
# Afrikaans,af
# Albania,sq
# Amharic,am
# Ả Rập,ar
# Armenia,hy
# Assamese,as
# Aymara,ay
# Azerbaijan,az
# Bambara,bm
# Basque,eu
# Belarus,be
# Bengal,bn
# Bhojpuri,bho
# Bosnia,bs
# Bulgaria,bg
# Catalan,ca
# Cebuano,ceb
# Chichewa,ny
# Tiếng Trung (Giản thể),zh-CN
# Tiếng Trung (Phồn thể),zh-TW
# Corsican,co
# Croatia,hr
# Séc,cs
# Đan Mạch,da
# Dhivehi,dv
# Dogri,doi
# Hà Lan,nl
# Anh,en
# Esperanto,eo
# Estonia,et
# Ewe,ee
# Filipino,tl
# Phần Lan,fi
# Pháp,fr
# Frisia,fy
# Galicia,gl
# Georgia,ka
# Đức,de
# Hy Lạp,el
# Guarani,gn
# Gujarat,gu
# Haiti Creole,ht
# Hausa,ha
# Hawaii,haw
# Hebrew,iw
# Hindi,hi
# Hmong,hmn
# Hungary,hu
# Iceland,is
# Igbo,ig
# Ilocano,ilo
# Indonesia,id
# Ireland,ga
# Ý,it
# Nhật Bản,ja
# Java,jw
# Kannada,kn
# Kazakh,kk
# Khmer,km
# Kinyarwanda,rw
# Konkani,gom
# Hàn Quốc,ko
# Krio,kri
# Kurd (Kurmanji),ku
# Kurd (Sorani),ckb
# Kyrgyz,ky
# Lào,lo
# Latin,la
# Latvia,lv
# Lingala,ln
# Litva,lt
# Luganda,lg
# Luxembourg,lb
# Macedonia,mk
# Maithili,mai
# Malagasy,mg
# Mã Lai,ms
# Malayalam,ml
# Malta,mt
# Maori,mi
# Marathi,mr
# Meiteilon (Manipuri),mni-Mtei
# Mizo,lus
# Mông Cổ,mn
# Myanmar,my
# Nepal,ne
# Na Uy,no
# Odia (Oriya),or
# Oromo,om
# Pashto,ps
# Ba Tư,fa
# Ba Lan,pl
# Bồ Đào Nha,pt
# Punjab,pa
# Quechua,qu
# Romania,ro
# Nga,ru
# Samoa,sm
# Phạn,sa
# Scots Gaelic,gd
# Sepedi,nso
# Serbia,sr
# Sesotho,st
# Shona,sn
# Sindhi,sd
# Sinhala,si
# Slovakia,sk
# Slovenia,sl
# Somali,so
# Tây Ban Nha,es
# Sundan,su
# Swahili,sw
# Thụy Điển,sv
# Tajik,tg
# Tamil,ta
# Tatar,tt
# Telugu,te
# Thái Lan,th
# Tigrinya,ti
# Tsonga,ts
# Thổ Nhĩ Kỳ,tr
# Turkmenistan,tk
# Twi,ak
# Ukraina,uk
# Urdu,ur
# Uyghur,ug
# Uzbek,uz
# Việt Nam,vi
# Wales,cy
# Xhosa,xh
# Yiddish,yi
# Yoruba,yo
# Zulu,zu