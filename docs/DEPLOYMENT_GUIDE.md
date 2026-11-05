# Enterprise Deployment & Configuration Guide

این راهنما گام‌به‌گام نحوه استقرار، کانفیگ و اتصال اجزای سامانه:
**Chatwoot (Omnichannel Inbox) + Dify (RAG & Brain) + FastAPI (Bridge Middleware) + Typebot**
را روی یک سرور لینوکسی (Ubuntu 22.04 / 24.04 LTS) شرح می‌دهد.

---

## ۱. پیش‌نیازهای سرور (Server Prerequisites)

- **سیستم‌عامل:** Ubuntu 22.04 / 24.04 LTS
- **حداقل مشخصات سخت‌افزاری:**
  - ۴ الی ۸ هسته پردازنده (vCPU)
  - ۱۶ الی ۳۲ گیگابایت رم (RAM)
  - حداقل ۸۰ گیگابایت حافظه پرسرعت SSD NVMe
- **نصب پکیج‌های پایه:**
  ```bash
  sudo apt update && sudo apt upgrade -y
  sudo apt install -y git curl wget ufw
  ```
- **نصب Docker و Docker Compose:**
  ```bash
  curl -fsSL https://get.docker.com -o get-docker.sh
  sudo sh get-docker.sh
  sudo usermod -aG docker $USER
  ```

---

## ۲. ایجاد شبکه مشترک داکر (Shared Network)

برای اینکه تمامی سرویس‌ها (Chatwoot, Dify, Middleware, Caddy) بتوانند بدون نیاز به باز کردن پورت‌های داخلی روی فایروال سرور با یکدیگر ارتباط پرسرعت و امن داشته باشند:

```bash
docker network create omnichannel-net
```

---

## ۳. راه‌اندازی Dify (مغز هوش مصنوعی و پایگاه دانش RAG)

۱. ریپازیتوری رسمی Dify را کلون کنید:
```bash
git clone https://github.com/langgenius/dify.git /opt/dify
cd /opt/dify/docker
```
۲. فایل محیطی را کپی کنید:
```bash
cp .env.example .env
```
۳. در فایل `docker-compose.yaml` دایفی، شبکه `omnichannel-net` را به بخش `networks` سرویس‌های `api` و `web` اضافه کنید:
```yaml
networks:
  default:
  omnichannel-net:
    external: true
```
۴. سرویس Dify را روشن کنید:
```bash
docker compose up -d
```
۵. پس از اتمام، وارد آدرس دایفی (مثلاً `http://SERVER_IP:3000` یا دامنه تنظیم‌شده `brain.yourdomain.com`) شوید و حساب مدیر ارشد را بسازید.

### کانفیگ ضد هذیان (Anti-Hallucination Guardrails) در Dify:
در بخش **Knowledge** اسناد رسمی (PDF تعرفه، قوانین، ساعات کار، دستورالعمل‌ها) را آپلود کنید:
- **Segment Mode:** Custom
- **Segment Length:** 500 Tokens
- **Overlap:** 50 Tokens
- **Index Mode:** High Quality (با مدل Embedding مثل `text-embedding-3-small` یا مدل محلی)
- **Retrieval Setting:** 
  - **Search Method:** Hybrid Search (Vector + Full-text Keyword)
  - **Top K:** 3
  - **Score Threshold:** `0.75` (هر متنی با ضریب تطابق کمتر از 0.75 مسدود می‌شود)
  - **Reranking Model:** فعال (BGE Reranker یا Cohere)

#### System Prompt تخصصی ضد خطا در چت‌بات Dify:
```text
شما دستیار رسمی و هوشمند کلینیک/مرکز هستید.
وظیفه شما پاسخ‌دهی دقیق، محترمانه و خلاصه به مراجعین است.

قوانین غیرقابل نقض (Strict Anti-Hallucination Rules):
۱. فقط و فقط بر اساس اطلاعات موجود در بخش «زمینه‌های بازیابی‌شده (Context)» پاسخ دهید.
۲. تحت هیچ شرایطی از حدس و گمان، دانش عمومی یا تجویزهای پزشکی خارج از اسناد استفاده نکنید.
۳. در صورتی که پاسخ سوال کاربر در اسناد بازیابی‌شده وجود نداشت، یا سوال مربوط به تشخیص‌های بالینی پیچیده بود، دقیقاً این عبارت را بدون هیچ کلمه اضافی برگردانید:
[TRIGGER_HUMAN_HANDOFF]
۴. اگر کاربر هرگونه حس عصبانیت شدید، شکایت، نارضایتی، یا درخواست مستقیم اپراتور انسانی داشت، بلافاصله کد زیر را خروجی دهید:
[TRIGGER_HUMAN_HANDOFF]
```

سپس از بخش **Develop** اپلیکیشن دایفی، کلید **API Key** (با فرمت `app-...`) را کپی کنید.

---

## ۴. راه‌اندازی Chatwoot (پنل چندکاناله و اینباکس ارتباطات)

۱. ریپازیتوری استقرار داکر چت‌ووت را کلون کنید:
```bash
git clone https://github.com/chatwoot/chatwoot.git /opt/chatwoot
cd /opt/chatwoot
```
۲. فایل محیطی را بسازید:
```bash
cp .env.example .env
```
۳. در فایل `.env` مقادیر `SECRET_KEY_BASE` و دیتابیس را ست کرده و شبکه `omnichannel-net` را به سرویس `base` یا `rails` اختصاص دهید.
۴. دیتابیس چت‌ووت را آماده کرده و بالا بیاورید:
```bash
docker compose run --rm rails bundle exec rails db:chatwoot_prepare
docker compose up -d
```
۵. وارد پنل چت‌ووت شوید (`chat.yourdomain.com`).
۶. حساب کاربری ادمین، کانال مورد نظر (ویجت وبسایت، تلگرام یا واتساپ) و یک تیم پشتیبانی تحت عنوان **«پشتیبانی انسانی / پذیرش»** ایجاد کنید.
۷. از بخش **Settings -> Profile Settings** توکن **Access Token** را دریافت کنید.
۸. از بخش **Settings -> Integrations -> Webhooks** یک وبهوک جدید بسازید:
   - **Webhook URL:** `http://middleware:8000/webhook/chatwoot` (یا `https://api.yourdomain.com/webhook/chatwoot`)
   - **Subscriptions:** تیک گزینه `Message Created` و `Conversation Created` را فعال کنید.

---

## ۵. استقرار میان‌افزار (FastAPI Middleware Bridge)

۱. وارد پوشه پروژه شوید:
```bash
cd /opt/omnichannel-ai
```
۲. فایل `.env` را در پوشه `middleware` از روی نمونه بسازید:
```bash
cp middleware/.env.example middleware/.env
```
۳. مقادیر را ویرایش کنید:
```env
CHATWOOT_BASE_URL=http://chatwoot-web:3000
CHATWOOT_API_ACCESS_TOKEN=توکن_کپی_شده_از_چت_ووت
CHATWOOT_ACCOUNT_ID=1

DIFY_API_BASE_URL=http://dify-api:5001/v1
DIFY_API_KEY=app-توکن_کپی_شده_از_دایفی

GOOGLE_CALENDAR_ID=your_clinic_calendar_id@group.calendar.google.com
GOOGLE_SERVICE_ACCOUNT_FILE=google-credentials.json
TYPEBOT_PUBLIC_URL=https://bot.yourdomain.com/clinic-booking
```
۴. استقرار کانتینرهای Middleware و Caddy:
```bash
docker compose up -d --build
```
۵. تست سلامت سرویس:
```bash
curl http://localhost:8000/health
# خروجی: {"status":"healthy","service":"Omnichannel AI Bridge",...}
```

---

## ۶. تنظیم اتصال به Google Calendar (نوبت‌دهی خودکار)

برای اتصال امن و خودکار بدون نیاز به لاگین دستی مراجعین:

۱. وارد [Google Cloud Console](https://console.cloud.google.com) شوید و یک پروژه جدید ایجاد کنید.
۲. از بخش **APIs & Services -> Library**، سرویس **Google Calendar API** را فعال (Enable) کنید.
۳. از بخش **Credentials -> Create Credentials** گزینه **Service Account** را انتخاب کرده و یک اکانت بسازید (مثلاً `clinic-booking-bot@project-id.iam.gserviceaccount.com`).
۴. وارد تب **Keys** اکانت ساخته‌شده شوید، گزینه **Add Key -> Create new key (JSON)** را بزنید و فایل کلید را با نام `google-credentials.json` دانلود کنید.
۵. فایل دانلودی را در مسیر `middleware/google-credentials.json` کپی کنید.
۶. وارد تقویم کاری کلینیک در [Google Calendar](https://calendar.google.com) شوید:
   - روی تقویم کلینیک کلیک راست کرده و **Settings and sharing** را بزنید.
   - در بخش **Share with specific people or groups** ایمیل Service Account را اضافه کرده و دسترسی را روی **Make changes to events** بگذارید.
   - شناسه تقویم (Calendar ID) را از انتهای صفحه کپی کرده و در متغیر `GOOGLE_CALENDAR_ID` فایل `.env` قرار دهید.

---

## ۷. راه‌اندازی فاز اول: ویجت تحت وب (Web Live Chat)

۱. در پنل Chatwoot، به مسیر **Settings -> Inboxes -> Add Inbox** بروید.
۲. گزینه **Website** را انتخاب کنید:
   - **Website Name:** وب‌سایت کلینیک
   - **Website Domain:** `yourdomain.com`
   - **Widget Color:** رنگ سازمانی دلخواه
   - فعال‌سازی گزینه RTL و زبان فارسی در تنظیمات اینباکس
۳. کد اسکریپت تولید شده را در انتهای تگ `<body>` وب‌سایت یا قالب سیستم کلینیک قرار دهید (نمونه آماده در فایل [`web/widget-demo.html`](file:///d:/Omnichannel%20AI%20Customer%20Support%20%26%20Appointment%20System%20with%20Human%20Handoff/web/widget-demo.html) موجود است).

---

## ۸. فعال‌سازی فاز دوم: ربات تلگرام (Telegram Integration)

معماری سامانه به گونه‌ای طراحی شده که اضافه کردن تلگرام **بدون حتی یک خط تغییر کد در بک‌اند یا دایفی** انجام می‌پذیرد:

۱. در تلگرام با **@BotFather** یک ربات جدید بسازید و توکن API را دریافت کنید.
۲. در پنل Chatwoot، به مسیر **Settings -> Inboxes -> Add Inbox** بروید و کانال **Telegram** را انتخاب کنید.
۳. توکن دریافتی از BotFather را وارد کنید.
۴. تمام! از این لحظه، پیام‌های تلگرام دقیقاً از همان وب‌هوک و لاجیک مشترک RAG، نوبت‌دهی تقویم و ارجاع انسانی استفاده خواهند کرد.

---

## ۹. تست و اعتبارسنجی ارجاع به انسان (Zero-Fail Verification)

برای اثبات صحت سناریوی Human Handoff، آزمون‌های زیر را در ویجت چت انجام دهید:

| سناریوی آزمون | ورودی کاربر | رفتار مورد انتظار سیستم |
| :--- | :--- | :--- |
| **۱. پاسخ مبتنی بر سند** | "ساعت کاری کلینیک چطوریه؟" | هوش مصنوعی پاسخ رسمی را بر اساس سند با جزئیات کامل می‌دهد. |
| **۲. کلمه کلیدی مستقیم** | "لطفاً وصل کن به پشتیبان انسانی" | میان‌افزار فوراً قبل از ارسال به Dify، برچسب `human-needed` زده، تیکت را unassign کرده و نوت خصوصی به اپراتور می‌زند. |
| **۳. سوال خارج از سند (RAG Miss)** | "آیا شما عمل جراحی قلب باز انجام میدید؟" (در حالی که کلینیک پوست است) | دایفی به دلیل عدم وجود سند و شباهت زیر 0.75، توکن `[TRIGGER_HUMAN_HANDOFF]` می‌دهد و چت فوراً به اپراتور واگذار می‌شود. |
| **۴. لحن عصبانی / شکایت** | "این چه وضعشه! کلاهبرداری کردید، حالم خرابه!" | دایفی حس منفی را تشخیص داده، تیکت فوراً به صف اپراتور با اولویت بحرانی هدایت می‌شود. |
| **۵. سکوت پس از ارجاع** | پیام‌های بعدی کاربر بعد از ارجاع | ربات هیچ واکنشی نشان نمی‌دهد چون تگ `human-needed` فعال است تا زمانی که کارشناس انسان پاسخ دهد. |
