"""Presentation text for Telegram Stars billing."""

# The interface intentionally includes Russian prose.
# ruff: noqa: RUF001

from bot.i18n import Locale

_LANGUAGE_INDEX = {language: index for index, language in enumerate(Locale)}

_TEXT = {
    "home": ("⭐ <b>Подписка Pro</b>", "⭐ <b>Pro subscription</b>", "⭐ <b>Suscripción Pro</b>"),
    "offer": (
        "Платный Pro стоит <b>{stars} звёзд Telegram</b> каждые 30 дней. "
        "Telegram показывает цену в местной валюте при покупке звёзд. "
        "Подписка продлевается автоматически, пока включено автопродление.",
        "Paid Pro costs <b>{stars} Telegram Stars</b> every 30 days. "
        "Telegram shows local prices when you buy Stars. "
        "The subscription renews while auto-renew is enabled.",
        "Pro de pago cuesta <b>{stars} estrellas de Telegram</b> cada 30 días. "
        "Telegram muestra los precios locales al comprar estrellas. "
        "La suscripción se renueva mientras esté activada la renovación automática.",
    ),
    "active": (
        "Доступ оплачен до <b>{date}</b>.",
        "Paid access is valid until <b>{date}</b>.",
        "El acceso pagado sigue vigente hasta <b>{date}</b>.",
    ),
    "renewal_stopped": (
        "Автопродление отключено через бот.",
        "Auto-renew was turned off through the bot.",
        "La renovación automática se desactivó desde el bot.",
    ),
    "unavailable": (
        "Новые подписки сейчас недоступны.",
        "New subscriptions are currently unavailable.",
        "Las nuevas suscripciones no están disponibles en este momento.",
    ),
    "trial_offer": (
        "Попробуйте Pro бесплатно в течение трёх календарных месяцев. "
        "Пробный период доступен один раз, без списаний и автопродления.",
        "Try Pro free for three calendar months. "
        "The trial is available once, with no charge or auto-renewal.",
        "Prueba Pro gratis durante tres meses naturales. "
        "La prueba se ofrece una sola vez, sin cobros ni renovación automática.",
    ),
    "trial_start": (
        "Начать бесплатный пробный период на 3 месяца",
        "Start 3-month free trial",
        "Iniciar prueba gratis de 3 meses",
    ),
    "trial_active": (
        "Бесплатный Pro активен до <b>{date}</b>. "
        "После этого доступ вернётся к Free. Платную подписку можно оформить отдельно.",
        "Your free Pro trial is active until <b>{date}</b>. "
        "You’ll return to Free afterwards and can choose a paid subscription separately.",
        "Tu prueba gratuita de Pro está activa hasta <b>{date}</b>. "
        "Después volverás a Free y podrás contratar por separado una suscripción de pago.",
    ),
    "trial_used": (
        "Ваш бесплатный пробный период завершился.",
        "Your free trial has ended.",
        "Tu prueba gratuita ha finalizado.",
    ),
    "trial_pending": (
        "Пробный период недоступен. Проверьте ожидающий платёж или откройте /paysupport.",
        "Could not start the trial. Check for a pending payment or open /paysupport.",
        "No se pudo iniciar la prueba. Comprueba si hay un pago pendiente o abre /paysupport.",
    ),
    "buy": ("Выставить счёт", "Create invoice", "Crear factura"),
    "pay": ("Оплатить в Telegram", "Pay in Telegram", "Pagar en Telegram"),
    "terms": ("Условия подписки", "Subscription terms", "Condiciones de suscripción"),
    "support": (
        "Помощь с платежами",
        "Payment support",
        "Ayuda con pagos",
    ),
    "support_hint": (
        "Опишите проблему и укажите дату платежа из квитанции Telegram. "
        "Для обращения достаточно даты и суммы.",
        "Describe the issue and include the date and amount shown on your Telegram receipt.",
        "Describe el problema e indica la fecha y el importe del recibo de Telegram.",
    ),
    "contact": ("Связаться с поддержкой", "Contact support", "Contactar con soporte"),
    "cancel": (
        "Отключить автопродление",
        "Turn off auto-renew",
        "Desactivar renovación automática",
    ),
    "confirm_cancel": (
        "Вы отключаете автопродление. Доступ сохранится до {date}.",
        "Turning off auto-renew keeps your paid access through {date}.",
        "Al desactivar la renovación, conservas el acceso pagado hasta {date}.",
    ),
    "confirm_button": (
        "Подтвердить отключение",
        "Confirm turn-off",
        "Confirmar desactivación",
    ),
    "resume": (
        "Разрешить продление в Telegram",
        "Allow renewal in Telegram",
        "Permitir renovación en Telegram",
    ),
    "cancelled": (
        "Автопродление отключено. Доступ сохранён до {date}.",
        "Auto-renew is off. Paid access continues through {date}.",
        "La renovación está desactivada. Conservas el acceso pagado hasta {date}.",
    ),
    "resumed": (
        "Теперь вы можете снова включить автопродление в настройках подписок Telegram.",
        "You can now re-enable auto-renew in Telegram's subscription settings.",
        "Ya puedes volver a activar la renovación en los ajustes de suscripciones de Telegram.",
    ),
    "stale": (
        "Откройте /pro, чтобы обновить сведения о подписке.",
        "Open /pro to refresh your subscription details.",
        "Abre /pro para actualizar los datos de tu suscripción.",
    ),
    "checkout_error": (
        "Не удалось подтвердить счёт. Откройте /pro и при необходимости получите новый счёт.",
        "We could not verify this invoice. Open /pro to check your plan or get a new invoice.",
        "No pudimos verificar la factura. Abre /pro para revisar tu plan u obtener una nueva.",
    ),
    "invoice_title": ("Python Mentor Pro", "Python Mentor Pro", "Python Mentor Pro"),
    "invoice_description": (
        "Доступ к разбору кода и подготовке к интервью. Автопродление каждые 30 дней.",
        "Code reviews and interview practice. Renews every 30 days.",
        "Revisión de código y práctica de entrevistas. Renovación cada 30 días.",
    ),
    "review": ("Разбор кода", "Code review", "Revisión de código"),
    "interview": ("Тренировка интервью", "Interview practice", "Práctica de entrevistas"),
    "dashboard": ("🏠 Главное меню", "🏠 Dashboard", "🏠 Inicio"),
    "back": ("Назад к подписке", "Back to subscription", "Volver a la suscripción"),
}


def billing_tr(locale: Locale, key: str, **values: str | int) -> str:
    """Read a localized billing label or message."""
    return _TEXT[key][_LANGUAGE_INDEX[locale]].format(**values)
