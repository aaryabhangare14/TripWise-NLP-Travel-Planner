import io
import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT


def generate_invoice_pdf(booking_data: dict) -> bytes:
    """
    Generates a professional, print-ready travel invoice and e-ticket PDF
    using ReportLab and returns the raw PDF bytes.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#0f172a')
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=colors.HexColor('#0d9488')
    )
    normal_style = ParagraphStyle(
        'NormalText',
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#334155')
    )
    bold_style = ParagraphStyle(
        'BoldText',
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#0f172a')
    )
    table_header_style = ParagraphStyle(
        'TableHeader',
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#ffffff')
    )
    status_badge_style = ParagraphStyle(
        'StatusBadge',
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=12,
        alignment=TA_RIGHT,
        textColor=colors.HexColor('#15803d')
    )

    story = []

    # Extract booking fields
    booking_id = booking_data.get("booking_id", "TW-2026-GOA-8941")
    customer_name = booking_data.get("customer_name", "Ronald")
    destination = booking_data.get("destination", "Goa")
    duration = booking_data.get("duration", 3)
    travelers = booking_data.get("travelers", 2)
    import calendar
    today_dt = datetime.date.today()
    nx_month = 1 if today_dt.month == 12 else today_dt.month + 1
    nx_year = today_dt.year + 1 if today_dt.month == 12 else today_dt.month
    nx_days = calendar.monthrange(nx_year, nx_month)[1]
    def_start = datetime.date(nx_year, nx_month, min(today_dt.day, nx_days))
    def_end = def_start + datetime.timedelta(days=duration - 1)

    start_date = booking_data.get("start_date", def_start.strftime("%d %b %Y"))
    end_date = booking_data.get("end_date", def_end.strftime("%d %b %Y"))
    created_date = booking_data.get("created_date", today_dt.strftime("%d %b %Y"))

    cost = booking_data.get("cost_breakdown", {})
    activities_cost = cost.get("activities", 3000)
    hotel_cost = cost.get("accommodation", 4400)
    food_cost = cost.get("food", 4800)
    transit_cost = cost.get("local_transport", 2250)
    subtotal = activities_cost + hotel_cost + food_cost + transit_cost
    tax = round(subtotal * 0.05)
    grand_total = subtotal + tax

    # 1. Header Banner
    header_data = [
        [
            Paragraph("<b>TripWise</b> Travel AI", title_style),
            Paragraph(f"<b>STATUS: CONFIRMED</b><br/><font color='#64748b' size='8'>Ref: {booking_id}</font>", status_badge_style)
        ],
        [
            Paragraph("Official E-Ticket Confirmation & Tax Invoice", subtitle_style),
            Paragraph(f"<font color='#64748b' size='8'>Issued: {created_date}</font>", ParagraphStyle('R', alignment=TA_RIGHT))
        ]
    ]
    header_table = Table(header_data, colWidths=[320, 220])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#0d9488'), spaceBefore=2, spaceAfter=12))

    # 2. Passenger & Trip Details Card
    info_data = [
        [
            Paragraph("<b>LEAD PASSENGER:</b>", bold_style),
            Paragraph("<b>JOURNEY DETAILS:</b>", bold_style)
        ],
        [
            Paragraph(f"Name: <b>{customer_name}</b><br/>Passengers: <b>{travelers} Traveler(s)</b><br/>Email: <b>ronald.traveler@tripwise.ai</b><br/>Booking Channel: <b>TripWise AI Assistant</b>", normal_style),
            Paragraph(f"Destination: <b>{destination}</b><br/>Duration: <b>{duration} Days ({duration-1 if duration > 1 else 1} Nights)</b><br/>Dates: <b>{start_date} to {end_date}</b><br/>Package: <b>Complete Personalized Itinerary</b>", normal_style)
        ]
    ]
    info_table = Table(info_data, colWidths=[270, 270])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('BOX', (0, 0), (-1, -1), 0.75, colors.HexColor('#e2e8f0')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 14))

    # 3. Confirmed Itinerary Schedule
    story.append(Paragraph("<b>CONFIRMED START-TO-END ITINERARY & ATTRACTION TICKETS</b>", ParagraphStyle('H2', fontName='Helvetica-Bold', fontSize=10.5, textColor=colors.HexColor('#0f172a'), leading=14)))
    story.append(Spacer(1, 6))

    itin_rows = [
        [
            Paragraph("Day / Time", table_header_style),
            Paragraph("Activity & Attraction", table_header_style),
            Paragraph("Category", table_header_style),
            Paragraph("Pass / Ticket", table_header_style)
        ]
    ]

    days_schedule = booking_data.get("itinerary_days", [])
    if not days_schedule:
        # Generate default schedule
        days_schedule = [
            {"day": 1, "title": f"Day 1 – Arrival & {destination} Exploration", "places": [{"name": f"{destination} Iconic Highlights", "time_slot": "Morning", "category": "Sightseeing", "cost": 300}]},
            {"day": 2, "title": f"Day 2 – Scenic Discovery", "places": [{"name": "Scenic Viewpoint & Cultural Tour", "time_slot": "Afternoon", "category": "Nature", "cost": 400}]},
            {"day": 3, "title": f"Day 3 – Souvenirs & Departure", "places": [{"name": "Local Bazaar & Farewell Lunch", "time_slot": "Evening", "category": "Shopping", "cost": 250}]}
        ]

    for day in days_schedule:
        for p in day.get("places", []):
            slot = p.get("time_slot", "Morning")
            name = p.get("name", "Attraction")
            cat = p.get("category", "General").title()
            itin_rows.append([
                Paragraph(f"<b>Day {day['day']}</b><br/><font color='#64748b' size='7'>{slot}</font>", normal_style),
                Paragraph(f"<b>{name}</b><br/><font color='#64748b' size='7.5'>{p.get('description', '')[:75]}...</font>", normal_style),
                Paragraph(cat, normal_style),
                Paragraph("<b>INCLUDED</b><br/><font color='#15803d' size='7'>Confirmed</font>", normal_style)
            ])

    itin_table = Table(itin_rows, colWidths=[75, 275, 95, 95])
    itin_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f172a')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#ffffff'), colors.HexColor('#f8fafc')]),
    ]))
    story.append(itin_table)
    story.append(Spacer(1, 14))

    # 4. Itemized Cost Breakdown Table
    story.append(Paragraph("<b>ITEMIZED TAX INVOICE & PAYMENT RECEIPT</b>", ParagraphStyle('H2', fontName='Helvetica-Bold', fontSize=10.5, textColor=colors.HexColor('#0f172a'), leading=14)))
    story.append(Spacer(1, 6))

    cost_rows = [
        [
            Paragraph("Item Description", table_header_style),
            Paragraph("Units / Duration", table_header_style),
            Paragraph("Rate (INR)", table_header_style),
            Paragraph("Total Amount (INR)", table_header_style)
        ],
        [
            Paragraph("Attraction Passes & Entry Tickets", normal_style),
            Paragraph(f"{travelers} Pax", normal_style),
            Paragraph(f"₹{activities_cost // max(1, travelers):,}", normal_style),
            Paragraph(f"₹{activities_cost:,}", normal_style)
        ],
        [
            Paragraph(f"Accommodation & Resort Stay ({duration-1 if duration > 1 else 1} Nights)", normal_style),
            Paragraph(f"{(travelers + 1) // 2} Room(s)", normal_style),
            Paragraph(f"₹{hotel_cost // max(1, (duration - 1 if duration > 1 else 1)):,}", normal_style),
            Paragraph(f"₹{hotel_cost:,}", normal_style)
        ],
        [
            Paragraph(f"Meals & Culinary Allowance ({duration} Days)", normal_style),
            Paragraph(f"{duration} Days", normal_style),
            Paragraph(f"₹{food_cost // max(1, duration):,}", normal_style),
            Paragraph(f"₹{food_cost:,}", normal_style)
        ],
        [
            Paragraph("Local Sightseeing Transfers & Cabs", normal_style),
            Paragraph(f"{duration} Days", normal_style),
            Paragraph(f"₹{transit_cost // max(1, duration):,}", normal_style),
            Paragraph(f"₹{transit_cost:,}", normal_style)
        ],
        [
            Paragraph("<b>Subtotal (Pre-Tax)</b>", bold_style),
            Paragraph("", normal_style),
            Paragraph("", normal_style),
            Paragraph(f"<b>₹{subtotal:,}</b>", bold_style)
        ],
        [
            Paragraph("Tourism GST / Service Tax (5%)", normal_style),
            Paragraph("5%", normal_style),
            Paragraph("", normal_style),
            Paragraph(f"₹{tax:,}", normal_style)
        ],
        [
            Paragraph("<b>TOTAL AMOUNT PAID</b>", ParagraphStyle('GB', fontName='Helvetica-Bold', fontSize=10, textColor=colors.HexColor('#0d9488'))),
            Paragraph("<b>All Taxes Included</b>", normal_style),
            Paragraph("", normal_style),
            Paragraph(f"<b>₹{grand_total:,}</b>", ParagraphStyle('GBR', fontName='Helvetica-Bold', fontSize=11, textColor=colors.HexColor('#0d9488'), alignment=TA_RIGHT))
        ]
    ]

    cost_table = Table(cost_rows, colWidths=[240, 100, 100, 100])
    cost_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d9488')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f0fdfa')),
        ('LINEABOVE', (0, -1), (-1, -1), 1.5, colors.HexColor('#0d9488')),
    ]))
    story.append(cost_table)
    story.append(Spacer(1, 14))

    # 5. Terms & Verification Seal
    terms_text = (
        "<b>Important Travel Instructions:</b><br/>"
        "• Please carry a valid government-issued Photo ID (Aadhaar, Passport, or Voter ID) for hotel check-in and monument entry.<br/>"
        "• Hotel check-in starts at 12:00 PM; check-out is 11:00 AM. Early check-in is subject to availability.<br/>"
        "• 100% refund available for cancellations made at least 48 hours prior to the journey start date.<br/>"
        "• For 24/7 on-trip assistance, call TripWise Concierge at <b>+91 1800-TRIPWISE</b> or email <b>support@tripwise.ai</b>."
    )
    terms_box = Table([[Paragraph(terms_text, ParagraphStyle('T', fontName='Helvetica', fontSize=7.5, leading=10.5, textColor=colors.HexColor('#64748b')))]], colWidths=[540])
    terms_box.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(terms_box)

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
