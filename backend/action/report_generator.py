from concurrent.futures import ThreadPoolExecutor
from langchain_google_genai import ChatGoogleGenerativeAI
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from backend.prompts.report_generator_prompts import feedback_themes_prompt,executive_summary_prompt,CLASSIFY_SENTIMENTS_PROMPT 

from collections import Counter
from datetime import datetime
import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
from collections import Counter
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    PageBreak
)

from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import inch
from reportlab.lib.colors import darkblue
from reportlab.lib.styles import ParagraphStyle
import json
import os

llm1 = ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite",
    api_key=os.getenv("GOOGLE_API_KEY_1"),
    temperature=0
)

llm2 = ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite",
    api_key=os.getenv("GOOGLE_API_KEY_2"),
    temperature=0
)


def classify_sentiments(analyst_output: list[dict]) -> list[str]:

    mid = len(analyst_output) // 2

    batch1 = analyst_output[:mid]
    batch2 = analyst_output[mid:]

    reasons1 = [item["reason"] for item in batch1]
    reasons2 = [item["reason"] for item in batch2]

    prompt = CLASSIFY_SENTIMENTS_PROMPT

    with ThreadPoolExecutor(max_workers=2) as executor:

        future1 = executor.submit(
            llm1.invoke,
            prompt + "\n\nInput:\n" + json.dumps(reasons1, indent=2)
        )

        future2 = executor.submit(
            llm2.invoke,
            prompt + "\n\nInput:\n" + json.dumps(reasons2, indent=2)
        )

        response1 = future1.result()
        response2 = future2.result()

        sentiments1 = json.loads(response1.content[0]["text"])
        sentiments2 = json.loads(response2.content[0]["text"])

        return sentiments1 + sentiments2


def extract_feedback_themes(analyst_output: list[dict]):

    reasons = [item["reason"] for item in analyst_output]
    prompt = feedback_themes_prompt.invoke(
    {
        "customer_summaries": json.dumps(reasons, indent=2)
    }
    )

    response = llm1.invoke(prompt)
    result = json.loads(response.content[0]["text"])
    return result




def create_sentiment_chart(sentiments: list[str]) -> str:

    os.makedirs("charts", exist_ok=True)

    counter = Counter(sentiments)

    labels = list(counter.keys())
    sizes = list(counter.values())

    color_map = {
        "EXCELLENT": "#2ECC71",        # Green
        "GOOD": "#3498DB",             # Blue
        "NEEDS_ATTENTION": "#F39C12",  # Orange
        "CRITICAL": "#E74C3C"          # Red
    }

    colors = [color_map[label] for label in labels]

    fig, ax = plt.subplots(figsize=(8, 6))

    wedges, texts, autotexts = ax.pie(
        sizes,
        colors=colors,
        startangle=90,
        autopct="%1.1f%%",
        pctdistance=0.75,
        wedgeprops={
            "width": 0.40,
            "edgecolor": "white",
            "linewidth": 2
        },
        textprops={
            "fontsize": 12,
            "weight": "bold"
        }
    )

    centre_circle = plt.Circle(
        (0, 0),
        0.60,
        fc="white"
    )

    ax.add_artist(centre_circle)

    ax.legend(
        wedges,
        labels,
        title="Sentiment",
        loc="center left",
        bbox_to_anchor=(1, 0.5),
        fontsize=11,
        title_fontsize=12
    )

    ax.set_title(
        "Customer Sentiment Distribution",
        fontsize=18,
        fontweight="bold",
        pad=20
    )

    plt.setp(
        autotexts,
        color="white",
        fontsize=11,
        fontweight="bold"
    )

    ax.set_aspect("equal")

    path = "charts/sentiment_chart.png"

    plt.tight_layout()

    plt.savefig(
        path,
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()

    return path


def create_pain_point_chart(pain_points: list[dict]) -> str:

    os.makedirs("charts", exist_ok=True)

    pain_points = sorted(
        pain_points,
        key=lambda x: x["count"],
        reverse=True
    )

    labels = [item["title"] for item in pain_points]
    counts = [item["count"] for item in pain_points]

    fig, ax = plt.subplots(figsize=(10, 6))

    bars = ax.barh(
        labels,
        counts,
        color="#E74C3C",
        edgecolor="black",
        linewidth=0.8
    )

    ax.invert_yaxis()

    ax.bar_label(
        bars,
        padding=5,
        fontsize=11,
        fontweight="bold"
    )

    ax.set_title(
        "Top 5 Customer Pain Points",
        fontsize=18,
        fontweight="bold",
        pad=15
    )

    ax.set_xlabel(
        "Number of Accounts",
        fontsize=13
    )

    ax.tick_params(
        axis="both",
        labelsize=11
    )

    ax.grid(
        axis="x",
        linestyle="--",
        alpha=0.35
    )

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    path = "charts/pain_points_chart.png"

    plt.tight_layout()

    plt.savefig(
        path,
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()

    return path


def create_appreciation_chart(appreciations: list[dict]) -> str:

    os.makedirs("charts", exist_ok=True)

    appreciations = sorted(
        appreciations,
        key=lambda x: x["count"],
        reverse=True
    )

    labels = [item["title"] for item in appreciations]
    counts = [item["count"] for item in appreciations]

    fig, ax = plt.subplots(figsize=(10, 6))

    bars = ax.barh(
        labels,
        counts,
        color="#2ECC71",
        edgecolor="black",
        linewidth=0.8
    )

    ax.invert_yaxis()

    ax.bar_label(
        bars,
        padding=5,
        fontsize=11,
        fontweight="bold"
    )

    ax.set_title(
        "Top 5 Customer Appreciations",
        fontsize=18,
        fontweight="bold",
        pad=15
    )

    ax.set_xlabel(
        "Number of Accounts",
        fontsize=13
    )

    ax.tick_params(
        axis="both",
        labelsize=11
    )

    ax.grid(
        axis="x",
        linestyle="--",
        alpha=0.35
    )

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    path = "charts/appreciations_chart.png"

    plt.tight_layout()

    plt.savefig(
        path,
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()

    return path


def create_charts(
    sentiments: list[str],
    feedback_themes: dict
) -> dict:

    sentiment_chart = create_sentiment_chart(
        sentiments
    )

    pain_point_chart = create_pain_point_chart(
        feedback_themes["pain_points"]
    )

    appreciation_chart = create_appreciation_chart(
        feedback_themes["appreciations"]
    )

    return {
        "sentiment_chart": sentiment_chart,
        "pain_point_chart": pain_point_chart,
        "appreciation_chart": appreciation_chart
    }


def generate_executive_summary(
    sentiments: list[str],
    feedback_themes: dict
):

    sentiment_counts = dict(Counter(sentiments))

    prompt = executive_summary_prompt.invoke(
    {
        "sentiment_distribution": json.dumps(sentiment_counts, indent=2),
        "pain_points": json.dumps(feedback_themes["pain_points"], indent=2),
        "customer_appreciations": json.dumps(feedback_themes["appreciations"], indent=2),
    }
    )


    response = llm1.invoke(prompt)

    return json.loads(response.content[0]["text"])

def create_pdf_report(
    summary: dict,
    charts: dict,
    analysis_date: str,
    total_accounts: int,
    sentiments,
    feedback_themes
):

    os.makedirs("reports", exist_ok=True)

    pdf_path = "reports/customer_retention_report.pdf"

    doc = SimpleDocTemplate(pdf_path)

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "Title",
        parent=styles["Heading1"],
        alignment=TA_CENTER,
        fontSize=22,
        textColor=darkblue,
        spaceAfter=20
    )

    heading_style = styles["Heading2"]

    body_style = styles["BodyText"]

    story = []

    story.append(
    Paragraph(
        "Customer Retention Executive Report",
        title_style
    )
    )

    story.append(
        Paragraph(
            f"<b>Analysis Date:</b> {analysis_date}",
            body_style
        )
    )

    story.append(
        Paragraph(
            f"<b>Generated On:</b> {datetime.now().strftime('%d %B %Y')}",
            body_style
        )
    )

    story.append(
        Paragraph(
            f"<b>Accounts Analysed:</b> {total_accounts}",
            body_style
        )
    )

    story.append(
        Paragraph(
            "<b>Generated By:</b> Customer Retention Copilot",
            body_style
        )
    )

    story.append(Spacer(1, 0.15 * inch))

    from collections import Counter

    counter = Counter(sentiments)

    critical = counter.get("CRITICAL", 0)
    needs_attention = counter.get("NEEDS_ATTENTION", 0)
    good = counter.get("GOOD", 0)
    excellent = counter.get("EXCELLENT", 0)

    top_pain = feedback_themes["pain_points"][0]["title"]
    top_appreciation = feedback_themes["appreciations"][0]["title"]

    kpi_data = [
        ["Accounts", total_accounts],
        ["Critical", critical],
        ["Needs Attention", needs_attention],
        ["Positive", good + excellent],
        ["Top Pain Point", top_pain],
        ["Top Appreciation", top_appreciation]
    ]

    table = Table(
        kpi_data,
        colWidths=[2.5 * inch, 3.5 * inch]
    )

    table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#EAF2F8")),
            ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),

            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),

            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),

            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 8),

            ("VALIGN", (0, 0), (-1, -1), "MIDDLE")
        ])
        )

    story.append(table)

    story.append(Spacer(1, 0.15 * inch))


    story.append(
        Paragraph(
            "Executive Summary",
            heading_style
        )
    )

    story.append(
        Paragraph(
            summary["executive_summary"],
            body_style
        )
    )

    story.append(Spacer(1,0.15 * inch))

    story.append(
        Paragraph(
            "Figure 1. Customer Sentiment Distribution",
            heading_style
        )
    )

    story.append(
        Image(
            charts["sentiment_chart"],
            width=4.5 * inch,
            height=3.4 * inch
        )
    )
    story.append(Spacer(1, 0.15 * inch))

    story.append(
        Paragraph(
            "<b>Insight</b>",
            heading_style
        )
    )
    story.append(
        Paragraph(
            summary["chart_insights"]["sentiment"],
            body_style
        )
    )

    story.append(Spacer(1, 0.15 * inch))


    story.append(
        Paragraph(
            "Figure 2. Top Customer Pain Points",
            heading_style
        )
    )

    story.append(
        Image(
            charts["pain_point_chart"],
            width=4.1 * inch,
            height=3.0* inch
        )
    )

    story.append(Spacer(1,0.15 * inch))

    story.append(
        Paragraph(
            "<b>Insight</b>",
            heading_style
        )
    )

    story.append(
        Paragraph(
            summary["chart_insights"]["pain_points"],
            body_style
        )
    )

    story.append(Spacer(1,0.15 * inch))

    story.append(
        Paragraph(
            "Figure 3. Top Customer Appreciations",
            heading_style
        )
    )

    story.append(
        Image(
            charts["appreciation_chart"],
            width=4.1 * inch,
            height=3.0* inch
        )
    )

    story.append(Spacer(1,0.15 * inch))

    story.append(
        Paragraph(
            "<b>Insight</b>",
            heading_style
        )
    )

    story.append(
        Paragraph(
            summary["chart_insights"]["appreciations"],
            body_style
        )
    )

    story.append(Spacer(1, 0.15 * inch))

    story.append(
        Paragraph(
            "Key Findings",
            heading_style
        )
    )

    for item in summary["key_findings"]:

        story.append(
            Paragraph(
                f"• {item}",
                body_style
            )
        )

    story.append(Spacer(1, 0.25 * inch))


    story.append(
        Paragraph(
            "Recommended Actions",
            heading_style
        )
    )

    for item in summary["recommended_actions"]:

        story.append(
            Paragraph(
                f"• {item}",
                body_style
            )
        )

    story.append(Spacer(1,0.15 * inch))
    story.append(
        Paragraph(
            "Overall Assessment",
            heading_style
        )
    )

    story.append(
        Paragraph(
            summary["overall_assessment"],
            body_style
        )
    )
    doc.build(story)

    return pdf_path

def generate_report(analyst_output: list[dict],analysis_date):

    
    sentiments = classify_sentiments(
        analyst_output
    )


    feedback_themes = extract_feedback_themes(
        analyst_output
    )

    charts = create_charts(
        sentiments,
        feedback_themes
    )

    summary = generate_executive_summary(
        sentiments,
        feedback_themes
    )

    pdf_path = create_pdf_report(
        summary,
        charts,
        total_accounts=len(analyst_output),
        analysis_date=analysis_date,
        sentiments=sentiments,
        feedback_themes=feedback_themes
    )

    return {
        "sentiments": sentiments,
        "feedback_themes": feedback_themes,
        "charts": charts,
        "summary": summary,
        "pdf": pdf_path
    }

