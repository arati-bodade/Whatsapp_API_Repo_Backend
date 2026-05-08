#!/usr/bin/env python3
"""
Generate WhatsApp Platform Architecture Diagram as PDF
Using backend venv and reportlab for PDF generation
"""

import os
import sys
from datetime import datetime

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_simple_html_diagram():
    """Create simple HTML diagram without external dependencies"""
    
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WhatsApp Platform Architecture</title>
    <style>
        @page {{
            size: A4 landscape;
            margin: 1cm;
        }}
        
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            padding: 30px;
        }}
        
        .header {{
            background: linear-gradient(135deg, #4CAF50 0%, #2196F3 100%);
            color: white;
            padding: 30px;
            text-align: center;
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 30px;
            border-radius: 10px;
        }}
        
        .architecture-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 30px;
            margin-bottom: 30px;
        }}
        
        .service-card {{
            background: white;
            border: 2px solid #ddd;
            border-radius: 10px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }}
        
        .service-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.15);
        }}
        
        .service-title {{
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 10px;
            color: #333;
        }}
        
        .service-icon {{
            font-size: 36px;
            margin-bottom: 10px;
        }}
        
        .service-details {{
            text-align: left;
            margin-top: 15px;
        }}
        
        .detail-item {{
            margin: 8px 0;
            padding: 8px;
            background: #f8f9fa;
            border-radius: 5px;
            border-left: 4px solid #4CAF50;
        }}
        
        .port {{
            background: #e3f2fd;
            color: #1976d2;
            padding: 4px 8px;
            border-radius: 15px;
            font-weight: bold;
            display: inline-block;
            margin: 5px 0;
        }}
        
        .tech {{
            background: #fff3e0;
            color: #f57c00;
            padding: 4px 8px;
            border-radius: 15px;
            font-size: 12px;
            display: inline-block;
            margin: 2px;
        }}
        
        .connections {{
            grid-column: 1 / -1;
            display: flex;
            justify-content: space-around;
            align-items: center;
            margin: 30px 0;
            padding: 20px;
            background: #f5f5f5;
            border-radius: 10px;
        }}
        
        .connection-arrow {{
            text-align: center;
            font-size: 24px;
            color: #666;
        }}
        
        .footer {{
            margin-top: 30px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
            text-align: center;
            color: #666;
            font-size: 14px;
        }}
        
        .frontend {{ border-color: #1976d2; }}
        .backend {{ border-color: #388e3c; }}
        .engine {{ border-color: #0d47a1; }}
        
        @media print {{
            body {{ background: white; }}
            .container {{ box-shadow: none; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            🏗️ WhatsApp Platform Architecture Diagram
            <div style="font-size: 14px; font-weight: normal; margin-top: 10px;">
                Three-Service Microservices Architecture | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </div>
        </div>
        
        <div class="architecture-grid">
            <!-- Frontend Service -->
            <div class="service-card frontend">
                <div class="service-icon">📱</div>
                <div class="service-title">Frontend Service</div>
                <div class="service-details">
                    <div class="detail-item">
                        <strong>Port:</strong> <span class="port">3000</span>
                    </div>
                    <div class="detail-item">
                        <strong>Technology:</strong> <span class="tech">Next.js 16.1.1</span>
                    </div>
                    <div class="detail-item">
                        <strong>Language:</strong> <span class="tech">TypeScript</span>
                    </div>
                    <div class="detail-item">
                        <strong>Purpose:</strong> User Interface & API Proxy
                    </div>
                </div>
            </div>
            
            <!-- Backend Service -->
            <div class="service-card backend">
                <div class="service-icon">⚙️</div>
                <div class="service-title">Backend Service</div>
                <div class="service-details">
                    <div class="detail-item">
                        <strong>Port:</strong> <span class="port">8000</span>
                    </div>
                    <div class="detail-item">
                        <strong>Technology:</strong> <span class="tech">Python FastAPI</span>
                    </div>
                    <div class="detail-item">
                        <strong>Database:</strong> <span class="tech">PostgreSQL</span>
                    </div>
                    <div class="detail-item">
                        <strong>Purpose:</strong> Business Logic & Data Management
                    </div>
                </div>
            </div>
            
            <!-- WhatsApp Engine -->
            <div class="service-card engine">
                <div class="service-icon">🔧</div>
                <div class="service-title">WhatsApp Engine</div>
                <div class="service-details">
                    <div class="detail-item">
                        <strong>Port:</strong> <span class="port">3002</span>
                    </div>
                    <div class="detail-item">
                        <strong>Technology:</strong> <span class="tech">Node.js + Baileys</span>
                    </div>
                    <div class="detail-item">
                        <strong>Library:</strong> <span class="tech">WhatsApp Web API</span>
                    </div>
                    <div class="detail-item">
                        <strong>Purpose:</strong> Direct WhatsApp Integration
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Connections -->
        <div class="connections">
            <div class="connection-arrow">↕️</div>
            <div class="connection-arrow">↔️</div>
            <div class="connection-arrow">↕️</div>
            <div class="connection-arrow">↔️</div>
        </div>
        
        <!-- Data Flow Legend -->
        <div class="connections">
            <div style="text-align: center; width: 100%;">
                <strong>📊 Data Flow</strong><br>
                📱 Frontend ↔️ ⚙️ Backend ↔️ 🔧 Engine ↔️ 💬 WhatsApp
            </div>
        </div>
        
        <!-- Architecture Benefits -->
        <div class="footer">
            <strong>🎯 Architecture Benefits:</strong><br>
            • <strong>Scalability:</strong> Each service can scale independently<br>
            • <strong>Maintainability:</strong> Clear code boundaries and responsibilities<br>
            • <strong>Reliability:</strong> Fault isolation between services<br>
            • <strong>Technology:</strong> Best tools for each service's purpose<br>
            • <strong>Development:</strong> Teams can work on services independently<br><br>
            <em>Generated using Python Backend Environment</em>
        </div>
    </div>
</body>
</html>
    """
    
    return html_content

def generate_pdf_with_reportlab():
    """Generate PDF using ReportLab (built-in Python PDF library)"""
    
    try:
        from reportlab.lib.pagesizes import letter, landscape
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        REPORTLAB_AVAILABLE = True
    except ImportError:
        REPORTLAB_AVAILABLE = False
    
    if not REPORTLAB_AVAILABLE:
        print("⚠️  ReportLab not available. Creating HTML fallback...")
        return create_simple_html_diagram()
    
    # Create PDF document
    doc = SimpleDocTemplate(
        "WHATSAPP_PLATFORM_ARCHITECTURE.pdf",
        pagesize=landscape(letter),
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30
    )
    
    # Get styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=20,
        alignment=1,  # Center
        textColor=colors.white
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=18,
        spaceAfter=12,
        textColor=colors.darkblue
    )
    
    normal_style = styles['Normal']
    
    # Build content
    story = []
    
    # Header
    header_data = [[
        ["🏗️ WHATSAPP PLATFORM ARCHITECTURE"],
        ["Three-Service Microservices Architecture"]
    ]]
    
    header_table = Table(header_data, colWidths=[6*inch, 4*inch])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 1), colors.Color(0.2, 0.5, 0.8, 1)),
        ('TEXTCOLOR', (0, 0), (0, 1), colors.whitesmoke),
        ('ALIGN', (0, 0), 'CENTER'),
        ('FONTNAME', (0, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), 16),
        ('BOTTOMPADDING', (0, 0), 20),
    ]))
    
    story.append(header_table)
    story.append(Spacer(1, 20))
    
    # Services Grid
    services_data = [
        ['📱 Frontend Service', '⚙️ Backend Service', '🔧 WhatsApp Engine'],
        [
            'Port: 3000\nNext.js 16.1.1\nTypeScript\nUser Interface & API Proxy',
            'Port: 8000\nPython FastAPI\nPostgreSQL\nBusiness Logic & Data Management',
            'Port: 3002\nNode.js + Baileys\nWhatsApp Web API\nDirect WhatsApp Integration'
        ]
    ]
    
    services_table = Table(services_data, colWidths=[4*inch, 4*inch, 4*inch])
    services_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.Color(0.9, 0.95, 0.98, 1)),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), 'CENTER'),
        ('VALIGN', (0, 0), 'TOP'),
        ('FONTNAME', (0, 0), 'Helvetica'),
        ('FONTSIZE', (0, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('TOPPADDING', (0, 0), 12),
        ('BOTTOMPADDING', (0, 0), 12),
    ]))
    
    story.append(services_table)
    story.append(Spacer(1, 20))
    
    # Data Flow
    story.append(Paragraph("📊 Data Flow", heading_style))
    data_flow = Paragraph(
        "📱 Frontend ↔️ ⚙️ Backend ↔️ 🔧 Engine ↔️ 💬 WhatsApp Network",
        normal_style
    )
    story.append(data_flow)
    story.append(Spacer(1, 20))
    
    # Architecture Benefits
    story.append(Paragraph("🎯 Architecture Benefits", heading_style))
    
    benefits = [
        "• Scalability: Each service can scale independently",
        "• Maintainability: Clear code boundaries and responsibilities", 
        "• Reliability: Fault isolation between services",
        "• Technology: Best tools for each service's purpose",
        "• Development: Teams can work on services independently"
    ]
    
    for benefit in benefits:
        story.append(Paragraph(benefit, normal_style))
        story.append(Spacer(1, 6))
    
    # Footer
    story.append(Spacer(1, 20))
    footer = Paragraph(
        f"Generated using Python Backend Environment\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        normal_style
    )
    story.append(footer)
    
    # Build PDF
    doc.build(story)
    return "WHATSAPP_PLATFORM_ARCHITECTURE.pdf"

def main():
    """Main function using backend environment"""
    
    print("🚀 WHATSAPP PLATFORM ARCHITECTURE PDF GENERATOR")
    print("=" * 60)
    print("Using Python Backend Environment...")
    
    try:
        # Try to generate PDF with ReportLab
        result_file = generate_pdf_with_reportlab()
        
        if result_file.endswith('.pdf'):
            print(f"✅ PDF generated successfully: {result_file}")
        else:
            print(f"✅ HTML generated as fallback: {result_file}")
            
    except Exception as e:
        print(f"❌ Error generating PDF: {e}")
        print("📋 Creating HTML fallback...")
        
        # Create HTML fallback
        html_content = create_simple_html_diagram()
        html_file = "WHATSAPP_PLATFORM_ARCHITECTURE.html"
        
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        result_file = html_file
        print(f"✅ HTML fallback created: {result_file}")
    
    print("\n" + "=" * 60)
    print("🎉 ARCHITECTURE DIAGRAM GENERATION COMPLETED!")
    print("=" * 60)
    
    print(f"\n📋 Generated File: {result_file}")
    print("\n📋 Diagram Contents:")
    print("• Three-service architecture visualization")
    print("• Service connections and data flow")
    print("• Technology stack information")
    print("• Port configurations")
    print("• Architecture benefits")
    
    print(f"\n🚀 Next Steps:")
    print(f"• Open {result_file} to view the diagram")
    print("• Share with team for architecture review")
    print("• Use for documentation and planning")

if __name__ == "__main__":
    main()
