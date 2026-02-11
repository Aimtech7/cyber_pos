from datetime import datetime
from typing import List, Dict, Any
from decimal import Decimal
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from io import BytesIO


def generate_receipt_pdf(
    transaction_data: Dict[str, Any],
    business_name: str = "CyberCafe POS Pro"
) -> BytesIO:
    """
    Generate a PDF receipt
    
    Args:
        transaction_data: Dictionary containing transaction details
        business_name: Name of the business
    
    Returns:
        BytesIO object containing PDF data
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title style
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    # Add business name
    elements.append(Paragraph(business_name, title_style))
    elements.append(Spacer(1, 0.2 * inch))
    
    # Receipt details
    receipt_info = [
        ['Receipt #:', str(transaction_data.get('transaction_number', 'N/A'))],
        ['Date:', transaction_data.get('date', datetime.now().strftime('%Y-%m-%d %H:%M'))],
        ['Attendant:', transaction_data.get('attendant_name', 'N/A')],
    ]
    
    info_table = Table(receipt_info, colWidths=[2*inch, 3*inch])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.grey),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 0.3 * inch))
    
    # Items table
    items_data = [['Description', 'Qty', 'Price', 'Total']]
    for item in transaction_data.get('items', []):
        items_data.append([
            item['description'],
            str(item['quantity']),
            f"KES {item['unit_price']:.2f}",
            f"KES {item['total_price']:.2f}"
        ])
    
    items_table = Table(items_data, colWidths=[2.5*inch, 0.8*inch, 1*inch, 1*inch])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 0.2 * inch))
    
    # Totals
    totals_data = [
        ['Subtotal:', f"KES {transaction_data.get('total_amount', 0):.2f}"],
        ['Discount:', f"KES {transaction_data.get('discount_amount', 0):.2f}"],
        ['TOTAL:', f"KES {transaction_data.get('final_amount', 0):.2f}"],
    ]
    
    totals_table = Table(totals_data, colWidths=[3.5*inch, 1.5*inch])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 2), (-1, 2), 12),
        ('LINEABOVE', (0, 2), (-1, 2), 2, colors.black),
    ]))
    elements.append(totals_table)
    elements.append(Spacer(1, 0.2 * inch))
    
    # Payment method
    payment_info = [
        ['Payment Method:', transaction_data.get('payment_method', 'N/A').upper()],
    ]
    if transaction_data.get('mpesa_code'):
        payment_info.append(['M-Pesa Code:', transaction_data['mpesa_code']])
    
    payment_table = Table(payment_info, colWidths=[2*inch, 3*inch])
    payment_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
    ]))
    elements.append(payment_table)
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_thermal_receipt(
    transaction_data: Dict[str, Any],
    business_name: str = "CyberCafe POS Pro"
) -> str:
    """
    Generate ESC/POS commands for thermal printer
    
    Args:
        transaction_data: Dictionary containing transaction details
        business_name: Name of the business
    
    Returns:
        String containing ESC/POS commands
    """
    # ESC/POS commands
    ESC = '\x1b'
    INIT = f'{ESC}@'  # Initialize printer
    CENTER = f'{ESC}a\x01'  # Center alignment
    LEFT = f'{ESC}a\x00'  # Left alignment
    BOLD_ON = f'{ESC}E\x01'  # Bold on
    BOLD_OFF = f'{ESC}E\x00'  # Bold off
    CUT = f'{ESC}d\x03{ESC}i'  # Feed and cut
    
    receipt = INIT
    receipt += CENTER + BOLD_ON + business_name + BOLD_OFF + '\n\n'
    receipt += LEFT
    receipt += f"Receipt #: {transaction_data.get('transaction_number', 'N/A')}\n"
    receipt += f"Date: {transaction_data.get('date', datetime.now().strftime('%Y-%m-%d %H:%M'))}\n"
    receipt += f"Attendant: {transaction_data.get('attendant_name', 'N/A')}\n"
    receipt += '--------------------------------\n'
    
    # Items
    for item in transaction_data.get('items', []):
        desc = item['description'][:20]  # Truncate long descriptions
        qty = item['quantity']
        total = item['total_price']
        receipt += f"{desc}\n"
        receipt += f"  {qty} x {item['unit_price']:.2f} = {total:.2f}\n"
    
    receipt += '--------------------------------\n'
    receipt += f"Subtotal:     KES {transaction_data.get('total_amount', 0):.2f}\n"
    receipt += f"Discount:     KES {transaction_data.get('discount_amount', 0):.2f}\n"
    receipt += BOLD_ON + f"TOTAL:        KES {transaction_data.get('final_amount', 0):.2f}\n" + BOLD_OFF
    receipt += '--------------------------------\n'
    receipt += f"Payment: {transaction_data.get('payment_method', 'N/A').upper()}\n"
    
    if transaction_data.get('mpesa_code'):
        receipt += f"M-Pesa: {transaction_data['mpesa_code']}\n"
    
    receipt += '\n' + CENTER + 'Thank you for your business!\n\n'
    receipt += CUT
    
    return receipt
