"""Market data providers.

* ``MockDataProvider`` — deterministic synthetic snapshot, works offline.
* ``YFinanceProvider`` — real data via the free ``yfinance`` package
  (optional dependency; only imported when DATA_MODE=yfinance).
* ``FallbackDataProvider`` — wraps the real provider and falls back to
  mock data **per call** when a fetch fails (network down, bad ticker,
  Yahoo rate-limit, ...). The returned dicts carry a ``source`` string
  and a ``used_fallback`` flag so the report can state honestly which
  data was used; the mock fallback's source is clearly marked synthetic.

All providers return the same plain-dict shapes so agents never care
which one served the data.
"""
from __future__ import annotations

import hashlib
import os


def _seeded(ticker: str) -> float:
    return int(hashlib.sha256(ticker.upper().encode()).hexdigest()[:6], 16) / 0xFFFFFF


class MockDataProvider:
    name = "mock"

    def market_snapshot(self, ticker: str) -> dict:
        s = _seeded(ticker)
        price = round(80 + s * 320, 2)
        return {
            "ticker": ticker.upper(),
            "price": price,
            "change_pct_1d": round((s - 0.42) * 4, 2),
            "change_pct_3m": round((s - 0.35) * 30, 2),
            "ema_10": round(price * (0.97 + s * 0.04), 2),
            "sma_50": round(price * (0.94 + s * 0.08), 2),
            "sma_200": round(price * (0.88 + s * 0.10), 2),
            "rsi_14": round(38 + s * 32, 1),
            "macd": round((s - 0.45) * 6, 2),
            "macd_signal": round((s - 0.48) * 6, 2),
            "macd_hist": round((s - 0.42) * 1.5, 2),
            "bollinger_upper": round(price * 1.06, 2),
            "bollinger_lower": round(price * 0.94, 2),
            "atr_14": round(price * 0.021, 2),
            "support_60d": round(price * 0.91, 2),
            "resistance_60d": round(price * 1.08, 2),
            "avg_volume_m": round(8 + s * 60, 1),
            "as_of": None,
            "currency": None,
            "source": "mock (synthetic, offline)",
            "used_fallback": False,
        }

    def fundamentals(self, ticker: str) -> dict:
        s = _seeded(ticker + ":f")
        return {
            "ticker": ticker.upper(),
            "company_name": None,
            "sector": None,
            "revenue_growth_yoy_pct": round(4 + s * 22, 1),
            "gross_margin_pct": round(32 + s * 34, 1),
            "operating_margin_pct": round(10 + s * 20, 1),
            "net_margin_pct": round(6 + s * 18, 1),
            "pe_ratio": round(14 + s * 30, 1),
            "forward_pe": round(12 + s * 26, 1),
            "peg_ratio": round(0.6 + s * 1.8, 2),
            "roe_pct": round(8 + s * 30, 1),
            "eps_ttm": round(1 + s * 9, 2),
            "beta": round(0.7 + s * 1.1, 2),
            "sector_pe_median": 21.0,
            "debt_to_equity": round(0.2 + s * 1.3, 2),
            "free_cash_flow_bn": round(1 + s * 24, 1),
            "market_cap_bn": round(50 + s * 900, 1),
            "dividend_yield_pct": round(s * 2.5, 2),
            "source": "mock (synthetic, offline)",
            "used_fallback": False,
        }

    def news(self, ticker: str) -> list[dict]:
        t = ticker.upper()
        return [
            {"headline": f"{t} leans into AI features across its product line",
             "publisher": "mock", "published": None, "tone": "positive"},
            {"headline": f"Analysts raise {t} price target after strong quarter",
             "publisher": "mock", "published": None, "tone": "positive"},
            {"headline": f"One broker turns cautious on {t} valuation",
             "publisher": "mock", "published": None, "tone": "negative"},
        ]


def _rsi(close, window: int = 14):
    """Wilder-style RSI from a pandas Close series; None if not enough data."""
    if len(close) <= window:
        return None
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / window, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / window, adjust=False).mean()
    last_loss = float(loss.iloc[-1])
    if last_loss == 0:
        return 100.0
    rs = float(gain.iloc[-1]) / last_loss
    return round(100 - 100 / (1 + rs), 1)


def _pct_or_none(value, digits: int = 1):
    """yfinance returns margins/growth as fractions (0.23 = 23%)."""
    if value is None:
        return None
    try:
        return round(float(value) * 100, digits)
    except (TypeError, ValueError):
        return None


def _num_or_none(value, digits: int = 2):
    if value is None:
        return None
    try:
        return round(float(value), digits)
    except (TypeError, ValueError):
        return None


class YFinanceProvider:
    name = "yfinance"
    SOURCE = "yfinance (Yahoo Finance, real data)"

    def __init__(self):
        self._session = None  # lazily built curl_cffi session

    def _get_session(self):
        """A browser-impersonating session for Yahoo.

        Yahoo rejects/stalls plain scripted clients, and some sandboxes
        route traffic through an HTTP(S) proxy given via environment
        variables — curl_cffi does not always pick those up by itself,
        so pass them explicitly. With no proxy in the environment this
        behaves like a normal direct session.
        """
        if self._session is None:
            try:
                from curl_cffi import requests as cf_requests

                proxy = (
                    os.environ.get("HTTPS_PROXY")
                    or os.environ.get("https_proxy")
                    or os.environ.get("ALL_PROXY")
                    or os.environ.get("all_proxy")
                )
                proxies = {"http": proxy, "https": proxy} if proxy else None
                self._session = cf_requests.Session(
                    impersonate="chrome", proxies=proxies
                )
            except Exception:
                self._session = False  # let yfinance use its default session
        return self._session or None

    def _ticker(self, ticker: str):
        import yfinance as yf  # optional dependency

        session = self._get_session()
        if session is not None:
            return yf.Ticker(ticker.upper(), session=session)
        return yf.Ticker(ticker.upper())

    def market_snapshot(self, ticker: str) -> dict:
        t = self._ticker(ticker)
        hist = t.history(period="1y", auto_adjust=False)
        if hist is None or hist.empty or "Close" not in hist:
            raise ValueError(f"yfinance returned no price history for {ticker}")
        close = hist["Close"].dropna()
        if len(close) < 2:
            raise ValueError(f"yfinance returned too little history for {ticker}")
        price = float(close.iloc[-1])

        def pct_ago(n: int):
            if len(close) <= n:
                return None
            return round((price / float(close.iloc[-1 - n]) - 1) * 100, 2)

        sma_50 = float(close.rolling(50).mean().iloc[-1]) if len(close) >= 50 else None
        sma_200 = float(close.rolling(200).mean().iloc[-1]) if len(close) >= 200 else None
        # Indicator set mirrors the analyst coverage of the user's own
        # trading-agents-plugin design (EMA10/SMA50/SMA200, RSI14, MACD,
        # Bollinger Bands, ATR, support/resistance) — implemented here
        # from standard formulas, no code copied.
        ema_10 = float(close.ewm(span=10, adjust=False).mean().iloc[-1])
        macd_line = (
            close.ewm(span=12, adjust=False).mean()
            - close.ewm(span=26, adjust=False).mean()
        )
        macd_signal = macd_line.ewm(span=9, adjust=False).mean()
        macd = float(macd_line.iloc[-1])
        macd_sig = float(macd_signal.iloc[-1])
        boll_mid = close.rolling(20).mean()
        boll_std = close.rolling(20).std()
        boll_upper = float((boll_mid + 2 * boll_std).iloc[-1]) if len(close) >= 20 else None
        boll_lower = float((boll_mid - 2 * boll_std).iloc[-1]) if len(close) >= 20 else None
        atr_14 = None
        support = resistance = None
        if {"High", "Low"} <= set(hist.columns):
            high, low = hist["High"], hist["Low"]
            prev_close = close.shift(1)
            import pandas as pd

            tr = pd.concat(
                [high - low, (high - prev_close).abs(), (low - prev_close).abs()],
                axis=1,
            ).max(axis=1)
            atr_14 = float(tr.ewm(alpha=1 / 14, adjust=False).mean().iloc[-1])
            window = min(60, len(hist))
            support = float(low.tail(window).min())
            resistance = float(high.tail(window).max())
        last_date = close.index[-1]
        currency = None
        try:
            currency = (t.info or {}).get("currency")
        except Exception:
            pass  # currency is cosmetic; price history already succeeded
        return {
            "ticker": ticker.upper(),
            "price": round(price, 2),
            "change_pct_1d": round(float(close.pct_change().iloc[-1]) * 100, 2),
            "change_pct_3m": pct_ago(63),
            "ema_10": round(ema_10, 2),
            "sma_50": round(sma_50, 2) if sma_50 is not None else None,
            "sma_200": round(sma_200, 2) if sma_200 is not None else None,
            "rsi_14": _rsi(close),
            "macd": round(macd, 2),
            "macd_signal": round(macd_sig, 2),
            "macd_hist": round(macd - macd_sig, 2),
            "bollinger_upper": round(boll_upper, 2) if boll_upper is not None else None,
            "bollinger_lower": round(boll_lower, 2) if boll_lower is not None else None,
            "atr_14": round(atr_14, 2) if atr_14 is not None else None,
            "support_60d": round(support, 2) if support is not None else None,
            "resistance_60d": round(resistance, 2) if resistance is not None else None,
            "avg_volume_m": round(float(hist["Volume"].tail(30).mean()) / 1e6, 1)
            if "Volume" in hist else None,
            "as_of": last_date.strftime("%Y-%m-%d"),
            "currency": currency,
            "source": self.SOURCE,
            "used_fallback": False,
        }

    def fundamentals(self, ticker: str) -> dict:
        t = self._ticker(ticker)
        info = t.info or {}
        if not info or (info.get("regularMarketPrice") is None and not info.get("longName")):
            raise ValueError(f"yfinance returned no fundamentals for {ticker}")
        fcf = info.get("freeCashflow")
        mcap = info.get("marketCap")
        # yfinance reports debtToEquity as a percentage-like number (157.5 ≙ 1.575x)
        dte = info.get("debtToEquity")
        return {
            "ticker": ticker.upper(),
            "company_name": info.get("longName") or info.get("shortName"),
            "sector": info.get("sector"),
            "revenue_growth_yoy_pct": _pct_or_none(info.get("revenueGrowth")),
            "gross_margin_pct": _pct_or_none(info.get("grossMargins")),
            "operating_margin_pct": _pct_or_none(info.get("operatingMargins")),
            "net_margin_pct": _pct_or_none(info.get("profitMargins")),
            "pe_ratio": _num_or_none(info.get("trailingPE"), 1),
            "forward_pe": _num_or_none(info.get("forwardPE"), 1),
            "peg_ratio": _num_or_none(
                info.get("trailingPegRatio") or info.get("pegRatio")
            ),
            "roe_pct": _pct_or_none(info.get("returnOnEquity")),
            "eps_ttm": _num_or_none(info.get("trailingEps")),
            "beta": _num_or_none(info.get("beta")),
            "sector_pe_median": None,  # not provided by Yahoo; left for the LLM to contextualise
            "debt_to_equity": round(float(dte) / 100, 2) if dte is not None else None,
            "free_cash_flow_bn": round(float(fcf) / 1e9, 1) if fcf else None,
            "market_cap_bn": round(float(mcap) / 1e9, 1) if mcap else None,
            # NOTE: unlike margins/growth (fractions), Yahoo's quoteSummary
            # already reports dividendYield in percent (0.46 means 0.46%).
            "dividend_yield_pct": _num_or_none(info.get("dividendYield"), 2),
            "source": self.SOURCE,
            "used_fallback": False,
        }

    def news(self, ticker: str) -> list[dict]:
        import yfinance as yf

        # NOTE: Ticker.get_news() returns an empty list in this
        # environment (its endpoint stalls through the sandbox proxy);
        # the Search API works and returns the same Yahoo headlines.
        queries = [ticker.upper()]
        raw = []
        for query in queries:
            try:
                search = yf.Search(query, news_count=5, session=self._get_session())
                raw = search.news or []
            except Exception:
                raw = []
            if raw:
                break
            # Yahoo's news search indexes some listings (e.g. 7203.T) under
            # the company name rather than the ticker — retry with it once.
            if len(queries) == 1:
                try:
                    info = self._ticker(ticker).info or {}
                    name = info.get("longName") or info.get("shortName")
                    if name:
                        queries.append(name)
                except Exception:
                    pass
        if not raw:
            raw = self._ticker(ticker).news or []
        out = []
        for item in raw[:5]:
            content = item.get("content") or {}
            title = content.get("title") or item.get("title") or ""
            if not title:
                continue
            provider = content.get("provider") or {}
            publisher = provider.get("displayName") or item.get("publisher")
            published = content.get("pubDate") or None
            epoch = item.get("providerPublishTime")
            if published is None and epoch:
                import datetime as _dt

                published = _dt.datetime.fromtimestamp(
                    epoch, tz=_dt.timezone.utc
                ).strftime("%Y-%m-%d")
            out.append({
                "headline": title,
                "publisher": publisher,
                "published": published,
                "tone": "unknown",  # sentiment is the News Agent's job (LLM)
            })
        if not out:
            raise ValueError(f"yfinance returned no news for {ticker}")
        return out


class FallbackDataProvider:
    """Try the real provider per call; on any failure use mock data and
    say so in the payload (``used_fallback=True`` + source note)."""

    def __init__(self, primary, fallback=None):
        self.primary = primary
        self.fallback = fallback or MockDataProvider()
        self.name = f"{primary.name} (mock fallback on error)"
        self.last_error: str | None = None

    def _call(self, method: str, ticker: str):
        try:
            return getattr(self.primary, method)(ticker)
        except Exception as exc:  # network, bad ticker, rate limit, ...
            self.last_error = f"{type(exc).__name__}: {exc}"
            result = getattr(self.fallback, method)(ticker)
            note = f"mock fallback after {self.primary.name} error ({self.last_error})"
            if isinstance(result, dict):
                result = {**result, "source": note, "used_fallback": True}
            elif isinstance(result, list):
                result = [{**item, "tone": item.get("tone", "unknown"),
                           "source": note} for item in result]
            return result

    def market_snapshot(self, ticker: str) -> dict:
        return self._call("market_snapshot", ticker)

    def fundamentals(self, ticker: str) -> dict:
        return self._call("fundamentals", ticker)

    def news(self, ticker: str) -> list[dict]:
        return self._call("news", ticker)


def build_data_provider(settings):
    if settings.data_mode == "yfinance":
        return FallbackDataProvider(YFinanceProvider())
    return MockDataProvider()
