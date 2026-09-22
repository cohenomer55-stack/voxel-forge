# VoxelForge — Minecraft Litematic Builder

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

**לחץ על הכפתור כדי לפרוס את האתר ב-Render.** Render משתמש ב-`render.yaml` כדי להגדיר את השירות; שדה `OPENAI_API_KEY` מוגדר כ-secret prompt בזמן הפריסה. Render תומכת ב-Blueprints, Docker ו-Web Services ציבוריים עם תת-דומיין `onrender.com`.

## מה כלול

- אתר RTL בעברית.
- תיאור בנייה חופשי + תמונת השראה.
- Planner עם OpenAI Responses API.
- יצירת עולם ווקסלי דטרמיניסטי מהתכנית.
- יצירת PNG preview.
- יצירת `.litematic` עם `BlockStatePalette` ו-`BlockStates` דחוסים.
- תיבות עם לוט בסיסי.
- מצב Demo מקומי דרך `python -m uvicorn app:app --host 0.0.0.0 --port 8000` בלי API key.

## פריסה ב-Render

1. העלה את כל התיקייה הזו ל-GitHub כ-repository.
2. פתח את `README.md` ב-GitHub ולחץ **Deploy to Render**. Render מציינת שכפתור כזה משתמש ב-`render.yaml` ומאפשר למשתמש לאשר את המשאבים ולפרוס אותם במהירות. מומלץ להשתמש ב-repo ציבורי; עבור repo פרטי צריך הרשאות GitHub ל-Render.
3. במסך הראשון Render תבקש ערך ל-`OPENAI_API_KEY` כי הוא מוגדר `sync: false`.
4. `OPENAI_MODEL` כבר מוגדר ל-`gpt-5.6-luna`, וניתן לשנות אותו ב-Environment Variables.
5. אחרי ה-deploy תקבל כתובת ציבורית `https://<service>.onrender.com`.

## הערות

האתר הוא Web Service כי הוא מריץ קוד Python לכל בקשה. Render דורשת שהשרת יאזין על `0.0.0.0`; ה-Dockerfile משתמש ב-`PORT` של Render כברירת מחדל 10000.

הקבצים הנוצרים נשמרים זמנית על דיסק השירות. לפרויקט אמיתי עם הרבה משתמשים כדאי להוסיף Object Storage (למשל S3/R2) ושמירת jobs.
