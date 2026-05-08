
import sys
import os
from datetime import datetime
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors

def create_pdf():
    doc = SimpleDocTemplate("WHATSAPP_PLATFORM_ARCHITECTURE.pdf", pagesize=landscape(letter))
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=24, textColor=colors.white, alignment=1)
    title = Paragraph("🏗️ WHATSAPP PLATFORM ARCHITECTURE", title_style)
    
    # Services
    services_data = [
        ['Service', 'Port', 'Technology', 'Purpose'],
        ['Frontend', '3000', 'Next.js 16.1.1', 'User Interface & API Proxy'],
        ['Backend', '8000', 'Python FastAPI', 'Business Logic & Data Management'],
        ['WhatsApp Engine', '3002', 'Node.js + Baileys', 'Direct WhatsApp Integration']
    ]
    
    services_table = Table(services_data, colWidths=[2*inch, 1*inch, 3*inch, 3*inch])
    services_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.Color(0.9, 0.95, 0.98, 1)),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), 'CENTER'),
        ('FONTNAME', (0, 0), 'Helvetica'),
        ('FONTSIZE', (0, 0), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('TOPPADDING', (0, 0), 12),
        ('BOTTOMPADDING', (0, 0), 12),
    ]))
    
    # Data Flow
    normal_style = styles['Normal']
    data_flow = Paragraph("📊 Data Flow: 📱 Frontend ↔️ ⚙️ Backend ↔️ 🔧 Engine ↔️ 💬 WhatsApp", normal_style)
    
    # Build PDF
    story = [title, Spacer(1, 20), services_table, Spacer(1, 20), data_flow, Spacer(1, 20)]
    
    # Footer
    footer = Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", normal_style)
    story.append(footer)
    
    doc.build(story)
    return "WHATSAPP_PLATFORM_ARCHITECTURE.pdf"

if __name__ == "__main__":
    try:
        pdf_file = create_pdf()
        print(f"✅ PDF generated: {pdf_file}")
        if os.path.exists(pdf_file):
            size = os.path.getsize(pdf_file)
            print(f"📄 File size: {size} bytes")
    except Exception as e:
        print(f"❌ Error: {e}")
