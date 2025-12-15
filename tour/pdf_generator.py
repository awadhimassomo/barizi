"""
PDF Generator for Tour Itineraries using ReportLab
"""
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from io import BytesIO
import json
from datetime import datetime


# Brand colors
BURNT_ORANGE = colors.HexColor('#CC5500')
BLACK = colors.HexColor('#000000')
WHITE = colors.HexColor('#FFFFFF')
LIGHT_GRAY = colors.HexColor('#F5F5F5')
DARK_GRAY = colors.HexColor('#333333')


def get_custom_styles():
    """Create custom paragraph styles for the PDF."""
    styles = getSampleStyleSheet()
    
    # Title style
    styles.add(ParagraphStyle(
        name='CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=BLACK,
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    ))
    
    # Subtitle style
    styles.add(ParagraphStyle(
        name='Subtitle',
        parent=styles['Normal'],
        fontSize=14,
        textColor=DARK_GRAY,
        spaceAfter=10,
        alignment=TA_CENTER,
    ))
    
    # Section header
    styles.add(ParagraphStyle(
        name='SectionHeader',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=BURNT_ORANGE,
        spaceBefore=20,
        spaceAfter=10,
        fontName='Helvetica-Bold'
    ))
    
    # Day header
    styles.add(ParagraphStyle(
        name='DayHeader',
        parent=styles['Heading3'],
        fontSize=14,
        textColor=WHITE,
        spaceBefore=15,
        spaceAfter=5,
        fontName='Helvetica-Bold',
        backColor=BLACK,
        borderPadding=10,
    ))
    
    # Normal text
    styles.add(ParagraphStyle(
        name='CustomBody',
        parent=styles['Normal'],
        fontSize=10,
        textColor=DARK_GRAY,
        spaceAfter=6,
        leading=14,
    ))
    
    # Small text
    styles.add(ParagraphStyle(
        name='SmallText',
        parent=styles['Normal'],
        fontSize=8,
        textColor=DARK_GRAY,
        spaceAfter=4,
    ))
    
    # Price text
    styles.add(ParagraphStyle(
        name='PriceText',
        parent=styles['Normal'],
        fontSize=12,
        textColor=BURNT_ORANGE,
        fontName='Helvetica-Bold',
        alignment=TA_RIGHT,
    ))
    
    return styles


def generate_itinerary_pdf(tour_request, itinerary_data):
    """
    Generate a professional PDF itinerary.
    
    Args:
        tour_request: TourRequest model instance
        itinerary_data: Dict containing the generated itinerary
    
    Returns:
        BytesIO buffer containing the PDF
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1*cm,
        leftMargin=1*cm,
        topMargin=1.5*cm,
        bottomMargin=1.5*cm
    )
    
    styles = get_custom_styles()
    story = []
    
    # ═══════════════════════════════════════════════════════════════
    # HEADER / TITLE PAGE
    # ═══════════════════════════════════════════════════════════════
    
    # Company name / branding
    story.append(Spacer(1, 1*cm))
    story.append(Paragraph("BARIZI TOURS", styles['CustomTitle']))
    story.append(Paragraph("Your Safari Adventure Awaits", styles['Subtitle']))
    story.append(Spacer(1, 0.5*cm))
    
    # Horizontal line
    story.append(HRFlowable(width="100%", thickness=2, color=BURNT_ORANGE))
    story.append(Spacer(1, 0.5*cm))
    
    # Tour title
    tour_title = f"{tour_request.duration_days}-Day {tour_request.get_tour_type_display()} Safari"
    story.append(Paragraph(tour_title, styles['CustomTitle']))
    
    # Client info box
    client_info = f"""
    <b>Prepared for:</b> {tour_request.client_name}<br/>
    <b>Email:</b> {tour_request.client_email}<br/>
    <b>Travel Dates:</b> {tour_request.start_date.strftime('%B %d, %Y')} - {tour_request.end_date.strftime('%B %d, %Y')}<br/>
    <b>Travelers:</b> {tour_request.num_adults} Adult(s), {tour_request.num_children} Child(ren)
    """
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph(client_info, styles['CustomBody']))
    story.append(Spacer(1, 0.5*cm))
    
    # Summary
    if itinerary_data.get('summary'):
        story.append(Paragraph("Tour Overview", styles['SectionHeader']))
        story.append(Paragraph(itinerary_data['summary'], styles['CustomBody']))
    
    story.append(Spacer(1, 0.5*cm))
    
    # ═══════════════════════════════════════════════════════════════
    # DAY-BY-DAY ITINERARY
    # ═══════════════════════════════════════════════════════════════
    
    story.append(Paragraph("Day-by-Day Itinerary", styles['SectionHeader']))
    story.append(HRFlowable(width="100%", thickness=1, color=LIGHT_GRAY))
    
    for day in itinerary_data.get('days', []):
        # Day header with background
        day_num = day.get('day', '')
        day_title = day.get('title', '')
        destination = day.get('destination', '')
        
        # Create day header table for better styling
        day_header_data = [[
            Paragraph(f"<font color='#CC5500'>DAY {day_num}</font>", styles['CustomBody']),
            Paragraph(f"<b>{day_title}</b>", styles['CustomBody']),
            Paragraph(destination, styles['SmallText'])
        ]]
        day_header_table = Table(day_header_data, colWidths=[1.5*cm, 10*cm, 5*cm])
        day_header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), BLACK),
            ('TEXTCOLOR', (0, 0), (-1, -1), WHITE),
            ('ALIGN', (0, 0), (0, 0), 'CENTER'),
            ('ALIGN', (1, 0), (1, 0), 'LEFT'),
            ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 10),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ]))
        story.append(Spacer(1, 0.3*cm))
        story.append(day_header_table)
        
        # Activities
        activities = day.get('activities', [])
        if activities:
            story.append(Spacer(1, 0.2*cm))
            story.append(Paragraph("<b>Activities:</b>", styles['CustomBody']))
            for activity in activities:
                act_name = activity.get('name', '')
                act_time = activity.get('time', '')
                act_cost = activity.get('cost_per_person', '')
                time_str = f" ({act_time})" if act_time else ""
                cost_str = f" - ${act_cost}/pp" if act_cost else ""
                story.append(Paragraph(f"• {act_name}{time_str}{cost_str}", styles['SmallText']))
        
        # Accommodation
        accommodation = day.get('accommodation', {})
        if accommodation:
            story.append(Spacer(1, 0.2*cm))
            acc_name = accommodation.get('name', 'TBA')
            meal_plan = accommodation.get('meal_plan', '')
            acc_cost = accommodation.get('cost_per_person', '')
            meal_str = f" ({meal_plan})" if meal_plan else ""
            cost_str = f" - ${acc_cost}/pp" if acc_cost else ""
            story.append(Paragraph(f"<b>Accommodation:</b> {acc_name}{meal_str}{cost_str}", styles['CustomBody']))
        
        # Transport
        transport = day.get('transport', {})
        if transport:
            trans_desc = transport.get('description', '')
            distance = transport.get('distance_km', '')
            dist_str = f" (~{distance} km)" if distance else ""
            if trans_desc:
                story.append(Paragraph(f"<b>Transport:</b> {trans_desc}{dist_str}", styles['SmallText']))
        
        # Meals
        meals = day.get('meals_included', [])
        if meals:
            meals_str = ', '.join(meals)
            story.append(Paragraph(f"<b>Meals:</b> {meals_str}", styles['SmallText']))
        
        # Tips
        tips = day.get('tips', '')
        if tips:
            story.append(Paragraph(f"<i>💡 {tips}</i>", styles['SmallText']))
    
    # ═══════════════════════════════════════════════════════════════
    # COST BREAKDOWN
    # ═══════════════════════════════════════════════════════════════
    
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph("Cost Breakdown", styles['SectionHeader']))
    story.append(HRFlowable(width="100%", thickness=1, color=LIGHT_GRAY))
    
    cost_breakdown = itinerary_data.get('cost_breakdown', {})
    if cost_breakdown:
        cost_data = []
        
        if cost_breakdown.get('accommodation_total'):
            cost_data.append(['Accommodation', f"${cost_breakdown['accommodation_total']:,.0f}"])
        if cost_breakdown.get('activities_total'):
            cost_data.append(['Activities & Excursions', f"${cost_breakdown['activities_total']:,.0f}"])
        if cost_breakdown.get('transport_total'):
            cost_data.append(['Transport', f"${cost_breakdown['transport_total']:,.0f}"])
        if cost_breakdown.get('park_fees_total'):
            cost_data.append(['Park & Conservation Fees', f"${cost_breakdown['park_fees_total']:,.0f}"])
        
        # Subtotal
        if cost_breakdown.get('subtotal_per_person'):
            cost_data.append(['', ''])  # Spacer row
            cost_data.append(['Subtotal (per person)', f"${cost_breakdown['subtotal_per_person']:,.0f}"])
        
        # Markup info (only show to operator, not client)
        # Skip markup in client PDF
        
        # Totals
        if cost_breakdown.get('total_per_person'):
            cost_data.append(['', ''])  # Spacer row
            cost_data.append(['TOTAL PER PERSON', f"${cost_breakdown['total_per_person']:,.0f}"])
        if cost_breakdown.get('total_all_travelers'):
            cost_data.append(['TOTAL (ALL TRAVELERS)', f"${cost_breakdown['total_all_travelers']:,.0f}"])
        
        if cost_data:
            cost_table = Table(cost_data, colWidths=[12*cm, 5*cm])
            cost_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('FONTNAME', (0, -2), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('TEXTCOLOR', (0, -2), (-1, -1), BURNT_ORANGE),
                ('LINEABOVE', (0, -2), (-1, -2), 1, BLACK),
                ('PADDING', (0, 0), (-1, -1), 5),
            ]))
            story.append(cost_table)
    
    # ═══════════════════════════════════════════════════════════════
    # WHAT TO PACK
    # ═══════════════════════════════════════════════════════════════
    
    what_to_pack = itinerary_data.get('what_to_pack', [])
    if what_to_pack:
        story.append(Spacer(1, 0.5*cm))
        story.append(Paragraph("Packing Checklist", styles['SectionHeader']))
        story.append(HRFlowable(width="100%", thickness=1, color=LIGHT_GRAY))
        
        # Create 3-column layout for packing items
        pack_rows = []
        row = []
        for i, item in enumerate(what_to_pack):
            row.append(f"☐ {item}")
            if len(row) == 3:
                pack_rows.append(row)
                row = []
        if row:  # Add remaining items
            while len(row) < 3:
                row.append('')
            pack_rows.append(row)
        
        if pack_rows:
            pack_table = Table(pack_rows, colWidths=[5.5*cm, 5.5*cm, 5.5*cm])
            pack_table.setStyle(TableStyle([
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('PADDING', (0, 0), (-1, -1), 4),
            ]))
            story.append(pack_table)
    
    # ═══════════════════════════════════════════════════════════════
    # FOOTER / TERMS
    # ═══════════════════════════════════════════════════════════════
    
    story.append(Spacer(1, 1*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=BURNT_ORANGE))
    story.append(Spacer(1, 0.3*cm))
    
    footer_text = f"""
    <b>Barizi Tours</b> | Your Trusted Safari Partner<br/>
    Generated on: {datetime.now().strftime('%B %d, %Y at %H:%M')}<br/>
    <i>This itinerary is subject to availability. Prices valid for 7 days from generation date.</i>
    """
    story.append(Paragraph(footer_text, styles['SmallText']))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer


def generate_operator_pdf(tour_request, itinerary_data):
    """
    Generate a PDF with operator-specific details (including profit margins).
    This is for internal use only.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1*cm,
        leftMargin=1*cm,
        topMargin=1.5*cm,
        bottomMargin=1.5*cm
    )
    
    styles = get_custom_styles()
    story = []
    
    # Header
    story.append(Paragraph("OPERATOR COPY - CONFIDENTIAL", styles['CustomTitle']))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.red))
    story.append(Spacer(1, 0.5*cm))
    
    # Client & Request info
    info_text = f"""
    <b>Request ID:</b> #{tour_request.pk}<br/>
    <b>Client:</b> {tour_request.client_name} ({tour_request.client_email})<br/>
    <b>Dates:</b> {tour_request.start_date} - {tour_request.end_date}<br/>
    <b>Tour Type:</b> {tour_request.get_tour_type_display()}<br/>
    <b>Travelers:</b> {tour_request.num_adults}A + {tour_request.num_children}C<br/>
    <b>Markup Applied:</b> {tour_request.markup_percentage}%
    """
    story.append(Paragraph(info_text, styles['CustomBody']))
    story.append(Spacer(1, 0.5*cm))
    
    # Financial summary
    story.append(Paragraph("Financial Summary", styles['SectionHeader']))
    
    cost_breakdown = itinerary_data.get('cost_breakdown', {})
    if cost_breakdown:
        fin_data = [
            ['Item', 'Amount'],
            ['Base Cost (per person)', f"${cost_breakdown.get('subtotal_per_person', 0):,.2f}"],
            ['Your Markup (%)', f"{cost_breakdown.get('operator_markup_percentage', 0)}%"],
            ['Markup Amount (per person)', f"${cost_breakdown.get('operator_markup_per_person', 0):,.2f}"],
            ['Final Price (per person)', f"${cost_breakdown.get('total_per_person', 0):,.2f}"],
            ['', ''],
            ['Total Markup (All Travelers)', f"${cost_breakdown.get('operator_markup_total', 0):,.2f}"],
            ['GRAND TOTAL', f"${cost_breakdown.get('total_all_travelers', 0):,.2f}"],
            ['', ''],
            ['YOUR PROFIT', f"${cost_breakdown.get('operator_markup_total', 0):,.2f}"],
        ]
        
        fin_table = Table(fin_data, colWidths=[10*cm, 6*cm])
        fin_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), BLACK),
            ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 14),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.green),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#E8F5E9')),
            ('LINEABOVE', (0, -3), (-1, -3), 1, BLACK),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, LIGHT_GRAY),
        ]))
        story.append(fin_table)
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer
