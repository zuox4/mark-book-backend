import resend
import secrets

from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.models import EmailLog

# Инициализация Resend
resend.api_key = settings.RESEND_API_KEY


class ResendEmailService:

    @staticmethod
    def send_verification_email(
            db:Session,
            email: str,
            verification_token: str,
            user_name: str = None
    ) -> bool:
        """
        Отправка email с ссылкой подтверждения через Resend
        """
        try:
            verification_url = f"{settings.FRONTEND_URL}/api/auth/verify-email?token={verification_token}"

            # Создаем HTML контент
            html_content = ResendEmailService._create_verification_email_html(
                user_name=user_name,
                verification_url=verification_url
            )

            # Параметры для отправки
            params = {
                "from": f"{settings.SCHOOL_NAME} <{settings.RESEND_FROM_EMAIL}>",
                "to": [email],
                "subject": f"Подтверждение регистрации - {settings.SCHOOL_NAME}",
                "html": html_content,
                "reply_to": f"support@{settings.SCHOOL_DOMAIN}",
                "tags": [
                    {
                        "name": "category",
                        "value": "email_verification"
                    },
                    {
                        "name": "project",
                        "value": "school_platform"
                    }
                ]
            }

            # Отправка email
            result = resend.Emails.send(params)

            # Логируем успешную отправку
            email_log = EmailLog(
                email=email,
                subject=params["subject"],
                template_name="email_verification",
                status="sent"
            )
            db.add(email_log)
            db.commit()

            print(f"✅ Verification email sent to: {email}")
            print(f"📧 Email ID: {result['id']}")
            return True

        except Exception as e:
            print(f"❌ Failed to send verification email to {email}: {e}")

            # Логируем ошибку
            email_log = EmailLog(
                email=email,
                subject="Email Verification",
                template_name="email_verification",
                status="failed",
                error_message=str(e)
            )
            # db.add(email_log)
            # db.commit()
            return False

    @staticmethod
    def send_welcome_email(
            email: str,
            user_name: str = None
    ) -> bool:
        """
        Отправка приветственного email после подтверждения
        """
        try:
            html_content = ResendEmailService._create_welcome_email_html(user_name)

            params = {
                "from": f"{settings.SCHOOL_NAME} <{settings.RESEND_FROM_EMAIL}>",
                "to": [email],
                "subject": f"Добро пожаловать в {settings.SCHOOL_NAME}!",
                "html": html_content,
            }

            result = resend.Emails.send(params)
            #
            email_log = EmailLog(
                email=email,
                subject=params["subject"],
                template_name="welcome_email",
                status="sent"
            )
            # db.add(email_log)
            # db.commit()

            print(f"✅ Welcome email sent to: {email}")
            return True

        except Exception as e:
            print(f"❌ Failed to send welcome email: {e}")
            return False

    @staticmethod
    def _create_verification_email_html(user_name: str, verification_url: str) -> str:
        """
        Создание красивого HTML письма для подтверждения
        """
        return f"""
        <!DOCTYPE html>
        <html lang="ru">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Подтверждение email</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f9f9f9;
                }}
                .container {{
                    background: white;
                    border-radius: 10px;
                    padding: 40px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                }}
                .header {{
                    text-align: center;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    border-radius: 10px 10px 0 0;
                    margin: -40px -40px 30px -40px;
                }}
                .logo {{
                    font-size: 28px;
                    font-weight: bold;
                    margin-bottom: 10px;
                }}
                .button {{
                    display: inline-block;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 14px 28px;
                    text-decoration: none;
                    border-radius: 6px;
                    font-weight: 600;
                    font-size: 16px;
                    margin: 20px 0;
                    text-align: center;
                }}
                .verification-code {{
                    background: #f8f9fa;
                    border: 1px solid #e9ecef;
                    border-radius: 6px;
                    padding: 15px;
                    margin: 20px 0;
                    font-family: 'Courier New', monospace;
                    font-size: 14px;
                    word-break: break-all;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #eee;
                    color: #666;
                    font-size: 14px;
                }}
                @media (max-width: 600px) {{
                    .container {{
                        padding: 20px;
                    }}
                    .header {{
                        margin: -20px -20px 20px -20px;
                        padding: 20px;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">🎓 Школа 1298</div>
                    <p>Образовательная платформа</p>
                </div>

                <h2>Здравствуйте{', ' + user_name if user_name else ''}!</h2>

                <p>Благодарим вас за регистрацию в образовательной платформе <strong>{settings.SCHOOL_NAME}</strong>.</p>

                <p>Для завершения регистрации и активации вашего аккаунта, пожалуйста, подтвердите ваш email адрес:</p>

                <div style="text-align: center;">
                    <a href="{verification_url}" class="button">
                        ✅ Подтвердить Email
                    </a>
                </div>

                <p>Или скопируйте и вставьте в браузер следующую ссылку:</p>

                <div class="verification-code">
                    {verification_url}
                </div>

                <p><strong>⚠️ Важно:</strong> Ссылка действительна в течение 24 часов.</p>

                <p>Если вы не регистрировались в нашей системе, пожалуйста, проигнорируйте это письмо.</p>

                <div class="footer">
                    <p>С уважением,<br><strong>Команда {settings.SCHOOL_NAME}</strong></p>
                    <p>📧 Это письмо сгенерировано автоматически. Пожалуйста, не отвечайте на него.</p>
                </div>
            </div>
        </body>
        </html>
        """

    @staticmethod
    def _create_welcome_email_html(user_name: str) -> str:
        """
        Создание приветственного письма
        """
        return f"""
        <!DOCTYPE html>
        <html lang="ru">
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                    border-radius: 10px 10px 0 0;
                }}
                .content {{
                    background: white;
                    padding: 30px;
                    border-radius: 0 0 10px 10px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🎉 Добро пожаловать!</h1>
                <p>Ваш аккаунт успешно активирован</p>
            </div>
            <div class="content">
                <h2>Здравствуйте{', ' + user_name if user_name else ''}!</h2>
                <p>Мы рады приветствовать вас в образовательной платформе <strong>{settings.SCHOOL_NAME}</strong>!</p>

                <p>Теперь вам доступны все возможности системы:</p>
                <ul>
                    <li>📊 Просмотр ваших достижений и оценок</li>
                    <li>📅 Доступ к расписанию занятий</li>
                    <li>👨‍🏫 Общение с преподавателями</li>
                    <li>🏆 Участие в мероприятиях и олимпиадах</li>
                </ul>

                <p>Если у вас возникнут вопросы, обращайтесь к администратору системы.</p>

                <p>С уважением,<br>
                <strong>Команда {settings.SCHOOL_NAME}</strong></p>
            </div>
        </body>
        </html>
        """

    @staticmethod
    def generate_verification_token() -> str:
        """Генерация безопасного токена для верификации"""
        return secrets.token_urlsafe(32)