"""
Branded HTML email layout for OpenShiksha (the V2 "Unlock" design system).

The notification helpers in ``apps/core/emails.py`` and ``apps/ai/emails.py``
keep sending a plain-text body (the multipart/alternative fallback, and what the
test-suite asserts on). This module renders the *prettier* ``html_message`` that
rides alongside it: a responsive, table-based, inline-styled shell that survives
Gmail / Outlook / Apple Mail.

Design tokens mirror ``frontend_modern/tailwind.config.js`` — anchor orange
``#FF6F00``, warm "ink" neutrals, the graduation-cap keyhole logo, a Fraunces
wordmark. Localized chrome (en/hi/…) follows the same dependency-free catalog
approach as ``core.emails`` (no gettext/.po for a handful of strings).

Image and link URLs are absolute (``settings.EMAIL_LOGO_URL`` /
``settings.EMAIL_APP_URL``) so they resolve inside a mail client.
"""

from datetime import datetime

from django.conf import settings

# ── Brand palette (mirrors tailwind.config.js) ──────────────────────────────
BRAND_600 = "#FF6F00"  # brand anchor (legacy logo orange)
BRAND_700 = "#CC5800"
BRAND_100 = "#FFEEDC"
BRAND_50 = "#FFF8F1"
INK_900 = "#0F0E0D"
INK_700 = "#252220"
INK_500 = "#4A463F"
INK_400 = "#736D63"
INK_100 = "#E7E5E2"
INK_50 = "#F6F5F4"
WHITE = "#FFFFFF"

# Score / severity accents.
OK_GREEN = "#15803D"
WARN_AMBER = "#B45309"
WARN_AMBER_BG = "#FEF6EC"
BAD_RED = "#B91C1C"

FONT_SANS = (
    "-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue'," "Arial,'Noto Sans Devanagari',sans-serif"
)
FONT_SERIF = "'Fraunces',Georgia,'Times New Roman','Noto Sans Devanagari',serif"

# Brace-heavy <style> kept as a plain (non f-string) constant so the inline,
# brace-free fragments below can use f-strings freely.
_HEAD_STYLE = """
<style>
  body,table,td,a{-webkit-text-size-adjust:100%;-ms-text-size-adjust:100%;}
  table,td{mso-table-lspace:0pt;mso-table-rspace:0pt;}
  img{border:0;line-height:100%;outline:none;text-decoration:none;-ms-interpolation-mode:bicubic;}
  body{margin:0!important;padding:0!important;width:100%!important;}
  a{color:#FF6F00;}
  @media only screen and (max-width:600px){
    .os-container{width:100%!important;}
    .os-px{padding-left:22px!important;padding-right:22px!important;}
  }
</style>
"""

# ── Localized chrome (header tagline + footer) ──────────────────────────────
_CHROME = {
    "en": {
        "tagline": "Unlock every student's potential",
        "footer": (
            "You're receiving this email from OpenShiksha. You can manage your "
            "email preferences in your profile settings."
        ),
    },
    "hi": {
        "tagline": "हर विद्यार्थी की क्षमता को अनलॉक करें",
        "footer": (
            "यह ईमेल आपको OpenShiksha की ओर से मिला है। आप अपनी प्रोफ़ाइल "
            "सेटिंग्स में ईमेल प्राथमिकताएँ प्रबंधित कर सकते हैं।"
        ),
    },
}


def _chrome(lang: str, key: str) -> str:
    return (_CHROME.get(lang) or _CHROME["en"]).get(key) or _CHROME["en"][key]


def _logo_url() -> str:
    return getattr(settings, "EMAIL_LOGO_URL", "https://openshiksha.org/brand/logo-orange.png")


def _app_url() -> str:
    return getattr(settings, "EMAIL_APP_URL", "https://openshiksha.org")


# ── Reusable, email-safe components ─────────────────────────────────────────
def button(label: str, url: str, color: str = BRAND_600) -> str:
    """A bulletproof (table-wrapped) call-to-action button."""
    return (
        '<table role="presentation" cellpadding="0" cellspacing="0" border="0" '
        'style="margin:24px 0 4px;"><tr>'
        f'<td align="center" bgcolor="{color}" style="border-radius:12px;">'
        f'<a href="{url}" target="_blank" style="display:inline-block;'
        f"padding:14px 30px;font-family:{FONT_SANS};font-size:15px;font-weight:700;"
        f'color:#ffffff;text-decoration:none;border-radius:12px;">{label}</a>'
        "</td></tr></table>"
    )


def icon_badge(emoji: str, bg: str = BRAND_100) -> str:
    """A round, tinted emoji chip used as the email's hero icon."""
    return (
        '<table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr>'
        f'<td width="60" height="60" align="center" valign="middle" bgcolor="{bg}" '
        f'style="width:60px;height:60px;border-radius:30px;font-size:28px;'
        f'line-height:60px;text-align:center;">{emoji}</td></tr></table>'
    )


def score_ring(pct: int) -> str:
    """A circular score badge, centred and coloured by performance band.

    Horizontal centring rides on a full-width parent cell (``align="center"``)
    rather than table ``margin:auto`` (which some clients ignore); vertical
    centring uses ``line-height == height`` with ``mso-line-height-rule:exactly``
    so Outlook lines the digits up too.
    """
    if pct >= 75:
        color, bg = OK_GREEN, "#EAF6EE"
    elif pct >= 40:
        color, bg = WARN_AMBER, WARN_AMBER_BG
    else:
        color, bg = BAD_RED, "#FBEAEA"
    return (
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        'border="0"><tr><td align="center" style="padding:10px 0 6px;">'
        '<table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr>'
        f'<td width="120" height="120" align="center" valign="middle" bgcolor="{bg}" '
        f'style="width:120px;height:120px;border-radius:60px;text-align:center;'
        f"font-family:{FONT_SANS};font-size:32px;font-weight:700;color:{color};"
        f'line-height:120px;mso-line-height-rule:exactly;">{pct}%</td>'
        "</tr></table></td></tr></table>"
    )


def info_panel(label: str, body: str, accent: str = BRAND_600, bg: str = BRAND_50) -> str:
    """A left-accented callout panel (used for alerts / home activities)."""
    return (
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        f'border="0" style="margin:12px 0;background:{bg};border-radius:0 12px 12px 0;">'
        f'<tr><td style="padding:14px 18px;border-left:4px solid {accent};'
        f'font-family:{FONT_SANS};">'
        f'<div style="font-size:12px;font-weight:700;color:{accent};'
        f'text-transform:uppercase;letter-spacing:.6px;">{label}</div>'
        f'<div style="font-size:15px;color:{INK_700};line-height:1.55;'
        f'margin-top:5px;">{body}</div></td></tr></table>'
    )


def paragraph(html: str, color: str = INK_500) -> str:
    return (
        f'<p style="margin:0 0 14px;font-family:{FONT_SANS};font-size:16px;'
        f'line-height:1.6;color:{color};">{html}</p>'
    )


def render_branded_email(
    *,
    lang: str,
    preheader: str,
    badge_emoji: str,
    accent: str,
    heading: str,
    eyebrow: str = "",
    body_html: str,
    cta_label: str,
    cta_url: str = "",
) -> str:
    """Wrap per-email content in the shared OpenShiksha branded shell."""
    lang = lang if lang in _CHROME else "en"
    logo = _logo_url()
    url = cta_url or _app_url()
    tagline = _chrome(lang, "tagline")
    footer = _chrome(lang, "footer")
    year = datetime.now().year

    eyebrow_html = (
        f'<div style="font-family:{FONT_SANS};font-size:13px;font-weight:700;'
        f"letter-spacing:.6px;text-transform:uppercase;color:{accent};"
        f'margin:18px 0 6px;">{eyebrow}</div>'
        if eyebrow
        else ""
    )
    cta_html = button(cta_label, url, accent) if cta_label else ""

    return (
        f'<!DOCTYPE html><html lang="{lang}" xmlns="http://www.w3.org/1999/xhtml">'
        '<head><meta charset="utf-8"/>'
        '<meta name="viewport" content="width=device-width,initial-scale=1"/>'
        '<meta http-equiv="X-UA-Compatible" content="IE=edge"/>'
        "<title>OpenShiksha</title>"
        f"{_HEAD_STYLE}</head>"
        f'<body style="margin:0;padding:0;background:{INK_50};">'
        # Hidden preview text for the inbox list.
        f'<div style="display:none;max-height:0;overflow:hidden;mso-hide:all;'
        f'font-size:1px;line-height:1px;color:{INK_50};opacity:0;">{preheader}'
        "&#8203;&#8203;&#8203;&#8203;&#8203;&#8203;&#8203;&#8203;&#8203;&#8203;</div>"
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        f'border="0" style="background:{INK_50};"><tr>'
        '<td align="center" style="padding:28px 12px;">'
        '<table role="presentation" class="os-container" width="600" cellpadding="0" '
        'cellspacing="0" border="0" style="width:600px;max-width:600px;'
        f"background:{WHITE};border:1px solid {INK_100};border-radius:18px;"
        'overflow:hidden;">'
        # Top accent bar.
        f'<tr><td height="6" bgcolor="{accent}" style="height:6px;line-height:6px;'
        f'font-size:6px;background:{accent};">&nbsp;</td></tr>'
        # Header: logo + wordmark.
        '<tr><td class="os-px" style="padding:24px 32px 6px;">'
        '<table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr>'
        f'<td valign="middle"><img src="{logo}" width="40" height="40" alt="OpenShiksha" '
        'style="display:block;border-radius:9px;"/></td>'
        f'<td valign="middle" style="padding-left:12px;font-family:{FONT_SERIF};'
        f'font-size:21px;font-weight:600;color:{INK_900};letter-spacing:-.2px;">'
        "OpenShiksha</td></tr></table></td></tr>"
        # Hero icon.
        '<tr><td class="os-px" style="padding:18px 32px 0;">'
        f"{icon_badge(badge_emoji, BRAND_100 if accent == BRAND_600 else WARN_AMBER_BG)}"
        "</td></tr>"
        # Heading + body.
        '<tr><td class="os-px" style="padding:14px 32px 8px;">'
        f"{eyebrow_html}"
        f'<h1 style="margin:0 0 14px;font-family:{FONT_SERIF};font-size:25px;'
        f'line-height:1.25;font-weight:700;color:{INK_900};">{heading}</h1>'
        f"{body_html}"
        f"{cta_html}"
        "</td></tr>"
        # Divider.
        '<tr><td class="os-px" style="padding:18px 32px 0;">'
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        f'border="0"><tr><td height="1" bgcolor="{INK_100}" '
        'style="height:1px;line-height:1px;font-size:1px;">&nbsp;</td></tr></table>'
        "</td></tr>"
        # Footer.
        '<tr><td class="os-px" style="padding:16px 32px 30px;">'
        f'<div style="font-family:{FONT_SERIF};font-size:14px;font-weight:600;'
        f'color:{INK_700};">OpenShiksha</div>'
        f'<div style="font-family:{FONT_SANS};font-size:13px;color:{INK_400};'
        f'margin-top:2px;">{tagline}</div>'
        f'<div style="font-family:{FONT_SANS};font-size:12px;color:{INK_400};'
        f'line-height:1.6;margin-top:12px;">{footer}</div>'
        f'<div style="font-family:{FONT_SANS};font-size:12px;color:{INK_400};'
        f'margin-top:10px;">© {year} OpenShiksha</div>'
        "</td></tr>"
        "</table></td></tr></table></body></html>"
    )
