
Kod ko‘rik hisobot (UCG SCI-Grade Platform 4.0.0)
Rahbar xulosasi: Ushbu hisobotda taqdim etilgan UCG SCI-Grade Platform dasturiy ta’minotining Python kod bazasi 100 punktli sinovdan o‘tkaziladi. Hisobot quyidagi bo‘limlarga bo‘lingan: sintaksis va uslubiy tekshiruvlar, arxitektura va dizayn, xavfsizlik, samaradorlik, sinov qamrovi, hujjatlash, bog‘liqliklar, CI/CD, litsenziya masalalari, xalqaro qo‘llab-quvvatlash, kirish imkoniyati, xatolarni ishlov berish, loglash, kuzatiluvchanlik, masshtablilik, qo‘llab-quvvatlash (Texnik parvarish), ma’lumot maxfiyligi, va joylashtirish. Har bir bo‘limda tekshiruv nuqtalari (checklist) keltiriladi, nima uchun muhimligi va qaysi vosita yoki sinov bilan tasdiqlanishi mumkinligi tushuntiriladi. Shuningdek, keng tarqalgan xatolar va antipatternlar misollari, ularni JavaScript, Python va Java tillarida qanday to‘g‘rilash bo‘yicha kod namunalariga o‘rin berilgan. Yakunda xatolarni tuzatish bo‘yicha kichik kod parchalar bilan tavsiyalar, sinov kaseslari va avtomatlashtirilgan testlarni (unit, integratsiya, e2e) misol keltiriladi. Xavfsizlikni mustahkamlash, bog‘liqliklarni tekshirish vositalari, CI/CD tavsiyalari, va eng yaxshi amaliyot bo‘yicha amaliy reja (prioritet, vaqt va xavf bahosi bilan) berilgan. Ustiga ustak, kod sifati va jarayonlarni ta’minlash uchun tavsiya etiladigan linterlar, test ramkalari va CI/CD provayderlari bo‘yicha solishtirma jadvallar keltirilgan. Kerakli yerda arxitektura va ish jarayoni diagrammalari (Mermaid) qo‘shilgan. Ushbu hujjatda ko‘proq rasmiy manbalar va yetakchi qo‘llanmalar nazarda tutilgan, masalan Python PEP8, OWASP Cheat Sheet va GitHub hujjatlari.

Sintaksis va tuzilma
[1] Sintaksis tekshiruvi: Kod Python3 mosligiga ega ekanini ta’minlash. Masalan, modul boshida joylashgan def, class, va import so‘zlari to‘g‘ri joylashganligiga, dosya oxirida kutilgan if __name__ == "__main__": bloki mavjudligiga e’tibor beriladi. Nima uchun: Sintaksis xatolari ishga tushirish vaqtida to‘xtashga olib keladi. Tekshirish: Kodni python -m py_compile bilan tekshirish yoki CI pipeline’da flake8/pylint orqali avtomatik aniqlash, sintaksis masalalariga urg‘u berish.
[2] Kod bloki chegaralari va indentatsiya: Har bir blok (funksiya, shart, sikl) to‘g‘ri indentatsiya qilingan va to‘rt bo‘shliq ishlatilganmi, tabs va bo‘shliq aralashmaganmi tekshirish. PEP8 bo‘yicha 1 darajadagi bo‘shliq 4 bo‘shliqqa teng bo‘lishi, chiziq uzunligi odatda 79 belgidan oshmasligi kerak. Nima uchun: Noto‘g‘ri indentatsiya va satr uzunligi kodni o‘qishni qiyinlashtiradi va kod sifatini pasaytiradi. Tekshirish: Flake8 yoki Pylint ishlatib, indentatsiya va uzunlik bo‘yicha ogohlantirishlarni tahlil qilish.
[3] Modul boshidagi bo‘limlar: Har bir faylda boshlang‘ich hujjat satri yoki sharh(lar) borligini, importlar modul izohlaridan keyin va boshqa kodlardan oldin to‘g‘ri joylashganligini tekshirish. Importlar alohida satrlarda, standart kutubxona, uchinchi tomon, mahalliy modul importlari ketma-ket guruhlarda bo‘lishi va guruhlar orasida bitta bo‘sh qatordan ajratilishi kerak. Nima uchun: To‘g‘ri import tartibi kodni o‘qishni yengillashtiradi va boshqarishni osonlashtiradi. Tekshirish: Vizual tekshiruv yoki linter (isort, flake8-import-order) qo‘llash orqali importlarning tartibini va bo‘sh qatorlarni aniqlash.
[4] Noma’lum identifikatorlar: O‘zgarmas nomlar, funksiyalar va sinflar nomlarini tekshirib, ularning ixtiyoriyligini ko‘rib chiqing (masalan, sintaksis xatolari yoki NameError keltirib chiqaradigan nomlari). Klasslar CamelCase bilan nomlanishi, funksiyalar va o‘zgaruvchilar kichik harflar bilan va bo‘shliq o‘rniga pastki chiziq bilan bo‘lishi tavsiya etiladi. Nima uchun: Nomlash konventsiyalariga rioya qilish kodni tushunishni osonlashtiradi. Tekshirish: Pylint kabi vositalar yoki kod sharhi bilan nom qo‘llanmalariga mos kelishini kuzatish.
[5] Keraksiz kod va takrorlar: Global o‘zgaruvchilar yoki ishlatilmayotgan importlar (psutil kabi bir xil modulni bir necha bor import qilish) mavjudligini aniqlash. Ikki marta ulangani aniqlangan kod qismlarini yagona modulga olish. Nima uchun: Keraksiz kod va importlar kodni tartibsizlashtiradi, xatolar xavfini oshiradi va samaradorlikni pasaytiradi. Tekshirish: vulture yoki flake8 vositalari yordamida ishlatilmayotgan kod bo‘laklari va takror importlarni topish.
Kod uslubi (Style)
[6] PEP8 va mos keluvchi stil: Python PEP8 yo‘riqnomalariga rioya qilinganini tekshiring. Masalan, bir qatorda ortiqcha bo‘sh joy yo‘qligi, satr 79 belgidan qisqaroq bo‘lishi (kommentariyalar uchun 72 belgi). Bloklarda ortiqcha bo‘sh joy bo‘lmasligi, teng (yoki ko‘p) bo‘lishi kerak (kod ichida spam(1) kabi). Nima uchun: Yagona kod uslubi jamoada kod o‘qilishini yaxshilaydi. Tekshirish: Linterlar (masalan, Flake8, Black) yordamida avtomatik formatlash va bo‘shliqni aniqlash.
[7] Nomlash va ta’sinlar: Funksiya va o‘zgaruvchilar nomlari pastki chiziq bilan kichik harflardan tashkil topgan bo‘lishi, sinflar esa Boshlang‘ich harflar bilan (CamelCase) bo‘lishi kerak. Konstanta nomlari katta harf va ostki chiziqlar bilan (MASALAN_VAL) bo‘lishi tavsiya etiladi. Xato nomlangan identifikatorlar kodni chalkashtiradi. Nima uchun: Kod o‘qilishini oshiradi va me’yorlarga mos bo‘ladi. Tekshirish: Pylint yoki boshqa static analizator yordamida nomlash yodgorliklarini tekshirish.
[8] Wildcard-importlardan saqlanish: Kutilmagan from module import * ko‘rinishlarini toping va bartaraf qiling. PEP8 bo‘yicha bunday importlar noto‘g‘ri qo‘llanadi, chunki ular namespace’da aniq bo‘lmagan elementlar paydo bo‘lishiga olib keladi. Nima uchun: Wildcard-import kodni o‘qishni va vositalar bilan analizni qiyinlashtiradi. Tekshirish: Matn bo‘yicha “import *” qidiruvi yoki linter (masalan, Flake8) yordami bilan aniqlash.
[9] Magic qiymatlardan qochish: Kutilmagan qatorda to‘g‘ridan-to‘g‘ri raqamlar yoki ma’lumotlar yozilishini (masalan, vaqt zonalari, API URL-lar va h.k.) aniqlang. Bunday qiymatlarni doimiy o‘zgaruvchi yoki sozlama sifatida ko‘rib chiqish kerak. Nima uchun: Magic qiymatlar kodni tushunishni qiyinlashtiradi. Tekshirish: Kutilmagan soniyalarga yoki stringlarga oid kodlarni qidirib, ularni nomlangan konstantalarga aylantiring.
[10] Talqinlar va sharhlar: Kod bloklarini tushuntiruvchi sharhlar va docstring’lar bor-yo‘qligini tekshiring. Har bir funksiyaning maqsadi, argumentlari va qaytaradigan qiymati dokumentatsiyalangan bo‘lsin (PEP257 bo‘yicha). Nima uchun: Yaxshi hujjatlangan kodni keyinchalik tushunish osonroq bo‘ladi. Tekshirish: Pylint va pydocstyle kabi vositalar yordamida docstring qoidalarini tekshirish.
Arxitektura va dizayn
[11] Ajratish tamoyillari (SoC): Kode bazasi modul va qatlamlarga bo‘linganligini baholang. Masalan, UI (Streamlit), biznes mantiqi, ma’lumotlar bazasi qatlamlari aniq ajratilganmi. Nima uchun: Modular arxitektura o‘lchamlilik va sinov qilishni osonlashtiradi. Tekshirish: Kodni tahlil qilib, alohida modul fayllar, sinflar yoki funksiya guruhlari mavjudligini aniqlash.
[12] Konfiguratsiya va sozlamalar: Muayyan parametrlar (API kalitlari, yo‘llar, model sozlamalari va h.k.) kode ichida yozilmagan, tashqi konfiguratsiya (yaml/ini/JSON) fayllarida bo‘lishi kerak. Nima uchun: Kod ichida qat’iy belgilangan parametrlar moslamalarga moslashuvchanlikni pasaytiradi. Tekshirish: Kode ichida config yoki setting nomli obyektlar, fayl o‘qish funksiyalari bor-yo‘qligini tekshirish.
[13] Masshtablilik va ko‘lamdorlik: Xizmat mustaqil modullardan iborat bo‘lishi, mikrokservis dizayniga mos yoki kamida mikroprotsessorli paralel ishga moslashtirilgan bo‘lishi zarur. Nima uchun: Yaxshi dizayn qator ishchi jarayonlarda kengaytirish imkonini beradi. Tekshirish: Kodi ichida bir nechta jarayon (multiprocessing) funksiyalari, yoki konteyner/veb-sokratlik (API-server) modellarining mavjudligini tekshirish.
[14] Ustuvor sanalar va jadvallar: Loyihaning umumiy arxitekturasini tushuntiruvchi diagram yoki blok-sxemani tekshiring. Misol uchun, foydalanuvchi kiritishi va natija chiqarish oqimini ko‘rsatuvchi Mermaid diagrammasini yaratishga harakat qiling. Nima uchun: Arxitektura tasviri kodni tushunishni sezilarli darajada osonlashtiradi. Tekshirish: Quyidagi ko‘rinishdagi Mermaid diagram yordamida dastur arxitekturasi tasvirlang:
Foydalanuvchi

Streamlit UI

Biznes mantiqi

ML/Statistik Model

Ma'lumotlar bazasi

Keshlash/Fayl tizimi



Показать код
[15] Xatoliklardan tiklanish (Resilience): Xatolik yuz berganda, muqobil yo‘l (fallback) bo‘lishi va foydalanuvchini ogohlantiruvchi qayta urinuvlar mexanizmi borligini tekshiring. Nima uchun: Kuchli arxitektura tizimni bardoshliligini oshiradi. Tekshirish: try/except bloklari va timeout qo‘shimchalari mavjudligini kodda qidirish (masalan, subprocess`da timeout qo‘shilgani tekshirilgan).
Xavfsizlik
[16] Kiritish ma’lumotlarini tekshirish: Foydalanuvchi kiritadigan barcha ma’lumotlar xavfsizlik nuqtai nazaridan filtrlanganini (sanitized) aniqlang. Masalan, sanitize_input funksiyasida r'[--;... ]' kabi regex ishlatilib \x00 va ' belgilar olib tashlanganini tekshirish. Nima uchun: Xavfsizlik bo‘yicha OWASP tavsiyasida keltirilganidek, server tomonida validatsiya va sanitizatsiya bo‘lmasa, SQL in’ektsiya va XSS hujumlari ehtimoli yuqori. Tekshirish: Analiz qilib, re.sub yoki parametrli so‘rovlar orqali xatli belgilar olib tashlanganini, SQL so‘rovlar parametrli usulda (? yoki %s) bajarilganini nazorat qilish.
[17] SQL injeksiyadan saqlanish: Agar sqlite3 yoki boshqa DB interfeyslaridan foydalanilsa, parametrli so‘rovlar (masalan, cursor.execute("SELECT ... WHERE id = ?", (user_id,))) qo‘llangan bo‘lishi kerak. String biriktirish usuli bilan so‘rov tuzilmaganini tekshiring, chunki bu SQL injeksiya xavfini keltirib chiqaradi. Nima uchun: OWASP bo‘yicha SQL injeksiyadan qochish uchun qat’iy parametrli so‘rovlar ishlatilishi kerak. Tekshirish: Kodda cursor.execute ustida + yoki .format bilan so‘rov tuzilmaganligini qidirish, ? yoki :param ishlatilganini tekshirish.
[18] Xujumga ta’sirchan ozgaruvchilar: exec, eval, notanish os.system yoki subprocess chaqiruvlari bilan foydalanuvchi ma’lumotini ishlatish tekshiriladi. Bunday xatolik keltirmaslik uchun subprocess.run(..., timeout=...) va shell=False kabi xavfsizlik parametrlaridan foydalaning. Nima uchun: Kodda noto‘g‘ri komandani bajarish (command injeksiya) xavfini oldini olish zarur. Tekshirish: “eval(” yoki “os.system” so‘zlarini grep yordamida qidirish yoki bandit kabi vositani ishga solish, subprocess chaqiruvlari uchun shell=False va timeout mavjudligini tekshirish.
[19] Maxfiy ma’lumotlarni boshqarish: Dastur ichida API kalitlari, parollar yoki sertifikatlar kabi maxfiy ma’lumotlar kodga yozilmaganligiga ishonch hosil qiling. Xavfsizlik yuzasidan OWASP tavsiyasiga ko‘ra maxfiylar alohida fayl va muhit o‘zgaruvchisida saqlanishi kerak. Nima uchun: Qattiq kodlangan maxfiy ma’lumotlar tarqalishi xavfli; ular ataylab git ignore qilinishi lozim. Tekshirish: Kutilmagan password= yoki api_key= iboralarini kodda qidirish, hamda python-dotenv yoki AWS Secrets Manager kabi vositalardan foydalanganini tekshirish.
[20] Shifrlash va xavfsiz aloqalar: Agar foydalanuvchi ma’lumotlari yoki sezgir ma’lumotlar saqlansa/shifrlansa (masalan, HTTPS), kuchli algoritmlardan (AES-256, RSA-2048) foydalanganini tekshiring. OWASP kriptografiya bo‘limida tavsiya qilingan standartlarga amal qilish muhim. Nima uchun: Zaif algoritmlar bilan ma’lumotlar oson buzilishi mumkin. Tekshirish: Kodda ssl, cryptography modulidan foydalanilgani yoki HTTPS konfiguratsiyasi tekshirish; shuningdek, joriy kutubxonalar versiyalari yangilanganiga e’tibor berish.
[21] Bog‘liqliklarni tekshirish: O‘rnatilgan kutubxonalar so‘nggi versiyada ekanligini va ma’lum xatarli xavfsizlik kamchiliklariga ega emasligini tekshirish. Masalan, pip-audit, safety, npm audit, yoki OWASP Dependency-Check kabi vositalarni ishga tushiring. Nima uchun: OWASPga ko‘ra kutubxonalarni muntazam yangilash zarur, zero-day zaifliklarini kamaytiradi. Tekshirish: Buyruqlar: pip install pip-audit && pip-audit, yoki JavaScript loyihalarida npm audit komandasini ishga tushirib bo‘shliq va xavfli bog‘liqliklarni aniqlash.
Ishlash samaradorligi (Performance)
[22] Algoritm va murakkablik: Eng katta ma’lumot to‘plamlari va jadvallar ustida kodni optimallashtirish kerak. Masalan, kerakli bo‘lmagan for sikllari, intensiv hisob-kitoblarni vektorlashtirish yoki numpy/scipy funksiyalaridan foydalanish orqali tezlatish mumkin. Nima uchun: Katta hajmli ma’lumotlar bilan ishlashda operatsiyalarni tekshirish, ortiqcha qayta ishlashni olib tashlash zarur. Tekshirish: Profilerni (cProfile, line_profiler) ishlatib sekin qismlarni aniqlash, keyin algoritm optimizatsiyasi.
[23] Kesh va qayta foydalanish: Bir xil hisob-kitob yoki ma’lumot so‘rovi takror qilinmasligi uchun keshlashni qo‘llash (masalan, functools.lru_cache yoki SQLite query caching). Sizning kod qisman maxsus funksiyalar uchun natijalarni vaqtincha saqlash imkoniyatiga ega bo‘lishi mumkin. Nima uchun: AWASPda keltirilganidek, keraksiz qayta ishlovlar va tarkibni keshlamaslik qimmat zamon va resurslarni sarflaydi. Tekshirish: Kodda takroriy ma’lumotlarni keshga olish xususiyatlarini qidirish, yoki kesh modul (diskcache, redis) integratsiyasi tekshirish.
[24] I/O operatsiyalarini optimallashtirish: Fayl va tarmoq operatsiyalarida katta hajmli o‘qish/yazish noto‘g‘ri ishlashga olib kelishi mumkin. Masalan, faylni butunlay emas, striming orqali o‘qish. Nima uchun: Ma’lumot oqimini boshqarish Ishlash tezligini oshiradi. Tekshirish: Kode ichida open() chaqiruvi ustida encoding="utf-8" belgilanganligini tekshirish (unicode bilan muammo bo‘lishi mumkin) va kerak bo‘lsa with konstruktsiyasidan foydalanish bilan resurslarni avtomatik yopish.
[25] Parallelizm va asinxronlik: CPU-chekkan vazifalar uchun multiprocessing yoki asyncio dan foydalanish mumkin. Kodda Windows uchun if __name__ == "__main__": qo‘llanishi multiprocessing uchun to‘g‘ri importni ta’minlaydi (FIX #4 talqin). Nima uchun: G‘olib server resurslaridan samarali foydalanish ish qilish tezligini oshiradi. Tekshirish: Kodda multiprocessing yoki concurrent.futures ishlatilganini ko‘rish va qayerda ishlayotganligini tahlil qilish.
[26] Obraz/grafik kitobxonalar: Agar matplotlib yoki plotly kutubxonalari katta ma’lumotli grafikalar chizish uchun ishlatilsa, ularning konfiguratsiyasi noto‘g‘ri bo‘lsa, ob’ektlar ko‘p joyni egallashi mumkin. Masalan, Plotly issiqlik xaritasini chizishda ma’lumotlar doimiy shkala bilan (min/max) chizilishi kerak (FIX #7). Nima uchun: Grafika va vizualizatsiyalar bilan ishlashda belgilangan formatlar ishlashni yaxshilaydi. Tekshirish: Koddagi px.imshow yoki plotly.graph_objs chaqiruvlarida zmin/zmax berilganini tekshirish (global min/max).
[27] Ishonchlilik: Ish yukiga (memory, CPU) qarshi test qilish. Misol uchun, fayllar hajmi yoki ma’lumotlar oqimi katta bo‘lganda try/except bloklari bilan chiqib ketadigan holatlarni (metod timeout, ma’lumotlar yetishmasligi kabi) sinash kerak. Nima uchun: Dastur kattaroq kutilmagan yuk ostida ham ishlashini ta’minlash muhim. Tekshirish: Kodni stress-test skriptlari bilan sinab ko‘ring yoki e2e testlarda yuqori yukni simulyatsiya qiling.
Sinovlar (Testing)
[28] Birlik testlar: Har bir funksiya va modul uchun unit-test yozing. Masalan, pytest frameworkda test funksiyalarini yaratib, assert bilan natijalarni solishtiring. Nima uchun: Unit-testlar alohida xatoliklarni tez aniqlash va regressiyani oldini olish uchun xizmat qiladi. Tekshirish: Masalan, sanitize_input uchun quyidagicha test yoziladi:

python
Копировать
def test_sanitize_input_removes_unsafe_chars():
    assert sanitize_input("Hello; DROP") == "Hello DROP"
[29] Chegaraviy holatlar: To‘g‘ri natija olinishi kutilgan chegaraviy va noto‘g‘ri kirish qiymatlarini sinash (null, bo‘sh string, juda katta raqam, noto‘g‘ri format va h.k). Nima uchun: OWASP tavsiyalarida ham chet holatlarni sinash xavfsizlik va barqarorlik uchun muhim. Tekshirish: Unit-test da with pytest.raises(...) bloki bilan xato kutilayotgan hollarda test yozish yoki parametrize bilan turli kirishlarni qamrab olish.

[30] Integratsion testlar: Turli komponentlarning (masalan, UI → biznes mantiq, mantiq → DB) birgalikda ishlashini tekshirish. Streamlit ilovasini minik serverda ishga tushirib, Selenium yoki Playwright kabi asinxron vosita bilan foydalanuvchi oqimini test qiling. Nima uchun: Bittalab qatlamlar orasidagi o‘zaro bog‘lanish buzilmaganini tekshirish muhim. Tekshirish: Misol uchun, Selenium bilan formani to‘ldirib, kutilgan natija sahifada chiqayotganini tekshirish.

[31] E2E (end-to-end) testlar: Foydalanuvchi portalini boshlang‘ich nuqtadan yakuniy natijagacha sinab ko‘ring. Masalan, pytest + Playwright orqali butun jarayonni (login, ma’lumot kiritish, hisobot ko‘rish) yozing. Nima uchun: Kodebardagi katta o‘zgarishlar qayerda qiyinchilik bo‘lishini aniqlash imkonini beradi. Tekshirish: Test kod misoli:

python
Копировать
from playwright.sync_api import sync_playwright

def test_full_user_flow():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("http://localhost:8501")
        page.fill("#user-input", "123")
        page.click("#run-button")
        assert "Natija" in page.inner_text("#result")
        browser.close()
[32] Test qamrovi va doimiylik: Kod o‘zgarishlari uchun doimiy avtomatlashtirilgan test kompilyatorlarni sozlash (masalan, GitHub Actions’ga biriktirish). Testlar har safar kod o‘zgarganida ham bajarilishi kerak. Nima uchun: Avtomatlashtirilgan testlar kod sifatini barqaror saqlaydi. Tekshirish: .github/workflows/ci.yml yoki boshqa CI konfiguratsiyasida pytest chaqirilib, coverage hisobotini olish mavjudligini tasdiqlash.

Hujjatlashtirish (Documentation)
[33] Kod ichidagi hujjatlar: Funktsiya va klasslar uchun docstring va izohlar to‘g‘ri berilganini tekshiring. Python’ning PEP 257 ga muvofiq tarzda qilingan bo‘lsin (kutilgan parametrlari, qaytariladigan qiymatlar, istisnolar). Nima uchun: Yaxshi hujjat kodni tushunishni tezlashtiradi va keyinchalik texnik parvarishni yengillashtiradi. Tekshirish: pydocstyle kabi vosita yoki qo‘l bilan funksiyalarning docstring bor-yo‘qligini tekshiring.
[34] README va qo‘llanma: Loyihaning README.md fayli, foydalanuvchi qo‘llanmasi yoki wiki mavjudligini ko‘rib chiqing. U erda o‘rnatish va boshlash bo‘yicha ko‘rsatmalar (masalan, requirements.txt va streamlit run app.py ishlatish), amallar ketma-ketligi bo‘lishi lozim. Nima uchun: Hujjatlar va loyiha shablonlari kodni boshqalar bilan baham ko‘rishda va boshqarishda yordam beradi. Tekshirish: README da loyiha maqsadi, dastlabki o‘rnatish, parametr sozlamalari haqida yozilganini tasdiqlash.
[35] Versiyalash va reliz hujjatlari: Loyihada versiya raqamini (masalan, __version__ = "4.0.0") va relizdagi o‘zgarishlar (CHANGELOG) belgilangani bor-yo‘qligini tekshirish. Nima uchun: Kengaytiriladigan loyihalarda versiyalar va o‘zgarishlar tarixi nazoratni osonlashtiradi. Tekshirish: __version__ yoki config.full_version kabi atributlardan foydalanish, CHANGELOG fayl bo‘lsa, u yangilanganligini ko‘rib chiqish.
Bog‘liqliklar (Dependencies)
[36] Paketlar ro‘yxati: Loyihada requirements.txt yoki Pipfile mavjud bo‘lib, kerakli paketlar qat’iy versiya raqamlari bilan ko‘rsatilganmi tekshiring. Nima uchun: Aniq versiyalar qayta tiklanadigan muhit yaratishga yordam beradi. Tekshirish: pip freeze > requirements.txt ishlatib, mavjud paketlar ro‘yxati bilan solishtirish; setup.py yoki pyproject.toml tarkibini tekshirish.
[37] Xavfsizlik skanerlash: Avvalo yuklab olingan paketlar xavfsizlikka oid muammolarga ega emasligini tekshirish. Python uchun pip-audit, safety; JavaScript uchun npm audit yoki yarn audit; Java uchun OWASP Dependency-Check kabi vositalar foydali. Nima uchun: Bog‘liqliklar eskirishi ko‘plab xavflarni keltirib chiqaradi. Tekshirish: Komandalar misolida: pip-audit -r requirements.txt va npm audit --production.
[38] Bog‘liq versiyalar mosligi: Asosiy kutubxona versiyalariga mos kelmaslik yoki ziddiyatli versiyalarni qidiring. Masalan, Pandas va Numpy versiyalarining mos kelishi, yoki streamlit versiyasi bilan kod mosligi. Nima uchun: Noto‘g‘ri versiya chalg‘ib qolish yoki API o‘zgarganda xatolarga olib keladi. Tekshirish: pip check qo‘mondonasi yoki pipdeptree yordamida versiya ziddiyatlari bor-yo‘qligini aniqlang.
[39] Kutilmagan modul: Kodga kutilmagan, noma’lum kutubxona (torchaudio, eski scipy modullari) qo‘shilmaganini tekshiring. Nima uchun: Keraksiz paketlar loyihani yuki va xavfsizlik riskini oshiradi. Tekshirish: requirements.txt bilan solishtirib, imkoni bo‘lmagan modullarni aniqlash.
CI/CD (Uzluksiz Integratsiya/Yetkazib berish)
[40] CI muhitini sozlash: Loyihada GitHub Actions, GitLab CI, Jenkins kabi CI konfiguratsiyasi mavjudligi tekshiriladi. Har bir commit yoki PR ochilganda testlar va lint tekshiruvlari avtomatik ishlashi kerak. Nima uchun: Avtomatlashtirilgan CI jarayoni xatolarni dastlabki bosqichda aniqlashga yordam beradi. Tekshirish: .github/workflows/ci.yml yoki .gitlab-ci.yml mavjudligini, undagi ishga tushirishlar (push, PR) va test bosqichlari (pytest, flake8) borligini tekshirish.
[41] Avtomatlashtirilgan lint va test: CI pipeline’da linter (flake8, eslint) va testlar (pytest, jest, mvn test) qatnashadi. Bu kod va uslubiy xatolarni merge’ga yuborishdan oldin ushlab qoladi. Nima uchun: Greptile’ning ta’kidlashicha, formatlash va oddiy testlar hammasi avtomatlashtirilishi kerak, inson qo‘lidan ko‘ra vositalar allaqachon hal qilishi lozim. Tekshirish: CI logini tekshirib, linter va test ishga tushganini ko‘ring.
[42] Qayta tarqatish (Deployment): Loyihada Dockerfile, Kubernetes manifest, Heroku/CloudFormation skritlari bo‘lsa, ularning mavjudligi va to‘g‘ri ishlashini tekshiring. Nima uchun: Qayta tarqatish uchun mustahkam CI/CD kanallari zarur. Tekshirish: Dockerfile yoki docker-compose.yml fayllari mavjudligini va sintaksisini tekshirish, shuningdek helm/kustomize konfiguratsiyasi mavjudligini ko‘rib chiqish.
[43] Sirlar va atrof-muhit o‘zgaruvchilari: CI serverida maxfiy ma’lumotlar (API kalitlari va h.) atrof-muhit o‘zgaruvchilaridan o‘qilishi va secrets manbaiga joylashtirilishini tekshiring. Nima uchun: Parollar, tokenlar kodga kiritilmasligi lozim. Tekshirish: GitHub Secrets yoki GitLab Vault sozlamalarida kerakli elementlar borligini tekshirish.
[44] Kod qabul qilish qoidalari: Pull request’lar bo‘yicha kod sharhlari va ko‘rib chiqish jarayonining standartlari borligini tekshiring. Masalan, PR tavsifi kiritilishi yoki kamida ikkita tekshiruvchidan rozilik talabi. Nima uchun: Tashqi versiyalarni qabul qilish madaniyatini mustahkamlash va sifatni nazorat qilish uchun kerak. Tekshirish: Loyihaning CONTRIBUTING.md faylida PR protseduralari (code review jarayoni) yozilgan bo‘lsa, shuni ko‘rib chiqish.
Litsenziya
[45] Litsenziya fayli: Loyihada rasmiy Litsenziya fayli bo‘lishi kerak (masalan, MIT, Apache-2.0, GPL). Nima uchun: Ochiq manba hujjatlarida litsenziya ochiq holda aks ettirilishi lozim (loyihaning huquqiy himoyasi uchun). Tekshirish: LICENSE yoki COPYING nomli faylning mavjudligini tasdiqlash va qaysi litsenziya ekanini aniqlash.
[46] Litsenziya qoidalarga moslik: Kod va foydalanilgan kutubxonalar litsenziya talablari bilan mos ekanligini tekshiring. Masalan, GPL litsenziyasi bo‘lsa, u bilan bog‘liq majburiyatlar bajarilishini ko‘rib chiqing. Nima uchun: Litsenziya buzilishi kompaniya uchun huquqiy xavf tug‘dirishi mumkin. Tekshirish: Foydalanilgan barcha open-source kutubxonalar litsenziyalarini tekshirib chiqing (masalan, pip-licenses, oss-detective kabi vositalar bilan).
Xalqaro qo‘llab-quvvatlash (I18n)
[47] Unicode qo‘llab-quvvatlash: Matnli ma’lumotlar har doim Unicode ko‘rinishida saqlanishi kerak. open(..., encoding="utf-8") kabi sozlamalar bilan ishlash zarur. Nima uchun: Turli tillar (lotin, kirill, xitoy va h.k.) bilan ishlaganda kod o‘zaro mos bo‘lishi uchun. Tekshirish: Kodda matnli fayl ochishlarda utf-8 belgilanganini ko‘rib chiqing.
[48] To‘liq tarjima imkoniyati: Foydalanuvchi interfeysidagi matnlar (label, button matnlari, sabit xabarlar) kod ichida qat’iy yozilmasdan, alohida resurs fayllarida saqlangan bo‘lishi lozim. Nima uchun: Keyinchalik boshqa tillarga osongina tarjima qilish uchun. Tekshirish: Matnli ifodalar bevosita chaqirilmagan, balki masalan, gettext yoki o‘xshash kutubxona bilan ishlatilganligini tekshiring.
[49] Dinamik formatlash: Sana, vaqt va valyuta formatlari mahalliy standardga mos bo‘lishi uchun locale modulidan foydalanish. Nima uchun: Turli hududlarda foydalanuvchi o‘zi qulay formatda ma’lumot ko‘rishini ta’minlaydi. Tekshirish: Kodda datetime.strftime qatorlarida qat’iy format ("%Y-%m-%d") emas, balki locale elementlari qo‘llanganini tekshirish.
[50] Ko‘p tilli yordam: Agar ilova ko‘p tilli interfeysga mo‘ljallangan bo‘lsa, foydalanuvchi tilini tanlash imkoniyati bo‘lishi va bu holatlarning sinovi bajarilishi kerak. Nima uchun: Global foydalanuvchilarga moslashish uchun. Tekshirish: Streamlit kodida st.selectbox kabi til tanlash vidjeti borligini tekshirish yoki lokalizatsiya kutubxonalari qo‘llanilganini ko‘rib chiqish.
Kirish imkoniyati (Accessibility)
[51] Alt matn va tavsiflar: Grafik elementlarga (st.image, st.chart, diagramlar) tavsiflovchi alt matn yoki tushuntirish berilganini tekshiring. Nima uchun: Ko‘rish qobiliyati cheklangan foydalanuvchilar skrin-o‘qish qurilmalari bilan ishlaganda ma’lumotni yo‘qotmasin. Tekshirish: Kodda alt yoki caption parametrlariga qarang va ularni to‘ldirishini tekshiring.
[52] Rang kontrasti: Foydalanuvchi interfeysidagi matn va fon ranglari orasidagi kontrast yetarli ekanini tekshiring. WCAG bo‘yicha qora (yoki 90% qora) matn oq rang fon ostida kamida 4.5:1 nisbatda bo‘lishi lozim. Nima uchun: Rang kontrasti kam bo‘lsa, rang ko‘ra olmagan foydalanuvchilar matnni o‘qiy olmaydi. Tekshirish: Kod dizaynida stillar tekshirilib, CSS yoki vizual parametrlar kontrast vositalaridan (axe, Lighthouse) foydalanib tekshirilsin.
[53] Klaviatura navigatsiyasi: Interfeys elementlari to‘liq klaviatura bilan boshqarilishi kerak (tugmalar, shakllar tab bilan tanlanishi, enter tugmasi bilan faollashtirilishi). Nima uchun: Ko‘zi ojiz foydalanuvchilar uchun sichqoncha bilan ishlamaslik imkoniyati zarur. Tekshirish: Streamlit elementlari (masalan st.button) uchun .button chaqiruvlarida key yoki on_click parametrlariga e’tibor bering, shuningdek st.selectbox va st.slider klaviatura bilan boshqariladimi aniqlang.
[54] Ta’limnomasozlik: Ekran o‘qiydigan qurilmalar uchun aria-label yoki role kabi atributlar kerak bo‘lsa, tekshirib chiqing. Nima uchun: Assistiv texnologiyalar foydalanuvchi tajribasini yaxshilaydi. Tekshirish: Streamlit’da maxsus atribut qo‘shish qiyinroq bo‘lsa-da, yuklangan grafiklar yonida matnli sharh yoki st.markdown() bilan ekvivalent ma’lumot berilishi mumkinligini tekshirish.
Xatolarni boshqarish (Error Handling)
[55] Istisno tutish: Dasturda barcha kutilmagan xatolar uchun try/except bloklari mavjudligini ko‘rib chiqing. Talab qilingan bo‘lsa, muammo haqida foydalanuvchiga tushunarli xabar ko‘rsating va tizimni urinishlar bilan qayta tiklang. Nima uchun: Mijozga noaniq yoki ichki ma’lumot (stack trace) ko‘rsatish xavfsizlik nuqtai nazaridan yomon. Tekshirish: Kodda barcha open, subprocess, db.connect kabi chaqiruvlar atrofiga try/except qo‘yilganini aniqlash.
[56] Ma’lumot oqim xatolari: Fayl yoki tarmoq bilan bog‘liq xatolar (masalan, fayl yo‘q, HTTP so‘rov bloklandi) uchun alohida xabarlar bering. Nima uchun: Aks holda, dasturning to‘liq ishdan chiqishi foydalanuvchi uchun yomon tajriba. Tekshirish: Xatoni tutuvchi kod bo‘lsa, foydalanuvchiga tushunarli natija yoki konsolda log chiqishi bilan javob qaytarganini ko‘rib chiqing.
[57] Spetsifik istisnolar: Raqamli ifodalar uchun umumiy Exception emas, alohida turlardagi istisnolarni (ValueError, KeyError va h.k.) tutish tavsiya etiladi. Nima uchun: Turli xatolarni ajratib ko‘rish va mos chora ko‘rish osonroq bo‘ladi. Tekshirish: Kodda except Exception: o‘rniga aniq turdagi istisno (except ValueError:) ishlatilganiga e’tibor bering.
[58] Fallback mexanizmlari: Agar ba’zi modul ishlamay qolsa (masalan, tashqi API ishlamayotgan bo‘lsa), muqobil yo‘l bo‘lishi kerak (keshingdan ma’lumot oling, oldingi natijani chiqarish va h.k.). Nima uchun: Ishlash davomiyligini ta’minlash uchun. Tekshirish: except bloklar ichida qisman ma’lumot qaytarish yoki saqlangan keshdan foydalanish kodlarini qidirish.
[59] Logging xato va ogohlantirishlari: Xato va ogohlantirish loglari alohida darajada (ERROR, WARNING) yozilganini tekshirish. Nima uchun: Keyinchalik tizim xatolarini tahlil qilish uchun loglar kerak bo‘ladi. Tekshirish: logger.error va logger.warning chaqiruvlari to‘g‘ri joyda mavjudligini va xabar matni foydalanuvchi uchun ma’noga ega ekanligini ko‘rib chiqing.
Loglash (Logging) va kuzatiluvchanlik (Observability)
[60] Log darajalari va formati: Kodda standart Python logging kutubxonasi to‘g‘ri sozlanganmi tekshiring. Masalan, logging.basicConfig boshida chaqirilgan, logger = logging.getLogger(__name__) ishlatilgan bo‘lishi kerak. Nima uchun: Qayta ishlatish va tahlil qilish oson bo‘lgan strukturalangan loglar zarur. Tekshirish: Kod boshida yagona konfiguratsiya borligini va INFO, ERROR kabi darajalar ishlatilganiga e’tibor berish.
[61] Maxfiy ma’lumotlarni logga yozmaslik: Login va boshqa shaxsiy ma’lumot loglarga tushmasligiga ishonch hosil qiling. OWASP tavsiyasi bu borada qat’iy: maxfiy ma’lumotni loglamaslik. Nima uchun: Log fayllari kengroq huquqlarga ega bo‘lishi mumkin va ular maxfiylik buzilishiga sabab bo‘lishi mumkin. Tekshirish: logger metodlarini tekshirish va log matnida parol yoki kredit karta raqamlari kabi sezgir ma’lumot yo‘qligini ta’minlash.
[62] Logni rotatsiya va saqlash: Yirik loyihalarda log hajmi oshadi, eski loglarni avtomatik kesish (rotate) bo‘lishi kerak. Masalan, RotatingFileHandler yoki bulutli log saqlash (Azure Log Analytics, ELK) qo‘llanilishi mumkin. Nima uchun: Cheksiz log qo‘yish server resursini yopishi mumkin. Tekshirish: logging.handlers ostida RotatingFileHandler yoki TimedRotatingFileHandler ishlatilganini tekshirish.
[63] Tizim kuzatuvi va metrikalar: Dasturdagi muhim metrikalar (masalan, modelni chaqirish soni, IP ylko‘pligi, kechiktirish vaqti) Monitoring uchun chiqarilganmi? Grafana/Prometheus kabi tizimlar bilan integratsiya yo‘qmi ko‘rib chiqing. Nima uchun: Ishlash muammolari va barqarorlikni nazorat qilish uchun kerak. Tekshirish: Kodda prometheus_client kabi kutubxonalar chaqirilgani yoki st.metric (Streamlitda oddiy metric) funksiyasi ishlatilgani ko‘rilishi mumkin.
Masshtablilik (Scalability) va barqarorlik
[64] Gorizontal kengaytirish: Loyihada bir nechta instans yoki tugunlar ustida ishlashni qo‘llab-quvvatlovchi funksiyalar bo‘lsa, tekshiring. Masalan, Flask/Streamlit multi-threading yoki Sun’iy intellekt modellarini batch rejimida ishlatish. Nima uchun: Foydalanuvchi bazasi oshganda tizimni kengaytirish imkonini beradi. Tekshirish: Kodda st.experimental_singleton yoki st.cache decoratorlarining to‘g‘ri ishlatilishini va klaster ustida ishlash imkoniyatini tahlil qilish.
[65] Vertikal resurs ajratish: Kode ko‘p resurs talab qilganda avtomatik kengayish (OS shuilimi)? Masalan, Docker konteynerida CPU va RAM limitlari belgilangani tekshiring. Nima uchun: Ishlash jarayonida kutilmagan o‘rin ajratish masalalarining oldini olish uchun. Tekshirish: Dockerfile yoki Kubernetes manifestda resurs limiti (limits) ko‘rsatib o‘tilganligini aniqlash.
[66] Uchinchi tomon xizmati bog‘lanishi: Tashqi API yoki xizmat (masalan, Telegram bot, Stripe) bilan ishlashda aslida yuk ko‘tarish bilan bog‘liqlik bor-yo‘qligini tekshiring. Nima uchun: Agar cheklangan API so‘rovlar bo‘lsa, to‘g‘ri polling mexanizmi yoki fallback bo‘lishi kerak. Tekshirish: Kodda tashqi so‘rovlar (requests, aiohttp) boʻlib, ularning tez-tez ishlatilishi aniqlanib, qayta qo‘llash uchun metodlar mavjudligini tekshirish.
[67] Muxtasar imkoniyat: Agar servis bir necha qismlarga bo‘lingan bo‘lsa (Microservices), ular orasidagi bog‘liqliklarni tekshiring. Nima uchun: Mustaqil modulni qayta ishlash qulayligi ta’minlanadi. Tekshirish: Agar kodda mikroservis arxitekturasi bo‘lsa, har bir xizmatning alohida resursi va konfiguratsiyasi bor-yo‘qligini ko‘rib chiqing.
Texnik qo‘llab-quvvatlash (Maintainability)
[68] DRY tamoyiliga rioya: Kodda takrorlangan bloklar yoki deyarli bir xil funksiyalarni toping. Pythonda, bunday hollarda kodni umumiy funksiya yoki modulga ajratish kerak. Nima uchun: Dublikat kod o‘zgartirishda xatolarga olib keladi va qo‘llab-quvvatlashni murakkablashtiradi. Tekshirish: Linterlarda duplicated code (masalan, SonarQube) yoki flake8-duplicates plugin bilan tekshirish.
[69] Qisqa funksiyalar: Funksiya va sinflar juda uzun bo‘lmasligi kerak (masalan, 200+ qator), ular bitta mas’uliyatga ega bo‘lishi lozim (SRP). Nima uchun: Katta funksiyalarni tushunish va test qilish qiyin. Tekshirish: Kod bazasini tahlil qilib, uzun kod bloklari aniqlanganda, ularni bo‘limlarga ajratishni rejalashtirish.
[70] Versiya nazorati: Loyihada git yoki boshqa VCSdagi commit xabarlari standartlariga amal qilinishi kerak (masalan, Convential Commits). Nima uchun: Aniqlik va tarqatilgan hamkorlikni yaxshilaydi. Tekshirish: Git tarixini (git log) ko‘rib chiqing va commitlar mazmuni, formatining mosligini baholang.
[71] Kod sharhlari va tavsiyalar: Murakkab yoki noaniq qism yaqinida ishlovchi dasturchi uchun sharh va “TODO” eslatmalar qo‘yilganmi tekshiring. Nima uchun: Navbatdagi dasturchilar (yoki o‘zingiz) uchun yordamchi bo‘ladi. Tekshirish: Kodda # TODO yoki izohlash (#) ni qidirib, kerakli bo‘lgan joylarda izohlar mavjud ekanligiga ishonch hosil qiling.
[72] Qayta ishlash qulayligi: Kode oson tarqatilishi uchun bo‘limlar modul, paket sifatida ajratilganmi? Masalan, pip install -e . bilan o‘rnatiladigan loyihalarning setup.py yoki pyproject.toml fayli bor-yo‘qligini tekshirish. Nima uchun: Yaxshi paketlash mumkin bo‘lgan kod parchalari o‘zgartirishni soddalashtiradi. Tekshirish: setup.py yoki pyproject.toml tarkibini ko‘rib, packages va entry_points ko‘rsatilganini tekshirish.
Ma’lumot maxfiyligi (Data Privacy)
[73] Foydalanuvchi ma’lumotlarini himoya: Agar foydalanuvchi ma’lumotlari (ism, email, identifikator) saqlansa yoki qayta ishlansa, ularni shifrlangan holda saqlash kerak. Masalan, bcrypt yoki hashlib.sha256 singari xavfsiz xesh funksiyalar ishlatilganini tekshiring. Nima uchun: Maxfiy ma’lumot tarqalishi oldini olish uchun. Tekshirish: Parollar hashlib yoki bcrypt yordamida xeshlanganini tekshirish; agar shifrlash bo‘lmasa, darhol qo‘shishni rejalashtirish.
[74] GDPR/CCPA muvofiqligi: Agar loyihada foydalanuvchi ma’lumotlari Evropa Ittifoqi fuqarolari haqidagi ma’lumotlarni qayta ishlansa, maxfiylik talablari bajarilganligini tekshiring. Nima uchun: Qonunchilik bo‘yicha muomala. Tekshirish: Kode ichida “GDPR”, “consent” kabi so‘zlar borligi, foydalanuvchi roziligi so‘ralgani va ma’lumotlarni o‘chirib tashlash funksiya/so‘rovlarining mavjudligini tekshirish.
[75] Ma’lumotlarni minimallashtirish: Foydasiz ma’lumotlarni yig‘maslik va saqlamaslik. Kutilmagan maydonlardagi (shaxsiy) ma’lumotlarni ko‘rsatish yoki saqlash ustida tekshiruv o‘tkazing. Nima uchun: Keraksiz ma’lumot yig‘ish maxfiylik xavfini oshiradi. Tekshirish: Input va output formatlarini ko‘rib chiqib, faqat kerakli maydonlar borligiga ishonch hosil qilish.
[76] Shaxsiy ma’lumotlarni ro‘yxatdan o‘tkazish: Agar foydalanuvchi shaxsiy ma’lumotni kiritadigan bo‘lsa, ular xavfsiz saqlanishi va o‘chirilish huquqi ta’minlangan bo‘lishi kerak. Nima uchun: Data-suvlardan himoya qilish qonuniy talablardan biridir. Tekshirish: Boshqaruv panelida ma’lumotlarni o‘chirish / eksport qilish imkoniyatlari yaratilganini yoki shaxsiy ma’lumotlar SQL ma’lumotlar bazasida gazlangan arxividan o‘chirib tashlanishini aniqlash.
Joylashtirish (Deployment)
[77] Ishga tushirish bosqichi: Dastur qanday muhitda (server, konteyner, bulut) ishga tushirilishi yozilganmi tekshiring. Masalan, dokumentatsiyada streamlit run app.py yoki Docker konteynerda CMD ["streamlit", "run", "app.py"]. Nima uchun: Aniqlik jarayon boshqaruvini va nosozlik holatda tez javob berishni ta’minlaydi. Tekshirish: Dockerfile yoki Bulut konfiguratsiyasida kirish nuqtasi (ENTRYPOINT) va kerakli muhit o‘zgaruvchilari ko‘rsatilganini tekshiring.
[78] Muhit sozlamalari: Ishlash muhiti (dev, test, prod) o‘rtasida farq qilib, konfiguratsiyani avtomatik tanlaydigan mexanizm bor-yo‘qligini tekshiring. Nima uchun: Har xil muhit uchun mos konfiqsiz ishlash xatolarga olib kelishi mumkin. Tekshirish: config.environment kabi atributlardan foydalanilgani yoki if environment == 'prod' bo‘limi borligini aniqlash.
[79] Ishga tushirish xatolarini kuzatish: Joylashtirishda yuzaga kelishi mumkin bo‘lgan xatolarni (ContainerOutOfMemory, CrashLoopBackoff) aniqlash uchun tekshirish yarating. Nima uchun: Orqa tomonda tizim monitoringi muhim. Tekshirish: Docker konteynerda test muhitida resurs limitlarini pasaytirib, sabablari haqida loglarni oling yoki kutilmagan holatda avtomatik re-start sozlanganiga e’tibor bering.
Keng tarqalgan xatolar va antipatternlar
[80] Null-pointer / undefined referensiya:

Python: Agar obyekt bo‘lmasa .attribute chaqirilsa AttributeError keladi. To‘g‘ri qaror: tekshirish (if x is not None:).
python
Копировать
# Noto‘g‘ri
value = obj.field  # obj None bo‘lsa xato
# To‘g‘ri
value = obj.field if obj is not None else default
Java: NullPointerException oldini olish uchun metod parametrlariga tekshiruv qo‘yish yoki Optional sinfidan foydalanish:
java
Копировать
if (obj != null) {
    int value = obj.getField();
}
JavaScript/TypeScript: undefined/null tekshiruvi, masalan: const value = obj?.field || defaultValue; yoki if (obj) { ... }.
[81] SQL injeksiya (parametrsiz so‘rov):

Python:
python
Копировать
# Noto‘g‘ri:
cursor.execute("SELECT * FROM users WHERE id = %s" % user_input)
# To‘g‘ri (parametrli):
cursor.execute("SELECT * FROM users WHERE id = ?", (user_input,))
Java:
java
Копировать
// Noto‘g‘ri
Statement stmt = conn.createStatement();
stmt.executeQuery("SELECT * FROM users WHERE id = " + userId);
// To‘g‘ri (PreparedStatement)
PreparedStatement ps = conn.prepareStatement("SELECT * FROM users WHERE id = ?");
ps.setInt(1, userId);
JavaScript:
js
Копировать
// Noto‘g‘ri (string birlashtirish bilan)
db.query(`SELECT * FROM users WHERE id = ${userInput}`);
// To‘g‘ri (parameter binding)
db.query("SELECT * FROM users WHERE id = $1", [userInput]);
[82] XSS (Cross-Site Scripting):

Python (Flask/Django): Shablonlarda matnni avtomatik qayta ishlatish yoki escape() foydalanish:
python
Копировать
# Flask Jinja2: avtomatik escaping kerakli
{{ user_input }}
Java: JSP/Thymeleaf’da th:utext dan ko‘ra th:text ishlatib, yoki so‘zlashgan belgilarni StringEscapeUtils.escapeHtml4(input) bilan tozalash.
JS: React’da JSX avtomatik escaping qiladi, lekin dangerouslySetInnerHTML bilan ishlashda ehtiyot bo‘ling; Node’da express bilan helmet paketini qo‘shish tavsiya etiladi.
[83] Exceptions umumiy tutish:

Python:
python
Копировать
# Noto‘g‘ri:
except Exception:
    print("Xato bo'ldi")
# To‘g‘ri:
except ValueError as e:
    print(f"Qiymat xatosi: {e}")
Java:
java
Копировать
// Noto‘g‘ri:
try { ... } catch (Exception e) { ... }
// To‘g‘ri:
try { ... } catch (NumberFormatException e) { ... }
JavaScript:
js
Копировать
// Noto‘g‘ri:
try { ... } catch (e) { console.error("Xato"); }
// To‘g‘ri (specific):
try { JSON.parse(str); } catch (e) { console.error("JSON xatosi"); }
[84] Murakkab branch va chekka holatlarga e’tiborsizlik:

Python: if a and b or c kabi murakkab ifoda qiyin o‘qilsa, bo‘lish:
python
Копировать
# Yaxshi:
if (a and b) or c:
    ...
Java: Uzun if-else bloklari o‘rniga switch-case yoki Map struksturalaridan foydalanish.
JS: then().catch().then() chain’ini async/await bilan almashtirish aniqroq bo‘ladi.
[85] Ikkilashuv va mutable global:

Python:
python
Копировать
# Noto‘g‘ri:
global counter
counter += 1
# To‘g‘ri:
def increment(counter):
    return counter + 1
Java: public static o‘zgaruvchilarga ehtiyot bo‘ling, synchronized kerak bo‘lsa, yoki AtomicInteger.
JS: Global o‘zgaruvchi o‘rniga let/const va funksiya parametrlarini ishlating.
Kod tuzatish va namunali parchalar
Quyidagi kod qismlari keng tarqalgan muammolarni tuzatish uchun namunadir. Kontekstga mos ravishda joylashtiring:

Import tozalash:

diff
Копировать
- import streamlit as st
- import streamlit as st  # ikkinchi marta
+ import streamlit as st
Wildcard import tuzatish:

diff
Копировать
- from module import *
+ from module import allowed_name1, allowed_name2
Exception tuzatish:

diff
Копировать
- try:
-     result = int(user_input)
- except Exception:
-     result = 0
+ try:
+     result = int(user_input)
+ except ValueError:
+     result = 0
SQL parametrli so‘rovga o‘tkazish:

diff
Копировать
- query = "SELECT * FROM students WHERE id = " + str(student_id)
- cursor.execute(query)
+ query = "SELECT * FROM students WHERE id = ?"
+ cursor.execute(query, (student_id,))
Malumot sanitizatsiyasi:

diff
Копировать
- unsafe_input = user_data.replace(";", "")
+ import re
+ safe_input = re.sub(r'[;\x00]', '', user_data)
Loggingni sozlash:

diff
Копировать
+ import logging
+ logging.basicConfig(level=logging.INFO,
+     format='%(asctime)s %(levelname)s:%(name)s: %(message)s')
  logger = logging.getLogger(__name__)
CVS xatoliklarining oldini olish:

diff
Копировать
- if sys.platform == 'darwin':
-     multiprocessing.set_start_method('fork')
- elif sys.platform == 'win32':
-     multiprocessing.set_start_method('spawn')
+ if __name__ == "__main__":
+     multiprocessing.set_start_method('spawn' if sys.platform == 'win32' else 'fork')
+     main()
Testlar uchun namunaviy kod va sinov kaseslari
[86] Python (pytest) unit test:

python
Копировать
import pytest
from app_module import sanitize_input, safe_filepath

def test_sanitize_input_removes_forbidden_chars():
    assert sanitize_input("Hello;Drop") == "HelloDrop"

def test_safe_filepath_creates_directory(tmp_path):
    safe_name = safe_filepath("../data/file.txt", base_dir=str(tmp_path))
    assert tmp_path.joinpath(safe_name).exists()
[87] JavaScript (Jest) test:

javascript
Копировать
// file: sanitize.test.js
const { sanitizeInput } = require('./utils');

test('sanitizes input by removing ; and null', () => {
  expect(sanitizeInput("Hello;World\x00")).toBe("HelloWorld");
});
[88] Java (JUnit) test:

java
Копировать
import static org.junit.Assert.*;
import org.junit.Test;

public class UtilsTest {
    @Test
    public void testSafeFilename() {
        assertEquals("reports_file.txt", Utils.safeFilename("../reports/file.txt"));
    }
}
[89] Integratsiya/E2E test: Avval aytilgan Playwright yoki Selenium namunasi: foydalanuvchi oqimi sinovini yozing.

Xavfsizlikni mustahkamlash va skanerlash vositalari
[90] Linter va SAST: Kodni tekshirish uchun Bandit (Python), Semgrep yoki SonarQube kabi SAST vositalarini qo‘shing. Masalan: pip install bandit && bandit -r .. Nima uchun: Automatik skanerlash ma’lum xatolarni ushlab qoladi. Tekshirish: bandit hisobotida HIGH yoki MEDIUM xavfsizlik muammolari yo‘qmi tekshirish.
[91] Statik lintlar: Python uchun Flake8, Pylint; JavaScript uchun ESLint (TS uchun TypeScript ESLint); Java uchun Checkstyle, PMD, SpotBugs. Har birini pre-commit yoki CI’ga integratsiya qiling.
[92] Bog‘liqlik skanerlash: Python’da pip-audit, JS’da npm audit, Java’da OWASP Dependency-Check. Shuningdek, Trivy kabi universal Docker skanerlarini ham ko‘rib chiqing. Nima uchun: Oshirilgan xavfsizlik kafolati. Tekshirish: Loyihani qurishda npm audit va pip-audit ning natijasini CI jurnali orqali tekshirish.
[93] Credential scanning: Kodda parol yoki API kalitlar bor-yo‘qligini qidirish uchun git-secrets yoki detect-secrets vositalaridan foydalaning. Nima uchun: Xavfsizlik buzilishi oldini olish uchun. Tekshirish: Misol: git-secrets --scan.
[94] CI/CD xavfsizlik tekshiruvlari: GitHub Actions’ga CodeQL yoki GitLab SAST qo‘shing, container xavfsizligi uchun Trivy ishga tushiring. Nima uchun: Kiritilgan teshiklarni tezda topish va tuzatishga yordam beradi. Tekshirish: CI pipeline hisobotlarida SAST/DAST natijalarini tekshirish.
Amalga oshirish bo‘yicha reja (Prioritet va baho)
Quyida har bir toifaga oid asosiy vazifalar, taxminiy mehnat va xavf darajasi keltirilgan. Yuqori ustuvorlikdagilar avval bajarilishi lozim.

№	Vazifa	Taxminiy vaqt (soat)	Xavfdar darajasi (High/Med/Low)
1	Linter va formatlash (PEP8, ESLint) joriy etish	4	Past
2	Import va kod takrorlarini birlashtirish	3	O‘rta
3	Xavfsizlik tekshiruvi (OWASP tavsiyalari asosida)	6	Yuqori
4	Unit va integratsiya testlari yozish	12	O‘rta
5	CI/CD pipeline sozlash (lint, test, yengillash)	8	O‘rta
6	Exception va xatolarni yaxshilash (maxfiy ma’lumotsiz)	4	O‘rta
7	Loglash va monitoringni kuchaytirish	4	Past
8	Bog‘liqliklar va SAST tekshiruvi (pip-audit, Dependency-Check)	5	Yuqori
9	UI optimizatsiyasi va i18n (tarjima, rang kontrasti)	6	Past
10	Hujjatlar (README, docstring, reliz notalari) yangilash	3	Past

Vositalar solishtirmasi va konfiguratsiya
Linterlar: Quyidagi jadvalda mashhur lint tekshiruvchi vositalar taqqoslanadi:

Til	Vosita (Lint)	Afzallik	Konfiguratsiya (suggested)
Python	Pylint	Batafsil kod statistikasi va xatolarni ko‘rsatadi	.pylintrc bilan qoidalarni sozlash
Python	Flake8	Kengaytirilgan plaginlar bilan (nemesis)	setup.cfg yoki tox.ini da sozlash
Python	mypy (typing)	Type hintlarga e’tibor, o‘zgaruvchilarni tekshiradi	mypy.ini da strict rejimi
JS/TS	ESLint	Keng qo‘llaniluvchi, konfiguratsiyasi boshqacha	.eslintrc.json (Airbnb, Standard)
Java	Checkstyle	Kod stili tekshiradi (naming, indent va h.)	checkstyle.xml da qoidalarni sozlash
Java	PMD	Kod sifati va optimizatsiya bo‘yicha tahlil	ruleset.xml fayl

Test ramkalari:

Til	Test ramkasi	Foydalanish misoli	Konfiguratsiya-tuzilish
Python	pytest	Intuitiv assert, parametrik testlar	pytest.ini (marker va parametrlar)
Python	unittest	Standart kutubxona, sinov klasslari	Standart -v va test suite shakli
Java	JUnit 5	Annotatsiyalar asosida test yozish	pom.xml yoki build.gradle da sozlash
JS	Jest	Sinov yozish oson (mock/spylar)	jest.config.js (transpiler qo‘llab-quvvatlash)
JS	Mocha + Chai	Moslashuvchan, assertion kutubxonasi	mocha.opts va package.json skriptlar

CI/CD provayderlari:

Provayder	Afzalliklar	Konfiguratsiya/Integratsiya
GitHub Actions	O‘zaro integratsiya, ko‘plab marketplace aksiyalar	.github/workflows/ci.yml (lint, test, build)
GitLab CI/CD	Docker lar, keng sozlamalar, bevosita repo ichida	.gitlab-ci.yml (stage: lint, test, deploy)
Jenkins	Moslashuvchan, keng plugin ekotizimi	Jenkinsfile (pipeline DSL, agent belgilash)
Travis CI	Ochiq manbalar uchun bepul, oddiy konfiguratsiya	.travis.yml (til, dastur muhitini sozlash)
CircleCI	Tez bulut versiya, Docker qo‘llab-quvvatlash	.circleci/config.yml (jobs va workflows)

Har bir qurilmada test va lint bosqichlarini qo‘shish taklif qilinadi. Masalan, Python loyihasi uchun:

yaml
Копировать
# GitHub Actions example snippet
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with: { python-version: '3.x' }
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run linters
        run: flake8 . && mypy .
      - name: Run tests
        run: pytest --maxfail=1 --disable-warnings -v
Yuqoridagi misolda linter va test bosqichlari integratsiya qilingan. Xuddi shunday JS/Java loyihalarida yarn lint && yarn test yoki mvn test kombinatsiyasi ishlatiladi.

Diagrammalar:

mermaid
Копировать
flowchart TB
    code[{"Kod bazasi"}] --> lint["Lint (Flake8, ESLint)"]
    code --> test["Unit Testlar"]
    lint --> ci["CI/CD pipeline"]
    test --> ci
    ci --> build["Build va Deploy"]
    build --> prod["Prod muhit"]
mermaid
Копировать
flowchart LR
    user[Foydalanuvchi] -->|So‘rov yuboradi| ui[Streamlit UI]
    ui --> logic[Biznes mantiq (model, statistika)]
    logic --> db[(Ma’lumotlar bazasi)]
    logic --> cache[Kesh/Fayllar]
    logic --> modelStat[Model va tahlil]
    modelStat --> logic
    db --> logic
Yuqoridagi jarayon diagramlari kod ko‘rigi, avtomatlashtirilgan tizim va arxitekturaning umumiy ko‘rinishini aks ettiradi.

Manbalar: Python kodlash standartlari bo‘yicha PEP8 tavsiyalaridan, OWASP xavfsizlik cheklistlaridan va GitHub Actions qo‘llanmasidan keng miqyosda foydalanildi. Ustuvor fokus – kod sifati va xavfsizlik – uchun Greptile’dagi kod ko‘rigi cheklovlari (L1-L3 qatlamlari) yordami katta. Bu tavsiyalar kodni mustahkamlash va texnik qarorlarni asoslashda asos bo‘lib hizmat qiladi.

