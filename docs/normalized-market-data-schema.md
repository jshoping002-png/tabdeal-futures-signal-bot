# Normalized Market Data Schema

## هدف

تعریف شکل مشترک دادهٔ بازار برای adapterهای read-only، به‌گونه‌ای که منطق سیگنال به منبع داده وابسته نباشد.

## اصول

- داده فقط از مسیرهای عمومی و read-only دریافت می‌شود.
- هیچ فیلد، متد یا وابستگی برای سفارش‌گذاری، معامله، موجودی یا موقعیت معاملاتی وجود ندارد.
- همهٔ زمان‌ها timezone-aware و ترجیحاً UTC هستند.
- `available_at` زمان قابل‌دسترس شدن داده و `received_at` زمان دریافت آن توسط سیستم است.
- برای رعایت PIT، مصرف‌کننده نباید رکوردی با `available_at > as_of` را وارد محاسبه کند.
- مقادیر عددی باید قابل تبدیل و اعتبارسنجی باشند؛ قیمت و حجم منفی مجاز نیستند.

## شکل پیشنهادی کندل

```text
Candle:
  instrument: str
  interval: str
  open_time: datetime
  close_time: datetime
  open: Decimal
  high: Decimal
  low: Decimal
  close: Decimal
  volume: Decimal
  available_at: datetime
  received_at: datetime
  provenance: DataProvenance
```

## قیود اعتبارسنجی

- `instrument` و `interval` خالی نباشند.
- `open_time < close_time`.
- `high >= max(open, close)`.
- `low <= min(open, close)`.
- `volume >= 0`.
- `available_at <= received_at`.
- timestampها timezone-aware باشند.
- provenance شامل منبع، شناسهٔ پاسخ یا batch و schema version باشد.

## نرمال‌سازی

adapter باید تفاوت‌های نام‌گذاری و قالب صرافی‌ها را به این مدل تبدیل کند؛ برای مثال:

- نام نماد به قالب canonical پروژه تبدیل شود.
- intervalهای منبع به مجموعهٔ intervalهای پشتیبانی‌شده نگاشت شوند.
- اعداد از رشته یا نوع عددی منبع به `Decimal` تبدیل شوند.
- timestampهای میلی‌ثانیه‌ای یا ثانیه‌ای به `datetime` timezone-aware تبدیل شوند.
- دادهٔ ناقص یا ناسازگار رد شود و وضعیت کیفیت مناسب ثبت گردد.

## خروجی adapter

خروجی نهایی باید از قرارداد `ReadOnlyDataSource` و مدل `NormalizedSnapshot` پیروی کند. adapter نباید تصمیم معاملاتی بگیرد و نباید هیچ endpoint خصوصی یا معاملاتی را فراخوانی کند.

## معیار پذیرش

- تست‌های unit برای قیود کندل وجود داشته باشد.
- تست PIT/no-lookahead برای `available_at` وجود داشته باشد.
- تست deterministic بودن نرمال‌سازی وجود داشته باشد.
- تست رد دادهٔ منفی، timestamp نامعتبر و OHLC ناسازگار وجود داشته باشد.
- تست عدم وجود قابلیت سفارش‌گذاری یا معامله وجود داشته باشد.
