# backend.py

import os
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go

from pmdarima import auto_arima
from statsmodels.tsa.arima.model import ARIMA
from scipy.optimize import minimize
from sklearn.metrics import mean_absolute_error, mean_squared_error

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet

warnings.filterwarnings("ignore", category=UserWarning)

# --- NEW: More Robust Forecasting ---
def forecast_expenditure(series: pd.Series, periods: int) -> pd.Series:
    series = pd.to_numeric(series, errors="coerce").dropna()
    if len(series) < 3:
        raise ValueError(f"Not enough historical points to forecast (found {len(series)}, need ≥ 3).")
    model = auto_arima(
        series, seasonal=False, stepwise=True, suppress_warnings=True,
        error_action="ignore", max_p=2, max_q=2, max_d=2
    )
    fc = model.predict(n_periods=periods)
    return pd.Series(fc)

# --- NEW: More Advanced Optimization ---
def optimize_expenditures(df: pd.DataFrame, inflation_rate=0.03, alpha=0.5, beta=0.5, gamma=0.001) -> pd.DataFrame:
    optimized_capex, optimized_opex = [], []
    for _, row in df.iterrows():
        pred_capex, pred_opex = float(row['Forecast_CapEx']), float(row['Forecast_OpEx'])
        def objective(x):
            capex, opex = x
            return (alpha * capex + beta * opex) * (1 + inflation_rate) + \
                   gamma * ((capex - pred_capex) ** 2 + (opex - pred_opex) ** 2)
        constraints = [{"type": "ineq", "fun": lambda x, pc=pred_capex: x[0] - 0.8 * pc}, {"type": "ineq", "fun": lambda x, po=pred_opex: x[1] - 0.7 * po}]
        result = minimize(objective, [pred_capex, pred_opex], method="SLSQP", bounds=[(0, None), (0, None)], constraints=constraints)
        if result.success and np.all(np.isfinite(result.x)):
            capex_opt, opex_opt = result.x
        else:
            capex_opt, opex_opt = 0.8 * pred_capex, 0.7 * pred_opex
        optimized_capex.append(float(capex_opt))
        optimized_opex.append(float(opex_opt))
    out = df.copy()
    out['Optimized_CapEx'], out['Optimized_OpEx'] = optimized_capex, optimized_opex
    return out

# --- NEW: More Detailed Recommendations ---
def generate_recommendations(pred_df: pd.DataFrame, opt_df: pd.DataFrame) -> str:
    total_forecast = pred_df[['Forecast_CapEx', 'Forecast_OpEx']].sum().sum()
    total_optimized = opt_df[['Optimized_CapEx', 'Optimized_OpEx']].sum().sum()
    total_savings = total_forecast - total_optimized
    savings_pct = (total_savings / total_forecast) * 100 if total_forecast else 0.0
    capex_reduction_pct = (1 - opt_df['Optimized_CapEx'].sum() / pred_df['Forecast_CapEx'].sum()) * 100 if pred_df['Forecast_CapEx'].sum() else 0.0
    opex_reduction_pct = (1 - opt_df['Optimized_OpEx'].sum() / pred_df['Forecast_OpEx'].sum()) * 100 if pred_df['Forecast_OpEx'].sum() else 0.0
    recs = [
        f"Total projected savings of {total_savings:,.2f} ({savings_pct:.2f}%) achievable without disrupting critical operations.",
        f"CapEx can be reduced by ~{capex_reduction_pct:.2f}% via deferring non-critical upgrades and phasing multi-year rollouts.",
        f"OpEx can be reduced by ~{opex_reduction_pct:.2f}% via process automation and vendor renegotiations.",
        "Lock in supplier/service contracts ahead of renewals to mitigate inflation passthrough.",
        "Prioritize high-ROI initiatives; sunset low-yield spend to free budget.",
        "Maintain a contingency reserve for regulatory or market shocks."
    ]
    return " ".join(recs)

# --- Reporting functions are fine, kept from old version for frontend compatibility ---
def plot_and_save_chart(full_df: pd.DataFrame, bank_name: str, output_dir: str) -> str:
    chart_path = os.path.join(output_dir, f"{bank_name}_chart.png")
    plt.figure(figsize=(9, 5.5))
    plt.plot(full_df["Year"], full_df["Forecast_CapEx"], "o-", label="Forecast CapEx")
    plt.plot(full_df["Year"], full_df["Optimized_CapEx"], "s-", label="Optimized CapEx")
    plt.plot(full_df["Year"], full_df["Forecast_OpEx"], "o--", label="Forecast OpEx")
    plt.plot(full_df["Year"], full_df["Optimized_OpEx"], "s--", label="Optimized OpEx")
    plt.title(f"{bank_name} - Forecast vs Optimized Expenditures"); plt.xlabel("Year"); plt.ylabel("Amount")
    plt.grid(alpha=0.5); plt.legend(); plt.tight_layout()
    plt.savefig(chart_path, bbox_inches="tight"); plt.close()
    return chart_path

def create_pdf_report(bank_name, summary_text, full_df, recommendations, chart_path, output_dir):
    pdf_path = os.path.join(output_dir, f"{bank_name}_report.pdf"); doc = SimpleDocTemplate(pdf_path, pagesize=A4)
    elements, styles = [], getSampleStyleSheet()
    elements.append(Paragraph(f"<b>{bank_name} Report</b>", styles['Title'])); elements.append(Spacer(1, 0.2 * inch))
    elements.append(Paragraph("<b>Summary:</b>", styles['Heading2'])); elements.append(Paragraph(summary_text.replace("\n", "<br/>"), styles['Normal'])); elements.append(Spacer(1, 0.2 * inch))
    table_data = [["Year", "Forecast CapEx", "Optimized CapEx", "Forecast OpEx", "Optimized OpEx"]]
    for _, r in full_df.iterrows():
        table_data.append([int(r['Year']), f"{r['Forecast_CapEx']:,.2f}", f"{r['Optimized_CapEx']:,.2f}", f"{r['Forecast_OpEx']:,.2f}", f"{r['Optimized_OpEx']:,.2f}"])
    table = Table(table_data, colWidths=[1*inch]*5)
    table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.grey), ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke), ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('GRID', (0, 0), (-1, -1), 0.5, colors.black)]))
    elements.append(table); elements.append(Spacer(1, 0.3 * inch))
    elements.append(Paragraph("<b>Recommendations:</b>", styles['Heading2'])); elements.append(Paragraph(recommendations, styles['Normal'])); elements.append(Spacer(1, 0.3 * inch))
    if chart_path and os.path.exists(chart_path):
        elements.append(Image(chart_path, width=5.5 * inch, height=3.5 * inch))
    doc.build(elements)
    return pdf_path

# --- NEW, INTEGRATED MAIN ANALYSIS PIPELINE ---
def run_analysis(file_path, bank_name, forecast_years, current_year, output_dir):
    # --- Data Loading and Robust Cleaning ---
    df = pd.read_excel(file_path)
    df.columns = [col.strip() for col in df.columns]
    if 'Banks' not in df.columns: raise ValueError("Excel file must contain a 'Banks' column.")
    df['Year'] = pd.to_numeric(df['Year'].ffill(), errors='coerce')
    df.dropna(subset=['Year'], inplace=True)
    df['Year'] = df['Year'].astype(int)
    bank_df = df[df['Banks'].astype(str).str.strip().str.lower() == bank_name.strip().lower()].copy()
    if bank_df.empty: raise ValueError(f"No data for bank: {bank_name}")
    
    max_year_for_forecast = current_year - 1
    historical_df = bank_df[bank_df['Year'] <= max_year_for_forecast].copy()
    historical_df['Capital Expenditure'] = pd.to_numeric(historical_df['Capital Expenditure'], errors='coerce').fillna(0)
    historical_df['Operating Expenditure'] = pd.to_numeric(historical_df['Operating Expenditure'], errors='coerce').fillna(0)
    grouped = historical_df.groupby('Year', as_index=False).agg({'Capital Expenditure': 'sum', 'Operating Expenditure': 'sum'})
    
    if len(grouped) < 3: # Lowered requirement
        raise ValueError(f"Not enough historical data for '{bank_name}' before year {current_year} (found {len(grouped)} years, need at least 3).")

    # --- Forecasting and Optimization ---
    last_historical_year = grouped['Year'].max()
    start_year = last_historical_year + 1
    forecast_years_list = list(range(start_year, start_year + forecast_years))
    capex_forecast = forecast_expenditure(grouped['Capital Expenditure'], forecast_years).reset_index(drop=True)
    opex_forecast = forecast_expenditure(grouped['Operating Expenditure'], forecast_years).reset_index(drop=True)
    pred_df = pd.DataFrame({'Year': forecast_years_list, 'Forecast_CapEx': capex_forecast, 'Forecast_OpEx': opex_forecast})
    optimized_df = optimize_expenditures(pred_df)
    full_df = pred_df.merge(optimized_df[['Year', 'Optimized_CapEx', 'Optimized_OpEx']], on='Year', how='left')
    
    # --- Calculate Metrics for Return Dictionary ---
    total_forecast_capex = full_df['Forecast_CapEx'].sum()
    total_forecast_opex = full_df['Forecast_OpEx'].sum()
    total_optimized_capex = full_df['Optimized_CapEx'].sum()
    total_optimized_opex = full_df['Optimized_OpEx'].sum()
    total_savings = (total_forecast_capex + total_forecast_opex) - (total_optimized_capex + total_optimized_opex)
    total_forecast = total_forecast_capex + total_forecast_opex
    total_optimized = total_optimized_capex + total_optimized_opex
    savings_pct = (total_savings / total_forecast) * 100 if total_forecast else 0

    # --- Generate Text and File Outputs ---
    summary_text = f"Bank: {bank_name.title()}\nForecast Years: {forecast_years_list}\n\nTotal Forecast CapEx: {total_forecast_capex:,.2f}\nTotal Optimized CapEx: {total_optimized_capex:,.2f}\nTotal Forecast OpEx: {total_forecast_opex:,.2f}\nTotal Optimized OpEx: {total_optimized_opex:,.2f}\n\nTotal Savings: {total_savings:,.2f}"
    recommendations = generate_recommendations(pred_df, full_df)
    os.makedirs(output_dir, exist_ok=True)
    excel_path = os.path.join(output_dir, f"{bank_name}_forecast_optimized.xlsx")
    full_df.to_excel(excel_path, index=False)
    chart_path = plot_and_save_chart(full_df, bank_name, output_dir)
    pdf_path = create_pdf_report(bank_name, summary_text, full_df, recommendations, chart_path, output_dir)
    
    # --- Create Plotly Chart for Frontend (Structure Unchanged) ---
    fig_plotly = go.Figure()
    fig_plotly.add_trace(go.Scatter(x=full_df['Year'], y=full_df['Forecast_CapEx'], name='Forecast CapEx', mode='lines+markers', line=dict(color='#1E88E5', dash='dash')))
    fig_plotly.add_trace(go.Scatter(x=full_df['Year'], y=full_df['Forecast_OpEx'], name='Forecast OpEx', mode='lines+markers', line=dict(color='#FF6F00', dash='dash')))
    fig_plotly.add_trace(go.Scatter(x=full_df['Year'], y=full_df['Optimized_CapEx'], name='Optimized CapEx', mode='lines+markers', line=dict(color='#1E88E5')))
    fig_plotly.add_trace(go.Scatter(x=full_df['Year'], y=full_df['Optimized_OpEx'], name='Optimized OpEx', mode='lines+markers', line=dict(color='#FF6F00')))
    fig_plotly.update_layout(
        xaxis=dict(title=dict(text="Year",font=dict(color="black")), tickfont=dict(color="black"), showline=True, linewidth=1, linecolor='black'),
        yaxis=dict(title=dict(text="Amount (Local Currency)", font=dict(color="black")), tickfont=dict(color="black"), showline=True, linewidth=1, linecolor='black'),
        legend=dict(title="Expenditure Type", font=dict(color="black")),
        template="plotly_white", hovermode="x unified"
    )
    
    # --- FINAL STEP: Return the dictionary with the EXACT same structure as before ---
    return {
        "summary": summary_text,
        "recommendations": recommendations,
        "combined_df": full_df,
        "excel_path": excel_path,
        "pdf_path": pdf_path,
        "chart_path": chart_path,
        "chart_fig": fig_plotly,
        "kpi_metrics": { "total_savings": total_savings, "savings_pct": savings_pct, "total_forecast": total_forecast, "total_optimized": total_optimized }
    }