# نقشهٔ راه منابع اطلاعاتی تحلیل

## هدف

این سند برنامهٔ مرحله‌ای برای اضافه‌کردن منابع اطلاعاتی موردنیاز تحلیل سیگنال را مشخص می‌کند. پروژه فقط مجاز به **دریافت داده، تحلیل، اعتبارسنجی، ارزیابی ریسک، persistence و اعلان سیگنال** است و نباید هیچ‌گونه اجرای سفارش، معاملهٔ خودکار یا endpoint معاملاتی اضافه کند.

## وضعیت فعلی

- داده‌های قیمتی و OHLCV در سطح fixture و ورودی‌های تحلیل/تست استفاده می‌شوند.
- مؤلفه‌های تکنیکال مانند RSI، EMA، MACD و Volume در سطح تحلیل یا قرارداد پیام مطرح هستند.
- کنترل‌های PIT، جلوگیری از look-ahead و تصمیم‌های `SIGNAL`/`BLOCKED` تعریف شده‌اند.
- اتصال زنده به Binance، Bybit، TradingView، منابع اقتصاد کلان، خبرگزاری‌ها یا شاخص‌های کلان هنوز پیاده‌سازی و تأیید نشده است.

## اصول مشترک تمام فازها

1. هر منبع باید adapter مستقل، قرارداد typed، timestamp و metadata کیفیت داشته باشد.
2. دادهٔ خام باید از دادهٔ نرمال‌شده و featureهای تحلیلی جدا باشد.
3. هر رکورد باید freshness، latency، source، symbol/instrument و زمان دریافت را مشخص کند.
4. دادهٔ آینده‌نگر، اصلاح‌شده یا منتشرشده پس از زمان تصمیم نباید وارد تحلیل تاریخی شود.
5. خرابی، تأخیر، gap، تناقض یا stale بودن منبع باید قابل تشخیص و قابل audit باشد.
6. منابع Context نباید بدون قرارداد صریح به شرط مستقیم LONG/SHORT تبدیل شوند.
7. هیچ adapter یا pipeline نباید قابلیت ارسال سفارش یا اجرای معامله داشته باشد.

## فاز ۰ — قرارداد و زیرساخت مشترک

### خروجی‌ها

- تعریف `DataSource`, `DataSnapshot`, `DataQuality` و `SourceHealth`.
- قرارداد واحد برای `timestamp`, `observed_at`, `published_at`, `received_at` و timezone.
- قرارداد خطا، retry، timeout، rate-limit و stale-data.
- ثبت source provenance و نسخهٔ schema.
- تست‌های fixture، replay، determinism و no-lookahead.
- تعریف policy برای fallback و زمانی که تصمیم باید `BLOCKED` شود.

### معیار پذیرش

- تمام منابع بعدی از یک قرارداد مشترک استفاده کنند.
- هیچ منبع نامعتبر یا stale بدون علامت کیفیت وارد تصمیم نشود.

## فاز ۱ — بازار و دادهٔ پایهٔ صرافی‌ها

### دامنه

- Binance Futures به‌عنوان provider اولیه.
- Bybit Futures به‌عنوان provider دوم برای مقایسه و fallback.
- در صورت نیاز، Spot به‌عنوان منبع زمینه‌ای؛ نه الزام اولیه.
- OHLCV، قیمت، volume، candle close و timestamp.

### کارها

- ساخت adapterهای فقط خواندنی برای Binance و Bybit.
- نرمال‌سازی symbol، contract، interval و exchange.
- کنترل ترتیب کندل‌ها، duplicate، gap، timestamp و clock skew.
- ذخیرهٔ snapshot خام و نرمال‌شده برای replay.
- مقایسهٔ اختلاف قیمت/کندل بین providerها.

### معیار پذیرش

- دادهٔ یکسان از دو provider خروجی deterministic بدهد.
- خرابی یک provider باعث ورود دادهٔ بی‌کیفیت به تصمیم نشود.
- هیچ endpoint معاملاتی در adapterها وجود نداشته باشد.

## فاز ۲ — تحلیل تکنیکال و چندتایم‌فریمی

### دامنه

- RSI، EMA، MACD، Volume.
- روند، market structure، حمایت/مقاومت.
- تایم‌فریم‌های کوتاه‌مدت، میان‌مدت و بلندمدت.

### کارها

- تعریف قرارداد featureها و windowهای موردنیاز.
- مشخص‌کردن حداقل تعداد کندل و رفتار warm-up.
- جلوگیری از استفاده از کندل بسته‌نشده مگر با قرارداد صریح.
- تعریف منطق تأیید چندتایم‌فریمی.
- ثبت feature provenance و input snapshot.

### معیار پذیرش

- featureها با replay تاریخی قابل بازتولید باشند.
- تغییر دادهٔ آینده روی تصمیم گذشته اثر نگذارد.
- خروجی تحلیل صرفاً signal candidate یا `BLOCKED` باشد.

## فاز ۳ — داده‌های مشتقات و microstructure

### دامنه

- Order Book و imbalance.
- Open Interest.
- Funding Rate.
- Liquidation data.

### ترتیب پیشنهادی

1. Order Book snapshot و imbalance.
2. Open Interest.
3. Funding Rate.
4. Liquidations و aggregation آن‌ها.

### کارها

- تعریف تفاوت snapshot، stream و aggregate.
- ثبت عمق order book، زمان snapshot و freshness.
- تعریف قرارداد محاسبهٔ imbalance و محدودیت‌های آن.
- مشخص‌کردن اینکه هر feature فقط تأییدکننده است یا می‌تواند در risk gate اثر بگذارد.
- کنترل اختلاف exchangeها و دادهٔ ناقص.

### معیار پذیرش

- featureهای مشتقات بدون دادهٔ معتبر به‌صورت `N/A` یا وضعیت نامعتبر مشخص شوند.
- هیچ feature به‌تنهایی مجوز معامله یا اجرای سفارش صادر نکند.

## فاز ۴ — TradingView و منابع تجمیعی

### تصمیم معماری پیش از پیاده‌سازی

باید مشخص شود TradingView:

- منبع مستقل داده است؛ یا
- فقط ابزار مشاهده، charting و تأیید انسانی است.

### کارها

- ثبت تصمیم معماری و محدودیت حقوقی/فنی استفاده از داده.
- در صورت انتخاب provider رسمی و مجاز، ساخت adapter فقط خواندنی.
- جلوگیری از دو بار شماری دادهٔ TradingView و صرافی‌ها.
- تعریف provenance جداگانه برای دادهٔ تجمیعی.

### معیار پذیرش

- نقش TradingView در تصمیم‌گیری صریح و مستند باشد.
- بدون قرارداد مستقل، TradingView وارد منطق اصلی سیگنال نشود.

## فاز ۵ — اقتصاد کلان رسمی

### دامنهٔ اولیه

- نرخ بهره و تصمیمات بانک مرکزی.
- CPI، PCE.
- NFP، Payrolls، نرخ بیکاری و سایر داده‌های اشتغال.
- GDP، PMI، Retail Sales.
- FOMC، بیانیه‌ها و سخنرانی مقامات بانک مرکزی.
- منابع رسمی مانند Federal Reserve، BLS و BEA و معادل رسمی آن‌ها برای سایر کشورها.

### کارها

- تعریف تقویم اقتصادی با `published_at` و `effective_at`.
- ذخیرهٔ مقدار اولیه، revision و زمان انتشار.
- تفکیک forecast، previous، actual و revised value.
- تعریف event importance و تأثیر احتمالی بر ریسک.
- ساخت macro context مستقل از signal direction.

### معیار پذیرش

- replay از وضعیت اطلاعاتی قابل‌دسترسی در زمان تصمیم پشتیبانی شود.
- revisionهای بعدی داده، تصمیم تاریخی را تغییر ندهند.
- رویدادهای پرریسک بتوانند از طریق risk gate باعث `BLOCKED` شوند، نه اینکه مستقیماً LONG/SHORT بسازند.

## فاز ۶ — اخبار و رویدادهای ریسک

### دامنه

- اخبار اقتصاد کلان و بانک‌های مرکزی.
- بحران‌های مالی و ژئوپلیتیک.
- اخبار ETF، مقررات و صنعت کریپتو.
- اخبار مهم صرافی‌ها و مؤسسات مالی.

### کارها

- تعریف provider و سطح اعتماد منبع.
- canonical URL، زمان انتشار، زمان دریافت و شناسهٔ خبر.
- حذف duplicate و تشخیص خبرهای بازنشرشده.
- طبقه‌بندی موضوع، شدت، دارایی‌های مرتبط و افق زمانی.
- تعریف human-review یا rule-based validation برای خبرهای حساس.

### معیار پذیرش

- خبر بدون provenance معتبر وارد context نشود.
- خبر به‌صورت مستقیم جهت معامله تولید نکند.
- در صورت ابهام یا تضاد منابع، risk warning یا `BLOCKED` تولید شود.

## فاز ۷ — شاخص‌های کلان ریسک و بازار

### دامنه

- DXY.
- VIX.
- بازده اوراق خزانهٔ آمریکا.
- شاخص‌های اصلی سهام.
- Gold.
- Liquidity و Financial Conditions.

### کارها

- تعریف این داده‌ها به‌عنوان `MarketContext` یا `RiskContext`.
- تعیین cadence، freshness و session/calendar هر شاخص.
- تعریف mapping شفاف از مقدار شاخص به risk warning، بدون تبدیل خودکار به LONG/SHORT.
- تست اثر نبودن یا stale بودن شاخص‌ها.

### معیار پذیرش

- شاخص‌ها فقط در context و risk evaluation مصرف شوند.
- هیچ آستانه‌ای بدون قرارداد، backtest و تأیید دامنه وارد تصمیم نشود.

## فاز ۸ — یکپارچه‌سازی، ارزیابی و آمادگی عملیاتی

### کارها

- data registry و source health dashboard.
- metrics برای freshness، latency، error rate، gap و fallback.
- audit trail برای raw input، normalized data، features و decision.
- replay کامل از snapshotهای ذخیره‌شده.
- تست concurrency، load، rate-limit و recovery.
- backup/restore و corruption recovery.
- مستندسازی runbook و incident response.
- بررسی امنیت credentialها و حداقل دسترسی.
- تکمیل dependency locking و reproducible installation.

### معیار پذیرش

- مسیر کامل از منبع تا تصمیم قابل audit و replay باشد.
- خرابی یا تضاد منابع به تصمیم کنترل‌شده منجر شود.
- production readiness فقط پس از شواهد واقعی deployment، recovery، observability و CI تأیید شود.

## ترتیب اولویت اجرایی

1. فاز ۰: قرارداد مشترک داده و کیفیت.
2. فاز ۱: Binance و Bybit برای OHLCV و قیمت.
3. فاز ۲: تکمیل featureهای تکنیکال و چندتایم‌فریمی.
4. فاز ۳: Order Book، Open Interest، Funding و Liquidations.
5. فاز ۴: تصمیم مستقل دربارهٔ TradingView.
6. فاز ۵: اقتصاد کلان رسمی.
7. فاز ۶: اخبار و رویدادهای ریسک.
8. فاز ۷: شاخص‌های کلان بازار.
9. فاز ۸: یکپارچه‌سازی و operational readiness.

## وضعیت تکمیل

این roadmap یک برنامهٔ طراحی و اجراست؛ وجود نام یک منبع در این سند به معنی اتصال، صحت‌سنجی یا آمادگی production آن منبع نیست.
