import os, datetime
from io import BytesIO
from flask import Flask, request, jsonify, Response, send_file

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER

app = Flask(__name__)

MOIS = ['','janvier','février','mars','avril','mai','juin',
        'juillet','août','septembre','octobre','novembre','décembre']

def P(text, size=8, align=TA_LEFT, bold=False, color=colors.black, italic=False):
    if bold and italic: fn = 'Helvetica-BoldOblique'
    elif bold:          fn = 'Helvetica-Bold'
    elif italic:        fn = 'Helvetica-Oblique'
    else:               fn = 'Helvetica'
    return Paragraph(text, ParagraphStyle('x',
        fontName=fn, fontSize=size, leading=size+3, alignment=align, textColor=color))

def fmt(n):
    return f"{n:,.2f}".replace(',', ' ').replace('.', ',') + ' €'

def generate_pdf_bytes(fa_num, fa_date, total_ht, qty):
    NAVY  = colors.HexColor('#22345b')   # bleu marine (bandeaux, filets, montants)
    LIGHT = colors.HexColor('#eef1f6')   # fond gris clair des encadrés
    GREY  = colors.HexColor('#8a8f99')   # gris labels / pied de page
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=15*mm, rightMargin=15*mm,
                            topMargin=14*mm, bottomMargin=20*mm)
    CW = A4[0] - 30*mm          # largeur utile
    s  = []

    # ── EN-TÊTE : logo « TT » + raison sociale  |  FACTURE + numéro ─────────────
    logo = Table([[P('TT', 16, TA_CENTER, True, colors.white)]],
                 colWidths=[15*mm], rowHeights=[15*mm])
    logo.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,-1),NAVY),('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),
        ('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),0)]))
    left = Table([[logo,
                   [P('TRADE TRONICS',20,TA_LEFT,True,NAVY),
                    P("Commerce de gros – Électronique d'occasion",8,TA_LEFT,
                      color=GREY,italic=True)]]],
                 colWidths=[17*mm, CW*0.55 - 17*mm])
    left.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(0,0),4),
        ('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),0)]))
    right = [P('FACTURE',20,TA_RIGHT,True,NAVY),
             P(f'N° FA-{fa_num:04d}',11,TA_RIGHT,color=GREY)]
    head = Table([[left, right]], colWidths=[CW*0.55, CW*0.45])
    head.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),
        ('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),0)]))
    s += [head, Spacer(1,4),
          HRFlowable(width='100%', thickness=1.5, color=NAVY,
                     spaceBefore=0, spaceAfter=12)]

    # ── ÉMETTEUR / DESTINATAIRE ────────────────────────────────────────────────
    em = ("<b>TRADE TRONICS</b><br/>SASU au capital de 500,00 €<br/>"
          "Bureau 326, 78 Avenue des Champs Élysées<br/>"
          "75008 Paris, France<br/>SIRET : 934 635 301 00013<br/>TVA : FR53934635301")
    de = ("<b>GATE TECHNOLOGY</b><br/>59 Avenue du Général de Gaulle<br/>"
          "Centre Commercial Westfield Rosny 2<br/>"
          "93110 Rosny-sous-Bois, France<br/>SIRET : 938 435 351 00011<br/>TVA : FR84938435351")
    def party(titre, corps):
        t = Table([[P(titre,9,bold=True,color=colors.white)],[P(corps,9)]],
                  colWidths=[(CW-6*mm)/2])
        t.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,0),NAVY),('BACKGROUND',(0,1),(-1,1),LIGHT),
            ('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),
            ('TOPPADDING',(0,0),(-1,0),5),('BOTTOMPADDING',(0,0),(-1,0),5),
            ('TOPPADDING',(0,1),(-1,1),8),('BOTTOMPADDING',(0,1),(-1,1),10)]))
        return t
    parties = Table([[party('ÉMETTEUR',em), '', party('DESTINATAIRE',de)]],
                    colWidths=[(CW-6*mm)/2, 6*mm, (CW-6*mm)/2])
    parties.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),
        ('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),
        ('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),0)]))
    s += [parties, Spacer(1,10)]

    # ── DATE / ÉCHÉANCE / RÈGLEMENT ────────────────────────────────────────────
    ech = fa_date + datetime.timedelta(days=30)
    info = Table([[P("DATE D'ÉMISSION",8,TA_CENTER,True,GREY),
                   P('ÉCHÉANCE',8,TA_CENTER,True,GREY),
                   P('MODE DE RÈGLEMENT',8,TA_CENTER,True,GREY)],
                  [P(fa_date.strftime('%d/%m/%Y'),11,TA_CENTER,True,NAVY),
                   P(ech.strftime('%d/%m/%Y'),11,TA_CENTER,True,NAVY),
                   P('Virement bancaire',11,TA_CENTER,True,NAVY)]],
                 colWidths=[CW/3]*3)
    info.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,-1),LIGHT),
        ('LINEAFTER',(0,0),(0,-1),.6,colors.white),
        ('LINEAFTER',(1,0),(1,-1),.6,colors.white),
        ('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),
        ('TOPPADDING',(0,0),(-1,0),8),('BOTTOMPADDING',(0,0),(-1,0),2),
        ('TOPPADDING',(0,1),(-1,1),2),('BOTTOMPADDING',(0,1),(-1,1),8)]))
    s += [info, Spacer(1,14)]

    # ── TABLEAU RÉCAPITULATIF ──────────────────────────────────────────────────
    sd = [[P('CATÉGORIE',10,TA_LEFT,True,colors.white),
           P('QTÉ',10,TA_CENTER,True,colors.white),
           P('TOTAL HT',10,TA_RIGHT,True,colors.white)],
          [P('Apple iPhone',10),P(str(qty),10,TA_CENTER),P(fmt(total_ht),10,TA_RIGHT)],
          [P('TOTAL',12,TA_LEFT,True,NAVY),'',P(fmt(total_ht),13,TA_RIGHT,True,NAVY)]]
    st = Table(sd, colWidths=[CW-56*mm, 26*mm, 30*mm])
    st.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),NAVY),
        ('BACKGROUND',(0,2),(-1,2),LIGHT),
        ('LINEBELOW',(0,1),(-1,1),.4,colors.HexColor('#d5dae3')),
        ('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),
        ('TOPPADDING',(0,0),(-1,0),6),('BOTTOMPADDING',(0,0),(-1,0),6),
        ('TOPPADDING',(0,1),(-1,1),9),('BOTTOMPADDING',(0,1),(-1,1),9),
        ('TOPPADDING',(0,2),(-1,2),9),('BOTTOMPADDING',(0,2),(-1,2),9)]))
    s += [st, Spacer(1,8),
          P(f"Voir annexe pour le détail des {qty} unités.",9,TA_LEFT,
            color=GREY,italic=True)]

    # ── ESPACE puis COORDONNÉES BANCAIRES / CONDITIONS (bas de page) ────────────
    s += [Spacer(1,60*mm)]
    banque = ("<b>COORDONNÉES BANCAIRES</b><br/><br/>"
              "<b>Pays :</b> BELGIQUE<br/>"
              "<b>IBAN :</b> BE58 9771 0386 1179<br/>"
              "<b>Code SWIFT/BIC :</b> PAYVBEB2XXX")
    cond   = ("<b>CONDITIONS</b><br/><br/>"
              "Paiement à 30 jours<br/>"
              "Escompte pour paiement anticipé : Néant<br/>"
              "Pénalités de retard : 3x taux légal<br/>"
              "TVA non applicable - Article 297-A du CGI<br/>"
              "Régime particulier - Biens d'occasion")
    # Une seule ligne de tableau => les deux encadrés ont la MÊME hauteur
    colw = (CW-6*mm)/2
    bas = Table([[P(banque,9), '', P(cond,9)]],
                colWidths=[colw, 6*mm, colw])
    bas.setStyle(TableStyle([
        ('VALIGN',(0,0),(-1,-1),'TOP'),
        # fond gris clair + filet marine à gauche des 2 colonnes de contenu
        ('BACKGROUND',(0,0),(0,0),LIGHT),('BACKGROUND',(2,0),(2,0),LIGHT),
        ('LINEBEFORE',(0,0),(0,0),3,NAVY),('LINEBEFORE',(2,0),(2,0),3,NAVY),
        # paddings des colonnes de contenu
        ('LEFTPADDING',(0,0),(0,0),10),('RIGHTPADDING',(0,0),(0,0),8),
        ('LEFTPADDING',(2,0),(2,0),10),('RIGHTPADDING',(2,0),(2,0),8),
        ('TOPPADDING',(0,0),(-1,-1),9),('BOTTOMPADDING',(0,0),(-1,-1),10),
        # colonne centrale = simple espace blanc
        ('LEFTPADDING',(1,0),(1,0),0),('RIGHTPADDING',(1,0),(1,0),0)]))
    s += [bas]

    # ── PIED DE PAGE ───────────────────────────────────────────────────────────
    def footer(c,d):
        c.setStrokeColor(colors.HexColor('#d5dae3')); c.setLineWidth(.5)
        c.line(15*mm, 16*mm, A4[0]-15*mm, 16*mm)
        c.setFont('Helvetica',7); c.setFillColor(GREY)
        c.drawCentredString(A4[0]/2,11*mm,
            'TRADE TRONICS – SASU au capital de 500,00 € – RCS Paris 934 635 301 '
            '– SIRET 934 635 301 00013 – TVA FR53934635301')
        c.drawCentredString(A4[0]/2,7*mm,
            'Bureau 326, 78 Avenue des Champs Élysées, 75008 Paris')
    doc.build(s, onFirstPage=footer, onLaterPages=footer)
    buf.seek(0)
    return buf

HTML = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Générateur de Factures — TRADE TRONICS</title>
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:-apple-system,Helvetica,sans-serif;background:#f0f2f7;
       display:flex;justify-content:center;align-items:center;min-height:100vh;padding:16px}
  .card{background:#fff;border-radius:16px;box-shadow:0 8px 32px rgba(0,0,0,.12);
        width:100%;max-width:420px;overflow:hidden}
  .banner{background:#1f4e8c;padding:28px 24px 22px;text-align:center;color:#fff}
  .banner h1{font-size:26px;font-weight:700;letter-spacing:1px}
  .banner p{font-size:12px;color:#adc4e8;margin-top:4px}
  .body{padding:28px 32px 32px}
  .info-row{display:flex;justify-content:space-between;gap:12px;margin-bottom:20px}
  .info-row .col{flex:1}
  .lbl{font-size:11px;color:#888;font-weight:600;text-transform:uppercase;
       letter-spacing:.4px;margin-bottom:6px}
  .info-row input, .field input{width:100%;border:2px solid #d0d9e8;border-radius:8px;
                  padding:10px 12px;font-size:15px;font-weight:700;color:#1f4e8c;
                  outline:none;text-align:center;background:#f7f9fc;transition:border-color .2s}
  .info-row input.date-f{color:#333;font-weight:500}
  .info-row input:focus,.field input:focus{border-color:#1f4e8c;
    box-shadow:0 0 0 3px rgba(31,78,140,.12)}
  .field{margin-bottom:16px}
  .field .lbl{display:block;margin-bottom:6px}
  .field input{font-size:22px;font-weight:700;color:#1a1a2e;padding:14px 16px}
  .qty-row{display:flex;justify-content:space-between;align-items:center;
           padding:10px 0;border-top:1px solid #eee;margin-bottom:20px}
  .qty-row span{font-size:13px;color:#666}
  .qty-row strong{font-size:15px;color:#333}
  button{width:100%;background:#1f4e8c;color:#fff;border:none;border-radius:8px;
         padding:16px;font-size:16px;font-weight:700;cursor:pointer;transition:background .2s}
  button:hover{background:#163d70}
  button:disabled{background:#aaa;cursor:not-allowed}
  .status{margin-top:16px;padding:14px 16px;border-radius:8px;font-size:14px;
          font-weight:600;display:none;text-align:center;line-height:1.9}
  .status.ok{background:#e8f5e9;color:#2e7d32;display:block}
  .status.err{background:#fdecea;color:#c62828;display:block}
  .dl-btn{display:inline-block;margin-top:8px;background:#1f4e8c;color:#fff;
          text-decoration:none;padding:10px 24px;border-radius:8px;font-size:14px;font-weight:700}
</style>
</head>
<body>
<div class="card">
  <div class="banner">
    <h1>TRADE TRONICS</h1>
    <p>Générateur de Factures</p>
  </div>
  <div class="body">
    <div class="info-row">
      <div class="col">
        <div class="lbl">Numéro de facture</div>
        <input type="text" id="fa-num" placeholder="FA-0051">
      </div>
      <div class="col">
        <div class="lbl">Date d'émission</div>
        <input type="text" id="fa-date" class="date-f" placeholder="JJ/MM/AAAA">
      </div>
    </div>

    <div class="field">
      <span class="lbl">Montant HT (€)</span>
      <input type="text" id="montant" placeholder="Ex : 46 750" autofocus inputmode="decimal">
    </div>

    <div class="qty-row">
      <span>Quantité estimée</span>
      <strong id="qty-preview">—</strong>
    </div>

    <button id="btn" onclick="generer()">GÉNÉRER LA FACTURE</button>
    <div class="status" id="status"></div>
  </div>
</div>
<script>
// Restaurer le dernier numéro depuis localStorage
const saved = localStorage.getItem('fa_last_num');
if(saved){
  const next = parseInt(saved)+2;
  document.getElementById('fa-num').value = 'FA-'+String(next).padStart(4,'0');
}
document.getElementById('fa-date').value =
  new Date().toLocaleDateString('fr-FR',{day:'2-digit',month:'2-digit',year:'numeric'});

document.getElementById('montant').addEventListener('input', function(){
  const v = parseFloat(this.value.replace(/\s/g,'').replace(',','.'));
  document.getElementById('qty-preview').textContent =
    isNaN(v)||v<=0 ? '—' : Math.max(1,Math.round(v/205));
});
document.getElementById('montant').addEventListener('keydown',e=>{if(e.key==='Enter')generer()});

function generer(){
  const raw = document.getElementById('montant').value.replace(/\s/g,'').replace(',','.');
  const v   = parseFloat(raw);
  if(isNaN(v)||v<=0){ showStatus('Entrez un montant valide.','err'); return; }

  const faNum  = document.getElementById('fa-num').value.trim();
  const faDate = document.getElementById('fa-date').value.trim();
  if(!faNum){ showStatus('Entrez un numéro de facture.','err'); return; }
  if(!faDate){ showStatus('Entrez une date (JJ/MM/AAAA).','err'); return; }

  const btn = document.getElementById('btn');
  btn.disabled=true; btn.textContent='Génération en cours…';

  fetch('/generer',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({montant:v, fa_num:faNum, fa_date:faDate})
  })
  .then(r=>r.blob())
  .then(blob=>{
    const url  = URL.createObjectURL(blob);
    const numStr = faNum.replace(/[^0-9]/g,'');
    localStorage.setItem('fa_last_num', numStr);
    const next = parseInt(numStr)+2;
    document.getElementById('fa-num').value = 'FA-'+String(next).padStart(4,'0');
    document.getElementById('montant').value='';
    document.getElementById('qty-preview').textContent='—';
    const fname = faNum.replace(/[^A-Z0-9\-]/gi,'')+'.pdf';
    const a = document.createElement('a');
    a.href=url; a.download=fname; a.className='dl-btn'; a.textContent='📄 Télécharger '+fname;
    const s = document.getElementById('status');
    s.className='status ok';
    s.innerHTML='✓ Facture générée avec succès !<br>';
    s.appendChild(a);
    btn.disabled=false; btn.textContent='GÉNÉRER LA FACTURE';
  })
  .catch(e=>{ showStatus('Erreur : '+e,'err'); btn.disabled=false; btn.textContent='GÉNÉRER LA FACTURE'; });
}
function showStatus(msg,cls){
  const s=document.getElementById('status'); s.className='status '+cls; s.innerHTML=msg;
}
</script>
</body>
</html>"""

@app.route('/')
def index():
    return Response(HTML, mimetype='text/html')

@app.route('/generer', methods=['POST'])
def generer():
    data  = request.get_json()
    total = float(data['montant'])
    raw   = data.get('fa_num','').upper().replace('FA-','').replace('FA','').strip()
    try:    n = int(raw)
    except: n = 51
    raw_date = data.get('fa_date','').strip()
    try:    fa_date = datetime.datetime.strptime(raw_date, '%d/%m/%Y')
    except: fa_date = datetime.datetime.now()
    qty = max(1, round(total / 205))
    buf = generate_pdf_bytes(n, fa_date, total, qty)
    return send_file(buf, mimetype='application/pdf',
                     as_attachment=True,
                     download_name=f'FA-{n:04d}.pdf')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5050))
    app.run(host='0.0.0.0', port=port)
