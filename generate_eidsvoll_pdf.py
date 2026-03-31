#!/usr/bin/env python3
"""
Eidsvoll Investment One-Pager PDF
Styrilia 51D, 2080 Eidsvoll
Struktur: David = GP, NHC Property = LP
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor, white, black
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ── Fonts ──────────────────────────────────────────────────────────────────────
VERA_PATH      = "/Users/claudeagent/Library/Python/3.9/lib/python/site-packages/reportlab/fonts/Vera.ttf"
VERA_BOLD_PATH = "/Users/claudeagent/Library/Python/3.9/lib/python/site-packages/reportlab/fonts/VeraBd.ttf"
pdfmetrics.registerFont(TTFont("Vera",     VERA_PATH))
pdfmetrics.registerFont(TTFont("VeraBold", VERA_BOLD_PATH))

# ── Farger ─────────────────────────────────────────────────────────────────────
DARK_BLUE  = HexColor("#1a2744")
MID_BLUE   = HexColor("#2c4a8c")
LIGHT_BLUE = HexColor("#e8edf7")
GOLD       = HexColor("#b8860b")
LIGHT_GRAY = HexColor("#f5f5f5")
MID_GRAY   = HexColor("#888888")
GREEN      = HexColor("#006600")
RED        = HexColor("#cc0000")

W, H   = A4
OUTPUT = "/Users/claudeagent/helseboliger/eidsvoll_one_pager.pdf"

# ── Finansmodell ───────────────────────────────────────────────────────────────
PURCHASE_PRICE      = 5_000_000
DOK_AVGIFT          = round(PURCHASE_PRICE * 0.025)   # 125 000
FINDERS_FEE         = 100_000
TRANS_COST_KJØP     =  50_000
TRANS_COST_EXIT     =  50_000
TOTAL_COST          = PURCHASE_PRICE + DOK_AVGIFT + FINDERS_FEE + TRANS_COST_KJØP  # 5 275 000

LTV          = 0.80
LOAN_AMOUNT  = round(TOTAL_COST * LTV)        # 4 180 000
EQUITY       = TOTAL_COST - LOAN_AMOUNT        # 1 045 000

RATE_ANNUAL  = 0.06
PERIODS      = 25 * 12                         # 300 måneder
monthly_rate = RATE_ANNUAL / 12
MONTHLY_PMT  = LOAN_AMOUNT * (monthly_rate * (1 + monthly_rate)**PERIODS) / \
               ((1 + monthly_rate)**PERIODS - 1)
ANNUAL_DEBT_SVC = MONTHLY_PMT * 12

RENT_Y1       = 360_000
OPEX_RATE     = 0.04166   # ~4.2% av leieinntekt
KPI           = 0.02
EXIT_CAP_RATE = 0.07
PREF_RETURN   = 0.08
CARRY_GP      = 0.30

def noi(year):
    rent = RENT_Y1 * (1 + KPI) ** (year - 1)
    return rent * (1 - OPEX_RATE)

def loan_balance(year):
    n = year * 12
    return LOAN_AMOUNT * ((1 + monthly_rate)**PERIODS - (1 + monthly_rate)**n) / \
           ((1 + monthly_rate)**PERIODS - 1)

# Kontantstrøm år 1-5
cf_rows = []
for yr in range(1, 6):
    rent = RENT_Y1 * (1 + KPI) ** (yr - 1)
    opex = rent * OPEX_RATE
    n    = rent - opex
    ds   = ANNUAL_DEBT_SVC
    cf_rows.append((yr, rent, opex, n, ds, n - ds))

# Exitanalyse
noi_y6       = noi(6)
exit_value   = noi_y6 / EXIT_CAP_RATE
bal_y5       = loan_balance(5)
gross_equity = exit_value - bal_y5

gross_equity -= TRANS_COST_EXIT   # trekk fra transaksjonskostnad ved exit

pref_total        = EQUITY * ((1 + PREF_RETURN)**5 - 1)
above_hurdle      = max(0, gross_equity - EQUITY - pref_total)
carry_gp          = above_hurdle * CARRY_GP
lp_proceeds       = EQUITY + pref_total + above_hurdle * (1 - CARRY_GP)

# IRR (Newton)
def irr(cashflows, guess=0.10):
    r = guess
    for _ in range(1000):
        npv  = sum(cf / (1 + r)**t for t, cf in enumerate(cashflows))
        dnpv = sum(-t * cf / (1 + r)**(t + 1) for t, cf in enumerate(cashflows))
        if abs(dnpv) < 1e-12:
            break
        r -= npv / dnpv
    return r

lp_irr = irr([-EQUITY, 0, 0, 0, 0, lp_proceeds]) * 100
dscr_y1 = noi(1) / ANNUAL_DEBT_SVC

# ── Hjelpefunksjoner ───────────────────────────────────────────────────────────
def fmt(n):
    return f"{int(round(n)):,}".replace(",", "\u00a0")   # non-breaking space

def box(c, x, y, w, h, color, r=0):
    c.setFillColor(color)
    if r:
        c.roundRect(x, y, w, h, r, fill=1, stroke=0)
    else:
        c.rect(x, y, w, h, fill=1, stroke=0)

def txt(c, x, y, s, font="Vera", size=9, color=black, align="left"):
    c.setFont(font, size)
    c.setFillColor(color)
    if   align == "center": c.drawCentredString(x, y, s)
    elif align == "right":  c.drawRightString(x, y, s)
    else:                   c.drawString(x, y, s)

def section_hdr(c, y, label, margin, body_w):
    """Tegner blå seksjonsheader og returnerer ny y (justert for innhold nedenfor)."""
    HDR_H = 0.52 * cm
    box(c, margin, y - HDR_H, body_w, HDR_H, MID_BLUE)
    txt(c, margin + 0.3*cm, y - HDR_H + 0.13*cm, label, "VeraBold", 9, white)
    return y - HDR_H - 0.22*cm   # luftrom mellom header og første innholdslinje

# ── Bygg PDF ───────────────────────────────────────────────────────────────────
def build():
    c      = canvas.Canvas(OUTPUT, pagesize=A4)
    c.setTitle("Eidsvoll Investering — One Pager")
    c.setAuthor("Helseboliger AS")

    margin = 1.8 * cm
    body_w = W - 2 * margin

    # ── Topptekst ────────────────────────────────────────────────────────────────
    box(c, 0, H - 2.8*cm, W, 2.8*cm, DARK_BLUE)
    txt(c, W/2, H - 1.55*cm, "INVESTERINGSMULIGHET \u2014 EIDSVOLL",
        "VeraBold", 14, white, "center")
    txt(c, W/2, H - 2.25*cm,
        "Styrilia 51D, 2080 Eidsvoll  |  Helseboliger AS  |  Konfidensiell",
        "Vera", 8, HexColor("#aabbdd"), "center")

    y = H - 3.1*cm

    # ── KPI-strip (2 kolonner) ───────────────────────────────────────────────────
    kpis = [
        ("Kj\u00f8pesum",             f"{fmt(PURCHASE_PRICE)} NOK"),
        ("Dokumentavgift (2,5%)",     f"{fmt(DOK_AVGIFT)} NOK"),
        ("Findersfee Helseboliger",   f"{fmt(FINDERS_FEE)} NOK"),
        ("Transaksjonskostn. kj\u00f8p", f"{fmt(TRANS_COST_KJØP)} NOK"),
        ("Total investering",         f"{fmt(TOTAL_COST)} NOK"),
        ("Areal / type",              "106 m\u00b2  |  4 soverom"),
        ("Leietaker",                 "Auris Helse AS"),
        ("Leiekontrakt",              "10 \u00e5r, KPI-regulert"),
        ("Brutto leie/\u00e5r",       "360\u00a0000 NOK"),
        ("NOI \u00e5r 1",             f"{fmt(noi(1))} NOK"),
        ("DSCR",                      f"{dscr_y1:.2f}x"),
        ("Egenkapital (EK)",          f"{fmt(EQUITY)} NOK  (20%)"),
        ("Banklån (80%)",             f"{fmt(LOAN_AMOUNT)} NOK  @6%  25 år"),
        ("Transaksjonskostn. exit",   f"{fmt(TRANS_COST_EXIT)} NOK"),
    ]
    col_w = body_w / 2 - 0.3*cm
    kpi_h = 0.7*cm
    for i, (label, val) in enumerate(kpis):
        col = i % 2
        row = i // 2
        bx  = margin + col * (col_w + 0.6*cm)
        by  = y - (row + 1) * kpi_h - row * 0.1*cm
        bg  = LIGHT_BLUE if row % 2 == 0 else LIGHT_GRAY
        box(c, bx, by, col_w, kpi_h - 0.05*cm, bg, 2)
        txt(c, bx + 0.3*cm,        by + 0.2*cm, label, "Vera",     7.5, MID_GRAY)
        txt(c, bx + col_w - 0.3*cm, by + 0.2*cm, val,  "VeraBold", 8.5, DARK_BLUE, "right")

    y -= (len(kpis)//2 + 1) * kpi_h + 0.35*cm

    # ── Struktur GP/LP ───────────────────────────────────────────────────────────
    y = section_hdr(c, y, "STRUKTUR  (GP / LP)", margin, body_w)

    struct_lines = [
        ("GP (General Partner):",  "David Myrann \u2014 prosjektledelse, forvaltning, daglig drift"),
        ("LP (Limited Partner):",  f"NHC Property \u2014 100% av egenkapital (NOK {fmt(EQUITY)})"),
        ("Preferert avkastning:",  "8% p.a. til LP (sammensatt rente p\u00e5 innest\u00e5ende EK)"),
        ("Carry til GP:",          "30% av overskudd over 8%-hurdle"),
        ("Holdingsperiode:",       "5 \u00e5r  |  Leiekontrakt: 10 \u00e5r"),
    ]
    line_h = 0.48*cm
    for label, val in struct_lines:
        txt(c, margin + 0.25*cm, y, label, "VeraBold", 8, DARK_BLUE)
        txt(c, margin + 5.2*cm,  y, val,   "Vera",     8, black)
        y -= line_h

    y -= 0.35*cm

    # ── 5-års kontantstrøm ───────────────────────────────────────────────────────
    y = section_hdr(c, y, "5-\u00c5RS KONTANTSTROM  (NOK)", margin, body_w)

    cols   = [("\u00c5r", 0.7*cm), ("Brutto leie", 2.5*cm), ("Driftskostnad", 2.6*cm),
              ("NOI",    2.4*cm),  ("Gjeldsbetj.", 2.8*cm), ("Fri KS",        2.4*cm)]
    col_xs = []
    cx = margin
    for _, cw in cols:
        col_xs.append(cx)
        cx += cw

    # kolonneheader
    box(c, margin, y - 0.44*cm, body_w, 0.44*cm, DARK_BLUE)
    for (label, cw), bx in zip(cols, col_xs):
        txt(c, bx + cw/2, y - 0.31*cm, label, "VeraBold", 7.5, white, "center")
    y -= 0.49*cm

    row_h = 0.47*cm
    for i, (yr, rent, opex, n, ds, cf) in enumerate(cf_rows):
        bg = LIGHT_GRAY if i % 2 == 0 else white
        box(c, margin, y - row_h + 0.05*cm, body_w, row_h, bg)
        vals = [str(yr), fmt(rent), fmt(opex), fmt(n), fmt(ds), fmt(cf)]
        for j, ((_, cw), bx) in enumerate(zip(cols, col_xs)):
            fc = (GREEN if cf >= 0 else RED) if j == 5 else DARK_BLUE
            txt(c, bx + cw/2, y - row_h + 0.13*cm, vals[j], "Vera", 8, fc, "center")
        y -= row_h

    y -= 0.3*cm

    # ── Exitanalyse ──────────────────────────────────────────────────────────────
    y = section_hdr(c, y,
        f"EXIT-ANALYSE  31.12 \u00c5R 5  (cap rate {EXIT_CAP_RATE*100:.0f}%)",
        margin, body_w)

    exit_rows = [
        (f"NOI \u00e5r 6 (basis for exit)",           f"{fmt(noi_y6)} NOK"),
        (f"Exitverdi  (NOI\u00e5r6 / {EXIT_CAP_RATE*100:.0f}%)", f"{fmt(exit_value)} NOK"),
        ("Gjenstående lånesaldo år 5",                f"{fmt(bal_y5)} NOK"),
        ("Brutto egenkapital ved exit",               f"{fmt(gross_equity)} NOK"),
        ("Tilbake EK til LP",                         f"{fmt(EQUITY)} NOK"),
        ("Preferert avkastning LP  (8% \u00d7 5 år, samm.)", f"{fmt(pref_total)} NOK"),
        ("Overskudd over hurdle",                     f"{fmt(above_hurdle)} NOK"),
        ("Carry GP  (30%)",                           f"{fmt(carry_gp)} NOK"),
        ("LP nettoproveny ved exit",                  f"{fmt(lp_proceeds)} NOK"),
        ("IRR til LP",                                f"{lp_irr:.1f}%"),
    ]
    for j, (label, val) in enumerate(exit_rows):
        bg   = LIGHT_BLUE if j % 2 == 0 else white
        bold = j == len(exit_rows) - 1
        box(c, margin, y - row_h + 0.05*cm, body_w, row_h, bg)
        fc_val = GOLD if bold else DARK_BLUE
        fn     = "VeraBold" if bold else "Vera"
        txt(c, margin + 0.3*cm,          y - row_h + 0.13*cm, label, fn,       8, DARK_BLUE)
        txt(c, margin + body_w - 0.3*cm, y - row_h + 0.13*cm, val,  "VeraBold", 8, fc_val, "right")
        y -= row_h

    y -= 0.4*cm

    # ── Hvorfor Eidsvoll ─────────────────────────────────────────────────────────
    y = section_hdr(c, y, "HVORFOR EIDSVOLL \u2014 INVESTERINGSCASE", margin, body_w)

    bullets = [
        "Etablert leiekontrakt med Auris Helse AS \u2014 lav kontraktsrisiko",
        "Helseboliger er et voksende segment: \u00d8kende behov for adekvate botilbud + kommunal boligmangel",
        f"Stabil KPI-regulert leieinntekt over 10-\u00e5rig kontrakt (5 \u00e5rs holding)",
        "Lav operasjonell risiko: ekstern forvalter (David / Helseboliger AS)",
        f"Exit basert p\u00e5 konservativ cap rate ({EXIT_CAP_RATE*100:.0f}%) \u2014 realistisk i segmentet",
    ]
    for b in bullets:
        c.setFillColor(GOLD)
        c.circle(margin + 0.25*cm, y - 0.08*cm, 2.5, fill=1, stroke=0)
        txt(c, margin + 0.55*cm, y - 0.14*cm, b, "Vera", 8, black)
        y -= 0.43*cm

    # ── Footer ───────────────────────────────────────────────────────────────────
    box(c, 0, 0, W, 1.2*cm, DARK_BLUE)
    txt(c, W/2, 0.57*cm,
        "Helseboliger AS  |  David Myrann  |  david@helseboliger.no  |  Konfidensiell \u2014 kun for adressaten",
        "Vera", 7.5, HexColor("#aabbdd"), "center")
    txt(c, W/2, 0.23*cm,
        "Estimater basert p\u00e5 tilgjengelig informasjon. Ikke en garanti for fremtidig avkastning.",
        "Vera", 6.5, MID_GRAY, "center")

    c.save()
    print(f"PDF lagret: {OUTPUT}")
    print(f"  Lån:            {fmt(LOAN_AMOUNT)} NOK  (80%)")
    print(f"  EK:             {fmt(EQUITY)} NOK  (20%)")
    print(f"  Årsleie:        {fmt(RENT_Y1)} NOK")
    print(f"  NOI år 1:       {fmt(noi(1))} NOK")
    print(f"  Gjeldsbetj/år:  {fmt(ANNUAL_DEBT_SVC)} NOK")
    print(f"  DSCR år 1:      {dscr_y1:.2f}x")
    print(f"  Exitverdi:      {fmt(exit_value)} NOK")
    print(f"  LP proveny:     {fmt(lp_proceeds)} NOK")
    print(f"  IRR LP:         {lp_irr:.1f}%")

if __name__ == "__main__":
    build()
