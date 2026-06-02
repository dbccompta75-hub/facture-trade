import os, datetime
from io import BytesIO
from flask import Flask, request, jsonify, Response, send_file

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER

app = Flask(__name__)

MOIS = ['','janvier','février','mars','avril','mai','juin',
        'juillet','août','septembre','octobre','novembre','décembre']

def P(text, size=8, align=TA_LEFT, bold=False, color=colors.black):
    return Paragraph(text, ParagraphStyle('x',
        fontName='Helvetica-Bold' if bold else 'Helvetica',
        fontSize=size, leading=size+2, alignment=align, textColor=color))

def fmt(n):
    return f"{n:,.2f}".replace(',', ' ').replace('.', ',') + ' €'

def generate_pdf_bytes(fa_num, fa_date, total_ht, qty):
    RB  = colors.HexColor('#1f4e8c')
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=12*mm, rightMargin=12*mm,
                            topMargin=12*mm, bottomMargin=18*mm)
    s = []
    s += [P('TRADE TRONICS',22,TA_CENTER,True,RB),
          P("Commerce de gros – Électronique d'occasion",8,TA_CENTER,color=colors.grey),
          P('FACTURE',11,TA_CENTER),
          P(f'FA-{fa_num:04d}',18,TA_CENTER,True,RB),
          P(f'{fa_date.day} {MOIS[fa_date.month]} {fa_date.year}',9,TA_CENTER),
          Spacer(1,6)]
    em = ("<b>TRADE TRONICS</b><br/>SASU au capital de 500,00 €<br/>"
          "Bureau 326, 78 Avenue des Champs Élysées<br/>"
          "75008 Paris, France<br/>SIRET : 934 635 301 00013<br/>TVA : FR53934635301")
    de = ("<b>GATE TECHNOLOGY</b><br/>59 Avenue du Général de Gaulle<br/>"
          "Centre Commercial Westfield Rosny 2<br/>"
          "93110 Rosny-sous-Bois, France<br/>SIRET : 938 435 351 00011<br/>TVA : FR84938435351")
    hdr = Table([[P('ÉMETTEUR',9,bold=True,color=colors.white),
                  P('DESTINATAIRE',9,bold=True,color=colors.white)],
                 [P(em,8),P(de,8)]], colWidths=[92*mm,92*mm])
    hdr.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),RB),('BOX',(0,0),(-1,-1),.5,colors.grey),
        ('INNERGRID',(0,0),(-1,-1),.3,colors.grey),
        ('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),
        ('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4)]))
    s += [hdr, Spacer(1,4)]
    ech = fa_date + datetime.timedelta(days=30)
    info = Table([[P("DATE D'ÉMISSION",8,bold=True),P('ÉCHÉANCE',8,bold=True),
                   P('MODE DE RÈGLEMENT',8,bold=True)],
                  [P(fa_date.strftime('%d/%m/%Y'),9,bold=True),
                   P(ech.strftime('%d/%m/%Y'),9,bold=True),
                   P('Virement bancaire',9)]], colWidths=[61*mm,61*mm,62*mm])
    info.setStyle(TableStyle([
        ('BOX',(0,0),(-1,-1),.5,colors.grey),('INNERGRID',(0,0),(-1,-1),.3,colors.grey),
        ('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),
        ('TOPPADDING',(0,0),(-1,-1),3),('BOTTOMPADDING',(0,0),(-1,-1),3)]))
    s += [info, Spacer(1,8), P('RÉCAPITULATIF',12,TA_LEFT,True,RB), Spacer(1,4)]
    sd = [[P('CATÉGORIE',10,bold=True,color=colors.white),
           P('QTÉ',10,bold=True,color=colors.white,align=TA_CENTER),
           P('TOTAL HT',10,bold=True,color=colors.white,align=TA_RIGHT)],
          [P('Apple iPhone',10),P(str(qty),10,TA_CENTER),P(fmt(total_ht),10,TA_RIGHT,bold=True)],
          [P('TOTAL',11,bold=True),P(str(qty),11,TA_CENTER,True),P(fmt(total_ht),11,TA_RIGHT,True,RB)]]
    st = Table(sd, colWidths=[120*mm,30*mm,36*mm])
    st.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),RB),
        ('BACKGROUND',(0,-1),(-1,-1),colors.HexColor('#eef2f8')),
        ('LINEBELOW',(0,0),(-1,-1),.3,colors.lightgrey),
        ('LINEABOVE',(0,-1),(-1,-1),.5,colors.grey),
        ('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),
        ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
    s += [st, Spacer(1,10),
          P("<i>Voir annexe pour les détails.</i>",9,TA_CENTER,color=colors.grey)]
    def footer(c,d):
        c.setFont('Helvetica',7); c.setFillColor(colors.grey)
        c.drawCentredString(A4[0]/2,12*mm,'Voir annexe pour les détails.')
        c.drawCentredString(A4[0]/2,9*mm,'TRADE TRONICS - SASU')
        c.drawCentredString(A4[0]/2,6*mm,
            'RCS Paris 934 635 301 - SIRET 934 635 301 00013 - TVA FR53934635301')
        c.drawCentredString(A4[0]/2,3*mm,
            'Bureau 326, 78 Avenue des Champs Elysees, 75008 Paris')
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
