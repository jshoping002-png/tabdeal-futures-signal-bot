# قرارداد PIT و Replay

## هدف

این سند قواعد جلوگیری از look-ahead bias و تضمین قابلیت بازپخش تصمیم‌ها را مشخص می‌کند. این قرارداد فقط برای تحلیل، اعتبارسنجی، persistence و audit است و هیچ قابلیت سفارش‌گذاری یا اجرای معامله ایجاد نمی‌کند.

## تعریف زمان‌ها

هر داده باید تا حد امکان این زمان‌ها را از هم جدا نگه دارد:

- `observed_at`: زمان مشاهده یا تولید داده در منبع؛
- `published_at`: زمان انتشار رسمی، برای خبر و دادهٔ اقتصادی؛
- `received_at`: زمان دریافت توسط سیستم؛
- `effective_at`: زمانی که داده از نظر معنایی اثرگذار است؛
- `decision_at`: زمان تولید تصمیم؛
- `available_at`: زمانی که داده واقعاً برای pipeline قابل استفاده شده است.

نباید `received_at` یا زمان اجرای replay به‌جای زمان واقعی در دسترس‌بودن داده استفاده شود.

## قانون اصلی Point-in-Time

در زمان `decision_at` فقط داده‌ای مجاز است که `available_at <= decision_at` داشته باشد.

داده‌ای که بعداً اصلاح، منتشر یا دریافت شده است نباید در بازسازی تصمیم تاریخی قبلی وارد شود؛ حتی اگر مقدار نهایی آن از نظر تاریخی دقیق‌تر باشد.

## نسخه و revision

- هر snapshot باید `schema_version` داشته باشد.
- داده‌های اقتصادی و خبری که revision می‌شوند باید revision یا version مستقل داشته باشند.
- تغییر در payload خام نباید snapshot قبلی را بی‌صدا overwrite کند.
- برای بازسازی دقیق، reference نسخهٔ خام و normalized باید حفظ شود.

## کندل و سری زمانی

- کندل بسته‌نشده باید با flag صریح مشخص شود.
- کندل بسته‌نشده نباید بدون policy صریح در featureهای نهایی استفاده شود.
- gap، duplicate، out-of-order و timestamp غیرقابل‌اعتماد باید قابل تشخیص و ثبت باشند.
- interval و timezone باید بخشی از metadata سری زمانی باشند.

## Replay requirements

Replay باید بتواند با ورودی‌های ثبت‌شده، موارد زیر را بازسازی کند:

1. snapshotهای ورودی؛
2. وضعیت کیفیت و freshness؛
3. featureها و contextهای مشتق‌شده؛
4. policyها و نسخهٔ schema؛
5. تصمیم نهایی؛
6. شناسهٔ idempotency و event؛
7. علت warning یا `BLOCKED` در صورت وجود.

Replay نباید به provider زنده وابسته باشد؛ در صورت نیاز به دادهٔ بیرونی، باید reference و رفتار fallback صریح باشد.

## Determinism

برای payload و configuration یکسان، نتیجهٔ normalized، feature و تصمیم باید deterministic باشد. هر وابستگی به زمان جاری، ترتیب نامشخص داده‌ها، random seed یا وضعیت mutable باید حذف یا versioned شود.

## Failure policy

- نبود دادهٔ لازم باید صریحاً به `UNAVAILABLE` یا وضعیت قراردادی مناسب تبدیل شود.
- دادهٔ stale یا ناقص باید warning، skip یا `BLOCKED` ایجاد کند؛ policy باید قابل مشاهده باشد.
- مقدار ساختگی، default پنهان یا forward-fill بدون ثبت provenance مجاز نیست.
- خطاهای provider نباید به‌عنوان سیگنال معتبر تفسیر شوند.

## Audit chain

زنجیرهٔ قابل ردیابی باید حداقل شامل این مسیر باشد:

`raw reference -> normalized snapshot -> quality result -> features/context -> decision -> persisted event`

برای هر مرحله باید version، timestamp و provenance تا حد امکان قابل بازیابی باشد.

## معیار پذیرش

- هیچ دادهٔ آینده‌ای وارد تصمیم تاریخی نشود؛
- revisionها قابل تفکیک و بازسازی باشند؛
- replay بدون provider زنده قابل اجرا باشد؛
- خروجی با ورودی یکسان deterministic باشد؛
- وضعیت کیفیت و علت `BLOCKED` قابل audit باشد؛
- هیچ مسیر replay یا data pipeline به order execution یا trading endpoint متصل نباشد.
