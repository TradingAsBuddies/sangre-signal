"""Claude AI-powered formatter for stock analysis.

This module provides natural language formatting of stock analysis
using Claude AI, with support for English and Spanish output.
"""

import logging
import re
import sys
from datetime import datetime
from typing import Optional, List, Literal, TYPE_CHECKING
from zoneinfo import ZoneInfo

from ..models import StockInfo, RiskAnalysis, RiskSeverity
from ..config import CLAUDE_CONFIG, ClaudeConfig
from .base import BaseFormatter

if TYPE_CHECKING:
    from ..cli import TickerResult

logger = logging.getLogger("super_signal")


def _strip_emojis(text: str) -> str:
    """Remove emojis and other non-printable characters for Windows console compatibility."""
    # Remove emoji and other problematic Unicode characters
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F700-\U0001F77F"  # alchemical symbols
        "\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
        "\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
        "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
        "\U0001FA00-\U0001FA6F"  # Chess Symbols
        "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
        "\U00002702-\U000027B0"  # Dingbats
        "\U000024C2-\U0001F251"  # Various symbols
        "]+",
        flags=re.UNICODE
    )
    return emoji_pattern.sub('', text)


def _safe_encode_for_console(text: str) -> str:
    """Safely encode text for Windows console, transliterating Spanish accents if needed.

    On Windows with legacy console encoding (cp1252, etc.), Spanish accented characters
    often don't display correctly due to encoding mismatches between UTF-8 and the
    console. This function always transliterates accented characters on Windows
    for reliable display.
    """
    # Spanish character transliteration map
    SPANISH_TRANSLITERATION = {
        'á': 'a', 'Á': 'A',
        'é': 'e', 'É': 'E',
        'í': 'i', 'Í': 'I',
        'ó': 'o', 'Ó': 'O',
        'ú': 'u', 'Ú': 'U',
        'ü': 'u', 'Ü': 'U',
        'ñ': 'n', 'Ñ': 'N',
        '¿': '?', '¡': '!',
        '–': '-', '—': '-',
        '"': '"', '"': '"',
        ''': "'", ''': "'",
        '…': '...',
        '•': '-', '·': '-',  # Bullet points
        '→': '->', '←': '<-',  # Arrows
        '×': 'x', '÷': '/',  # Math symbols
    }

    # Check if we're on Windows (non-UTF-8 console likely)
    is_windows = sys.platform == 'win32'
    encoding = (sys.stdout.encoding or 'utf-8').lower().replace('-', '')
    is_utf8 = encoding in ('utf8', 'utf16', 'utf32')

    # On Windows with non-UTF-8 encoding, always transliterate
    if is_windows and not is_utf8:
        result = []
        for char in text:
            if char in SPANISH_TRANSLITERATION:
                result.append(SPANISH_TRANSLITERATION[char])
            else:
                # Keep ASCII and basic Latin characters
                if ord(char) < 128:
                    result.append(char)
                else:
                    # Try to keep the character, fall back to ?
                    try:
                        char.encode('cp1252')
                        result.append(char)
                    except (UnicodeEncodeError, LookupError):
                        result.append('?')
        return ''.join(result)

    return text


# Bilingual prompts and templates
SYSTEM_PROMPTS = {
    "en": """You are a financial analyst providing clear, concise stock risk assessments for retail investors.
Your role is to explain complex financial data in plain language that anyone can understand.
Focus on actionable insights and clear explanations of risk factors.
Be direct but not alarmist - present facts objectively.
IMPORTANT: Do not use emojis in your response - use plain text only.""",

    "es": """Eres un analista financiero que proporciona evaluaciones claras y concisas de riesgos de acciones para inversionistas particulares.
Tu rol es explicar datos financieros complejos en un lenguaje sencillo que cualquier persona pueda entender.
Usa espanol mexicano (como se habla en la region de Oaxaca, Mexico) - amable, directo y accesible.
Concentrate en informacion practica y explicaciones claras de los factores de riesgo.
Se directo pero no alarmista - presenta los hechos de manera objetiva.
IMPORTANTE: No uses emojis en tu respuesta - usa solo texto plano."""
}

ANALYSIS_PROMPTS = {
    "en": """Analyze this stock and provide a well-formatted summary with risk assessment in plain language.

Stock Data:
- Ticker: {ticker}
- Company: {company_name}
- Exchange: {exchange}
- Country: {country}
- Headquarters: {headquarters}
- Is ADR: {is_adr}
- Market Cap: {market_cap}
- Current Price: {price}
- 52-Week High: {week_52_high}
- 52-Week Low: {week_52_low}
- % Off 52W High: {pct_off_high}
- Float Shares: {float_shares}
- Short % of Float: {short_pct}
- Insider Ownership: {insider_own}
- Institutional Ownership: {inst_own}
- Total Debt: {debt}
- VIX Index: {vix}

Detected Risk Flags:
{risk_flags}

Please provide:
1. A brief company overview (1-2 sentences)
2. RISK ASSESSMENT section with a clear overall rating (LOW/MEDIUM/HIGH) and explanation
3. For each detected risk flag, explain in plain language:
   - What it means for an investor
   - Why it matters
   - Potential impact on the investment
4. KEY METRICS summary highlighting important numbers
5. BOTTOM LINE: A clear, actionable summary

Format the response with clear headers and bullet points for readability.""",

    "es": """Analiza esta accion y proporciona un resumen bien formateado con evaluacion de riesgos en lenguaje sencillo.
Usa espanol mexicano (como se habla en Oaxaca, Mexico) - claro, amable y accesible.

Datos de la Accion:
- Simbolo: {ticker}
- Empresa: {company_name}
- Bolsa: {exchange}
- Pais: {country}
- Sede: {headquarters}
- Es ADR: {is_adr}
- Capitalizacion de Mercado: {market_cap}
- Precio Actual: {price}
- Maximo 52 Semanas: {week_52_high}
- Minimo 52 Semanas: {week_52_low}
- % Debajo del Maximo 52S: {pct_off_high}
- Acciones en Circulacion Libre: {float_shares}
- % Corto del Float: {short_pct}
- Propiedad de Insiders: {insider_own}
- Propiedad Institucional: {inst_own}
- Deuda Total: {debt}
- Indice VIX: {vix}

Senales de Riesgo Detectadas:
{risk_flags}

Por favor proporciona:
1. Una breve descripcion de la empresa (1-2 oraciones)
2. Seccion de EVALUACION DE RIESGO con una calificacion general clara (BAJO/MEDIO/ALTO) y explicacion
3. Para cada senal de riesgo detectada, explica en lenguaje sencillo:
   - Que significa para un inversionista
   - Por que es importante
   - Impacto potencial en la inversion
4. Resumen de METRICAS CLAVE destacando numeros importantes
5. CONCLUSION: Un resumen claro y practico

Formatea la respuesta con encabezados claros y vinetas para facilitar la lectura."""
}

BATCH_PROMPTS = {
    "en": """Analyze this portfolio of stocks and provide a consolidated risk assessment.

Portfolio Stocks:
{stocks_summary}

Please provide:
1. PORTFOLIO OVERVIEW: Brief summary of the stocks analyzed
2. RISK DISTRIBUTION: How many stocks fall into LOW/MEDIUM/HIGH risk categories
3. COMMON RISK FACTORS: Patterns across the portfolio
4. INDIVIDUAL HIGHLIGHTS: Key concerns for each stock (brief)
5. RECOMMENDATIONS: General portfolio risk observations

Keep the analysis concise but comprehensive.""",

    "es": """Analiza este portafolio de acciones y proporciona una evaluacion de riesgo consolidada.
Usa espanol mexicano (como se habla en Oaxaca, Mexico) - claro, amable y accesible.

Acciones del Portafolio:
{stocks_summary}

Por favor proporciona:
1. RESUMEN DEL PORTAFOLIO: Breve resumen de las acciones analizadas
2. DISTRIBUCION DE RIESGO: Cuantas acciones caen en categorias de riesgo BAJO/MEDIO/ALTO
3. FACTORES DE RIESGO COMUNES: Patrones en el portafolio
4. DESTACADOS INDIVIDUALES: Preocupaciones clave para cada accion (breve)
5. RECOMENDACIONES: Observaciones generales de riesgo del portafolio

Manten el analisis conciso pero completo."""
}


def _format_number(value: Optional[float], prefix: str = "$") -> str:
    """Format a number with appropriate suffix (K, M, B, T)."""
    if value is None:
        return "N/A"

    if abs(value) >= 1_000_000_000_000:
        return f"{prefix}{value / 1_000_000_000_000:.2f}T"
    elif abs(value) >= 1_000_000_000:
        return f"{prefix}{value / 1_000_000_000:.2f}B"
    elif abs(value) >= 1_000_000:
        return f"{prefix}{value / 1_000_000:.2f}M"
    elif abs(value) >= 1_000:
        return f"{prefix}{value / 1_000:.2f}K"
    else:
        return f"{prefix}{value:.2f}"


def _format_percent(value: Optional[float]) -> str:
    """Format a percentage value."""
    if value is None:
        return "N/A"
    return f"{value:.2f}%"


class ClaudeFormatter(BaseFormatter):
    """Formatter that uses Claude AI to generate natural language analysis.

    This formatter sends stock data to Claude and receives a well-formatted,
    plain-language analysis with risk explanations in English or Spanish.
    """

    def __init__(self, language: Literal["en", "es"] = None, config: ClaudeConfig = None):
        """Initialize the Claude formatter.

        Args:
            language: Output language ('en' or 'es'). Defaults to config setting.
            config: Claude configuration. Defaults to CLAUDE_CONFIG.
        """
        self.config = config or CLAUDE_CONFIG
        self.language = language or self.config.language
        self._client = None

    def _get_client(self):
        """Get or create the Anthropic client."""
        if self._client is None:
            try:
                import anthropic
                self._client = anthropic.Anthropic(api_key=self.config.api_key)
            except ImportError:
                raise ImportError(
                    "The 'anthropic' package is required for Claude formatting. "
                    "Install it with: pip install anthropic"
                )
        return self._client

    def _build_risk_flags_text(self, risk_analysis: RiskAnalysis) -> str:
        """Build a text representation of risk flags."""
        if not risk_analysis.has_risks:
            if self.language == "es":
                return "No se detectaron senales de riesgo significativas."
            return "No significant risk flags detected."

        flags_text = []
        for flag in risk_analysis.flags:
            severity_label = flag.severity.value.upper()
            flags_text.append(f"- [{severity_label}] {flag.message}")

        return "\n".join(flags_text)

    def _build_prompt(
        self,
        stock_info: StockInfo,
        risk_analysis: RiskAnalysis,
        float_threshold: int,
        vix_value: Optional[float]
    ) -> str:
        """Build the analysis prompt with stock data."""
        template = ANALYSIS_PROMPTS[self.language]

        return template.format(
            ticker=stock_info.ticker,
            company_name=stock_info.get_display_name() or "Unknown",
            exchange=stock_info.exchange or "Unknown",
            country=stock_info.get_country() or "Unknown",
            headquarters=stock_info.get_headquarters() or "Unknown",
            is_adr="Yes" if stock_info.is_adr else "No",
            market_cap=_format_number(stock_info.market_cap),
            price=_format_number(stock_info.regular_market_price),
            week_52_high=_format_number(stock_info.fifty_two_week_high),
            week_52_low=_format_number(stock_info.fifty_two_week_low),
            pct_off_high=_format_percent(stock_info.percent_off_52week_high()),
            float_shares=_format_number(stock_info.float_shares, prefix=""),
            short_pct=_format_percent(stock_info.short_percent_of_float),
            insider_own=_format_percent(
                stock_info.held_percent_insiders * 100 if stock_info.held_percent_insiders else None
            ),
            inst_own=_format_percent(
                stock_info.held_percent_institutions * 100 if stock_info.held_percent_institutions else None
            ),
            debt=_format_number(stock_info.total_debt),
            vix=f"{vix_value:.2f}" if vix_value else "N/A",
            risk_flags=self._build_risk_flags_text(risk_analysis)
        )

    def _call_claude(self, prompt: str) -> str:
        """Call Claude API with the given prompt."""
        client = self._get_client()

        message = client.messages.create(
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            system=SYSTEM_PROMPTS[self.language],
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        # Strip emojis and handle Windows console encoding
        text = _strip_emojis(message.content[0].text)
        return _safe_encode_for_console(text)

    def _format_fallback(
        self,
        stock_info: StockInfo,
        risk_analysis: RiskAnalysis,
        float_threshold: int,
        vix_value: Optional[float],
        error: str
    ) -> str:
        """Provide fallback formatting when Claude is unavailable."""
        lines = []
        divider = "=" * 60

        if self.language == "es":
            lines.append(divider)
            lines.append(f"  ANALISIS DE {stock_info.ticker}  ")
            lines.append(divider)
            lines.append(f"\n[Nota: Analisis de IA no disponible - {error}]")
            lines.append(f"\nEmpresa: {stock_info.get_display_name() or 'Desconocido'}")
            lines.append(f"Bolsa: {stock_info.exchange or 'Desconocido'}")
            lines.append(f"Pais: {stock_info.get_country() or 'Desconocido'}")
            lines.append(f"Precio: {_format_number(stock_info.regular_market_price)}")
            lines.append(f"\nSENALES DE RIESGO:")
            lines.append(self._build_risk_flags_text(risk_analysis))
        else:
            lines.append(divider)
            lines.append(f"  {stock_info.ticker} ANALYSIS  ")
            lines.append(divider)
            lines.append(f"\n[Note: AI analysis unavailable - {error}]")
            lines.append(f"\nCompany: {stock_info.get_display_name() or 'Unknown'}")
            lines.append(f"Exchange: {stock_info.exchange or 'Unknown'}")
            lines.append(f"Country: {stock_info.get_country() or 'Unknown'}")
            lines.append(f"Price: {_format_number(stock_info.regular_market_price)}")
            lines.append(f"\nRISK FLAGS:")
            lines.append(self._build_risk_flags_text(risk_analysis))

        lines.append(f"\n{divider}")
        return _safe_encode_for_console("\n".join(lines))

    def format(
        self,
        stock_info: StockInfo,
        risk_analysis: RiskAnalysis,
        float_threshold: int,
        vix_value: Optional[float] = None
    ) -> str:
        """Format stock data using Claude AI.

        Args:
            stock_info: Stock information data
            risk_analysis: Risk analysis results
            float_threshold: Minimum float threshold for risk highlighting
            vix_value: Current VIX index value (optional)

        Returns:
            Claude-generated analysis string
        """
        # Check if Claude is configured
        if not self.config.is_configured():
            return self._format_fallback(
                stock_info, risk_analysis, float_threshold, vix_value,
                "ANTHROPIC_API_KEY not set"
            )

        try:
            prompt = self._build_prompt(stock_info, risk_analysis, float_threshold, vix_value)
            analysis = self._call_claude(prompt)

            # Add header and timestamp
            divider = "=" * 60
            est = ZoneInfo("America/New_York")
            timestamp = datetime.now(est).strftime("%Y-%m-%d %H:%M:%S %Z")

            if self.language == "es":
                header = f"{divider}\n  ANALISIS DE {stock_info.ticker} (Potenciado por Claude AI)  \n{divider}"
                footer = f"\n{divider}\nGenerado: {timestamp}\n{divider}"
            else:
                header = f"{divider}\n  {stock_info.ticker} ANALYSIS (Powered by Claude AI)  \n{divider}"
                footer = f"\n{divider}\nGenerated: {timestamp}\n{divider}"

            return _safe_encode_for_console(f"{header}\n\n{analysis}{footer}")

        except Exception as e:
            logger.error(f"Claude API error for {stock_info.ticker}: {e}")
            return self._format_fallback(
                stock_info, risk_analysis, float_threshold, vix_value,
                str(e)
            )

    def format_batch(
        self,
        results: List["TickerResult"],
        float_threshold: int,
        vix_value: Optional[float] = None
    ) -> str:
        """Format multiple ticker results with portfolio-level analysis.

        Args:
            results: List of TickerResult objects
            float_threshold: Minimum float threshold for risk highlighting
            vix_value: Current VIX index value (optional)

        Returns:
            Formatted string output for all results with portfolio summary
        """
        outputs = []
        successful_results = [r for r in results if r.success]
        failed_results = [r for r in results if not r.success]

        # Format individual stocks
        for result in results:
            if result.success:
                outputs.append(self.format(
                    result.stock_info,
                    result.risk_analysis,
                    float_threshold,
                    vix_value
                ))
            else:
                outputs.append(self.format_error(result.ticker, result.error))

        # Add portfolio summary if multiple successful results and Claude is available
        if len(successful_results) > 1 and self.config.is_configured():
            try:
                portfolio_summary = self._format_portfolio_summary(
                    successful_results, float_threshold, vix_value
                )
                outputs.append("\n" + portfolio_summary)
            except Exception as e:
                logger.error(f"Failed to generate portfolio summary: {e}")

        return "\n\n".join(outputs)

    def _format_portfolio_summary(
        self,
        results: List["TickerResult"],
        float_threshold: int,
        vix_value: Optional[float]
    ) -> str:
        """Generate a portfolio-level summary using Claude."""
        # Build stocks summary
        stocks_lines = []
        for result in results:
            info = result.stock_info
            analysis = result.risk_analysis

            risk_count = len(analysis.flags)
            high_risks = len(analysis.get_flags_by_severity(RiskSeverity.HIGH))

            stocks_lines.append(
                f"- {info.ticker} ({info.get_display_name()}): "
                f"{risk_count} risk flags ({high_risks} high), "
                f"Price: {_format_number(info.regular_market_price)}, "
                f"Country: {info.get_country()}"
            )

        stocks_summary = "\n".join(stocks_lines)

        prompt = BATCH_PROMPTS[self.language].format(stocks_summary=stocks_summary)
        summary = self._call_claude(prompt)

        divider = "=" * 60
        if self.language == "es":
            header = f"{divider}\n  RESUMEN DEL PORTAFOLIO  \n{divider}"
        else:
            header = f"{divider}\n  PORTFOLIO SUMMARY  \n{divider}"

        return _safe_encode_for_console(f"{header}\n\n{summary}\n{divider}")

    def format_error(self, ticker: str, error: Optional[str]) -> str:
        """Format an error result for a ticker.

        Args:
            ticker: Stock ticker symbol
            error: Error message

        Returns:
            Formatted error string
        """
        if self.language == "es":
            return _safe_encode_for_console(f"Error para {ticker}: {error or 'Error desconocido'}")
        return f"Error for {ticker}: {error or 'Unknown error'}"
