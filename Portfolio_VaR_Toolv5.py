
import datetime
import pandas as pd
from pandas.tseries.offsets import BDay
import pandas_datareader.data as web
import numpy as np
import math
import matplotlib as plt
import matplotlib.dates as mdates
from matplotlib import cm as cm
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
import re
import scipy.stats
import time
import wx.lib.pubsub
from wx.lib.pubsub import pub
import wx
from vartests import kupiec_test, duration_test
import fix_yahoo_finance as yf

# --- normalize price column names early ---
import pandas as pd
def _fix_adj_col(df):
    if df is None or getattr(df, "empty", True):
        return df
    if isinstance(df.columns, pd.MultiIndex):
        # top level is field name (e.g., 'Adj Close'); normalize to 'Adj close'
        df.rename(columns={"Adj Close": "Adj close"}, level=0, inplace=True)
    else:
        df.rename(columns={"Adj Close": "Adj close"}, inplace=True)
    return df

UI_BG_HEX = "#00175f"
# First tab

class PageOne(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        # Set first tab input fields + button

        fontbold = wx.Font(18, wx.DEFAULT, wx.NORMAL, wx.BOLD)

        title = wx.StaticText(self, wx.ID_ANY, 'Portfolio Tool')
        title.SetFont(fontbold)

        stock_a_label = wx.StaticText(self, -1, "Ticker Stock A", (20, 20))
        stock_b_label = wx.StaticText(self, -1, "Ticker Stock B", (20, 20))
        stock_c_label = wx.StaticText(self, -1, "Ticker Stock C", (20, 20))
        stock_d_label = wx.StaticText(self, -1, "Ticker Stock D", (20, 20))

        self.stock_a_ticker_input = wx.TextCtrl(self, size=(60, -1))
        self.stock_b_ticker_input = wx.TextCtrl(self, size=(60, -1))
        self.stock_c_ticker_input = wx.TextCtrl(self, size=(60, -1))
        self.stock_d_ticker_input = wx.TextCtrl(self, size=(60, -1))

        stock_a_weight_label = wx.StaticText(self, -1, "Initial weight Stock A", (20, 20))
        stock_b_weight_label= wx.StaticText(self, -1, "Initial weight Stock B", (20, 20))
        stock_c_weight_label = wx.StaticText(self, -1, "Initial weight Stock C", (20, 20))
        stock_d_weight_label = wx.StaticText(self, -1, "Initial weight Stock D", (20, 20))

        self.stock_a_weight_input = wx.TextCtrl(self, size=(60, -1))
        self.stock_b_weight_input = wx.TextCtrl(self, size=(60, -1))
        self.stock_c_weight_input = wx.TextCtrl(self, size=(60, -1))
        self.stock_d_weight_input = wx.TextCtrl(self, size=(60, -1))

        timeseries_label = wx.StaticText(self, -1, "Time series from: [dd/mm/yyyy]", (20, 20))
        self.timeseries_input = wx.TextCtrl(self, size=(85, -1))
        enddate_label = wx.StaticText(self, -1, "End date [dd/mm/yyyy]", (20, 20))
        self.enddate_input = wx.TextCtrl(self, size=(85, -1))


        benchmark_label = wx.StaticText(self, -1, "Benchmark", (20, 20))
        self.benchmark_input = wx.TextCtrl(self, size=(85, -1))

        background_a = wx.StaticText(self, -1, "> Stock weights should be decimals (i.e. 40% = 0.4)", (20, 20))
        background_a.SetForegroundColour(wx.YELLOW)
        self.SetBackgroundColour(self.GetParent().GetBackgroundColour())

        self.export = wx.CheckBox(self, label = 'Export data to CSV')

        button = wx.Button(self, label="Retrieve data",)
        self.Bind(wx.EVT_BUTTON, self.onRETRIEVE, button)

        # Put all of the above in a Sizer

        self.warning = wx.StaticText(self, -1, "", (20, 20))

        sizer = wx.GridBagSizer(10, 15)

        sizer.Add(title, (1, 0))

        sizer.Add(stock_a_label, (3, 0))
        sizer.Add(stock_b_label, (4, 0))
        sizer.Add(stock_c_label, (5, 0))
        sizer.Add(stock_d_label, (6, 0))

        sizer.Add(self.stock_a_ticker_input, (3, 2))
        sizer.Add(self.stock_b_ticker_input, (4, 2))
        sizer.Add(self.stock_c_ticker_input, (5, 2))
        sizer.Add(self.stock_d_ticker_input, (6, 2))

        sizer.Add(stock_a_weight_label, (3, 5))
        sizer.Add(stock_b_weight_label, (4, 5))
        sizer.Add(stock_c_weight_label, (5, 5))
        sizer.Add(stock_d_weight_label, (6, 5))

        sizer.Add(self.stock_a_weight_input, (3, 7))
        sizer.Add(self.stock_b_weight_input, (4, 7))
        sizer.Add(self.stock_c_weight_input, (5, 7))
        sizer.Add(self.stock_d_weight_input, (6, 7))

        sizer.Add(timeseries_label, (3, 9))
        sizer.Add(self.timeseries_input, (3, 11))
        # NEW: end date widgets
        sizer.Add(enddate_label, (4, 9))
        sizer.Add(self.enddate_input, (4, 11))
        sizer.SetHGap(15)
        sizer.SetVGap(10)

        
        sizer.Add(benchmark_label, (5, 9))
        sizer.Add(self.benchmark_input, (5, 11))

        sizer.Add(background_a, (6, 9))

        sizer.Add(self.export, (8, 9))

        sizer.Add(button, (9, 0))

        sizer.Add(self.warning, (11, 0))

        self.border = wx.BoxSizer()
        self.border.Add(sizer, 1, wx.ALL | wx.EXPAND, 5)

        self.SetSizerAndFit(self.border)

    def onRETRIEVE(self, event):

        # Get input values

        stock_a_ticker = self.stock_a_ticker_input.GetValue()
        stock_b_ticker = self.stock_b_ticker_input.GetValue()
        stock_c_ticker = self.stock_c_ticker_input.GetValue()
        stock_d_ticker = self.stock_d_ticker_input.GetValue()

        stock_a_weight = self.stock_a_weight_input.GetValue()
        stock_b_weight = self.stock_b_weight_input.GetValue()
        stock_c_weight = self.stock_c_weight_input.GetValue()
        stock_d_weight = self.stock_d_weight_input.GetValue()

        stocks = [stock_a_ticker, stock_b_ticker, stock_c_ticker, stock_d_ticker, ]

        # Check if the date was inserted correctly

        try:

            datetime.datetime.strptime(self.timeseries_input.GetValue(), '%d/%m/%Y')

            # Check if all stock weights are floats

            if re.match("^\d+?\.\d+?$", stock_a_weight) is None or re.match("^\d+?\.\d+?$", stock_b_weight) is None or re.match("^\d+?\.\d+?$", stock_c_weight) is None or re.match("^\d+?\.\d+?$", stock_d_weight) is None:

                self.warning.SetLabel("Stock weight should be a digit")

                # Check whether all fields are populated

            elif any(x == '' for x in stocks) or any(x == None for x in stocks) or self.benchmark_input.GetValue() == '':

                self.warning.SetLabel("One or more inputs are missing. Please insert all required values")

            else:

                weights = np.asarray([float(stock_a_weight), float(stock_b_weight), float(stock_c_weight), float(stock_d_weight), ])

                # Check whether the portfolio weights sum up to 1

                if not np.isclose(np.sum(weights), 1.0):
                    self.warning.SetLabel("Portfolio weights should sum up to 1")


                else:

                    try:

                        self.warning.SetLabel("")

                        parse_date = datetime.datetime.strptime(self.timeseries_input.GetValue(), '%d/%m/%Y')

                        # Get stock data (normalize columns first)
                        prices = _fix_adj_col(yf.download(stocks, start=parse_date.date()))

                        # Handle multi-index (many tickers) vs single ticker uniformly -> 'data' ends up with columns = tickers
                        if isinstance(prices.columns, pd.MultiIndex):
                            data = prices['Adj close'].copy()
                        else:
                            # single ticker case; make it a 1-col DF so downstream indexing works
                            data = prices[['Adj close']].copy()
                            data.columns = [stocks[0]]

                        data.sort_index(inplace=True, ascending=True)
                        data.index = pd.to_datetime(data.index)

                        time.sleep(5)

                        # Get benchmark data (normalize columns first)
                        bench_df = _fix_adj_col(yf.download(self.benchmark_input.GetValue(), start=parse_date.date()))

                        # yfinance/stooq may return a DF; select the 'Adj close' series cleanly
                        if isinstance(bench_df.columns, pd.MultiIndex):
                            # take the first (or only) ticker’s adjusted close
                            benchmark = bench_df['Adj close'].iloc[:, 0].copy()
                        else:
                            benchmark = bench_df['Adj close'].copy()

                        benchmark.sort_index(inplace=True, ascending=True)
                        benchmark.index = pd.to_datetime(benchmark.index)
                        
                        # De-duplicate dates and sort
                        data = data[~data.index.duplicated(keep="first")].sort_index()
                        benchmark = benchmark[~benchmark.index.duplicated(keep="first")].sort_index()

                        # Align on common dates
                        common = data.index.intersection(benchmark.index)
                        data = data.loc[common]
                        benchmark = benchmark.loc[common]

                        if len(data) < 3:
                            self.warning.SetLabel("Not enough overlapping dates after alignment. Try a different range/tickers.")
                            return


                        # Calculate headline metrics
                        returns = (data.pct_change()
                                .replace([np.inf, -np.inf], np.nan)
                                .dropna())
                        mean_daily_returns = returns.mean()
                        std = returns.std()

                        benchmark_returns = (benchmark.pct_change()
                                            .replace([np.inf, -np.inf], np.nan)
                                            .dropna())
                        benchmark_std = benchmark_returns.std()
                        
                        def _beta_series(x, y):
                            # align on common dates and drop NaNs => equal-length arrays for cov/var
                            df = pd.concat([x, y], axis=1, join="inner").dropna()
                            xv, yv = df.iloc[:, 0].values, df.iloc[:, 1].values
                            return np.cov(xv, yv)[0, 1] / np.var(yv, ddof=1)

                        def _te(x, y):
                            # tracking error = std of (asset return − benchmark return), aligned on dates
                            df = pd.concat([x, y], axis=1, join="inner").dropna()
                            return (df.iloc[:, 0] - df.iloc[:, 1]).std()


                        # Create headers

                        mean_daily_return_label = wx.StaticText(self, -1, "Historical mean daily return (%)", (20, 20))
                        expected_annual_return_label = wx.StaticText(self, -1, "Historical annual return (%)", (20, 20))
                        daily_std_label = wx.StaticText(self, -1, "Hist. standard deviation (%, daily)", (20, 20))
                        annual_std_label = wx.StaticText(self, -1, "Hist. standard Deviation (%, annual)", (20, 20))
                        sharpe_label = wx.StaticText(self, -1, "Hist. Sharpe Ratio (annual)", (20, 20))
                        TE_label = wx.StaticText(self, -1, "Ex-post Tracking Error", (20, 20))
                        Beta_label = wx.StaticText(self, -1, "Beta", (20, 20))

                        stock_a_header = wx.StaticText(self, -1, str(stocks[0]), (20, 20))
                        stock_b_header = wx.StaticText(self, -1, str(stocks[1]), (20, 20))
                        stock_c_header = wx.StaticText(self, -1, str(stocks[2]), (20, 20))
                        stock_d_header = wx.StaticText(self, -1, str(stocks[3]), (20, 20))
                        portfolio_header = wx.StaticText(self, -1, "Portfolio", (20, 20))
                        benchmark_header = wx.StaticText(self, -1, "Benchmark("+self.benchmark_input.GetValue()+")", (20, 20))

                        # Calculate basis for portfolio metrics
                        # Make weights numeric and defensively re-normalize (even though UI enforces sum=1)
                        w = np.asarray([float(stock_a_weight), float(stock_b_weight),
                                        float(stock_c_weight), float(stock_d_weight)], dtype=float)
                        w = w / np.sum(w)

                        # Constant weights, aligned to returns index
                        positions = {
                            stocks[0]: {returns.index[0]: w[0]},
                            stocks[1]: {returns.index[0]: w[1]},
                            stocks[2]: {returns.index[0]: w[2]},
                            stocks[3]: {returns.index[0]: w[3]},
                        }
                        pos = (pd.DataFrame.from_dict(positions)
                            .reindex(returns.index)
                            .ffill()
                            .astype(float))

                        # Cumulative growth per asset (base=1 at first valid return date)
                        growth = (1.0 + returns).cumprod(axis=0)

                        # Portfolio wealth = weighted sum of each asset's growth
                        portfolio = pos * growth
                        portfolio['total_wealth'] = portfolio[[stocks[0], stocks[1], stocks[2], stocks[3]]].sum(axis=1)

                        # Set base wealth = 1 at the first date >= (start + 1 business day), else first index
                        date = datetime.datetime.strptime(self.timeseries_input.GetValue(), "%d/%m/%Y")
                        base_target = (date + BDay(1))
                        idx = portfolio.index

                        # choose base date
                        base_loc = idx.searchsorted(pd.Timestamp(base_target))
                        if base_loc < len(idx):
                            base_date = idx[base_loc]
                        else:
                            base_date = idx[0]

                        # Rescale so base wealth = 1
                        if np.isfinite(portfolio.loc[base_date, 'total_wealth']) and portfolio.loc[base_date, 'total_wealth'] != 0:
                            portfolio['total_wealth'] = portfolio['total_wealth'] / portfolio.loc[base_date, 'total_wealth']

                        # Portfolio returns from wealth, clean non-finites
                        portfolio['returns'] = portfolio['total_wealth'].pct_change()
                        portfolio.replace([np.inf, -np.inf], np.nan, inplace=True)
                        
                        # if portfolio['returns'].isna().any():
                        #     self.warning.SetLabel("Note: NaNs in portfolio returns were dropped (short range or missing data).")

                        # Calculate + insert specific stock, benchmark and portfolio metrics
                        stock_a_mean_daily_return = wx.StaticText(self, -1, str(round(mean_daily_returns[stocks[0]]*100, 2)), (20, 20))
                        stock_b_mean_daily_return = wx.StaticText(self, -1, str(round(mean_daily_returns[stocks[1]]*100, 2)), (20, 20))
                        stock_c_mean_daily_return = wx.StaticText(self, -1, str(round(mean_daily_returns[stocks[2]]*100, 2)), (20, 20))
                        stock_d_mean_daily_return = wx.StaticText(self, -1, str(round(mean_daily_returns[stocks[3]]*100, 2)), (20, 20))
                        portfolio_mean_daily_return = portfolio["returns"].mean()
                        portfolio_mean_daily_return_scr = wx.StaticText(self, -1, str(round(portfolio_mean_daily_return * 100, 2)), (20, 20))
                        benchmark_mean_daily_return = wx.StaticText(self, -1, str(round(benchmark_returns.mean() * 100, 2)), (20, 20))

                        stock_a_annual_return = wx.StaticText(self, -1, str(round(mean_daily_returns[stocks[0]]*100*252, 2)), (20, 20))
                        stock_b_annual_return = wx.StaticText(self, -1, str(round(mean_daily_returns[stocks[1]]*100*252, 2)), (20, 20))
                        stock_c_annual_return = wx.StaticText(self, -1, str(round(mean_daily_returns[stocks[2]]*100*252, 2)), (20, 20))
                        stock_d_annual_return = wx.StaticText(self, -1, str(round(mean_daily_returns[stocks[3]]*100*252, 2)), (20, 20))
                        portfolio_annual_return = wx.StaticText(self, -1, str(round(portfolio_mean_daily_return  * 100 * 252, 2)), (20, 20))
                        benchmark_annual_return = wx.StaticText(self, -1, str(round(benchmark_returns.mean()  * 100 * 252, 2)), (20, 20))

                        stock_a_daily_std = wx.StaticText(self, -1, str(round(std[stocks[0]]*100, 2)), (20, 20))
                        stock_b_daily_std = wx.StaticText(self, -1, str(round(std[stocks[1]]*100, 2)), (20, 20))
                        stock_c_daily_std = wx.StaticText(self, -1, str(round(std[stocks[2]]*100, 2)), (20, 20))
                        stock_d_daily_std = wx.StaticText(self, -1, str(round(std[stocks[3]]*100, 2)), (20, 20))
                        portfolio_daily_std = portfolio["returns"].std()
                        portfolio_daily_std_scr = wx.StaticText(self, -1, str(round(portfolio_daily_std * 100, 2)), (20, 20))
                        benchmark_daily_std = wx.StaticText(self, -1, str(round(benchmark_std * 100, 2)), (20, 20))

                        stock_a_annual_std = wx.StaticText(self, -1, str(round(std[stocks[0]] * 100 * np.sqrt(252), 2)), (20, 20))
                        stock_b_annual_std = wx.StaticText(self, -1, str(round(std[stocks[1]] * 100 * np.sqrt(252), 2)), (20, 20))
                        stock_c_annual_std = wx.StaticText(self, -1, str(round(std[stocks[2]] * 100 * np.sqrt(252), 2)), (20, 20))
                        stock_d_annual_std = wx.StaticText(self, -1, str(round(std[stocks[3]] * 100 * np.sqrt(252), 2)), (20, 20))
                        portfolio_annual_std = wx.StaticText(self, -1, str(round(portfolio_daily_std * 100 * np.sqrt(252), 2)), (20, 20))
                        benchmark_annual_std = wx.StaticText(self, -1, str(round(benchmark_std * 100 * np.sqrt(252), 2)), (20, 20))

                        risk_free_rate = 2.25 # 10 year US-treasury rate (annual)

                        sharpe_a = ((mean_daily_returns[stocks[0]] * 100 * 252) -  risk_free_rate ) / (std[stocks[0]] * 100 * np.sqrt(252))
                        sharpe_b = ((mean_daily_returns[stocks[1]] * 100 * 252) - risk_free_rate) / (std[stocks[1]] * 100 * np.sqrt(252))
                        sharpe_c = ((mean_daily_returns[stocks[2]] * 100 * 252) - risk_free_rate) / (std[stocks[2]] * 100 * np.sqrt(252))
                        sharpe_d = ((mean_daily_returns[stocks[3]] * 100 * 252) - risk_free_rate) / (std[stocks[3]] * 100 * np.sqrt(252))
                        sharpe_portfolio = ((portfolio_mean_daily_return * 100 * 252) - risk_free_rate) / (portfolio_daily_std * 100 * np.sqrt(252))
                        sharpe_benchmark = ((benchmark_returns.mean() * 100 * 252) - risk_free_rate) / (benchmark_std * 100 * np.sqrt(252))

                        sharpe_a_scr = wx.StaticText(self, -1, str(round(sharpe_a, 2)),(20, 20))
                        sharpe_b_scr = wx.StaticText(self, -1, str(round(sharpe_b, 2)), (20, 20))
                        sharpe_c_scr = wx.StaticText(self, -1, str(round(sharpe_c, 2)), (20, 20))
                        sharpe_d_scr = wx.StaticText(self, -1, str(round(sharpe_d, 2)), (20, 20))
                        sharpe_portfolio_scr = wx.StaticText(self, -1, str(round(sharpe_portfolio, 2)), (20, 20))
                        sharpe_benchmark_scr = wx.StaticText(self, -1, str(round(sharpe_benchmark, 2)), (20, 20))

                        # Tracking error (date-aligned)
                        TE_a = _te(returns[stocks[0]], benchmark_returns)
                        TE_b = _te(returns[stocks[1]], benchmark_returns)
                        TE_c = _te(returns[stocks[2]], benchmark_returns)
                        TE_d = _te(returns[stocks[3]], benchmark_returns)
                        TE_p = _te(portfolio["returns"], benchmark_returns)

                        TE_stock_a = wx.StaticText(self, -1, str(round(TE_a * 100, 2)), (20, 20))
                        TE_stock_b = wx.StaticText(self, -1, str(round(TE_b * 100, 2)), (20, 20))
                        TE_stock_c = wx.StaticText(self, -1, str(round(TE_c * 100, 2)), (20, 20))
                        TE_stock_d = wx.StaticText(self, -1, str(round(TE_d * 100, 2)), (20, 20))
                        TE_portfolio = wx.StaticText(self, -1, str(round(TE_p * 100, 2)), (20, 20))

                        # Betas (date-aligned)
                        beta_a = _beta_series(returns[stocks[0]], benchmark_returns)
                        beta_b = _beta_series(returns[stocks[1]], benchmark_returns)
                        beta_c = _beta_series(returns[stocks[2]], benchmark_returns)
                        beta_d = _beta_series(returns[stocks[3]], benchmark_returns)
                        beta_p = _beta_series(portfolio["returns"].dropna(), benchmark_returns)

                        beta_a_lab = wx.StaticText(self, -1, str(round(beta_a, 2)), (20, 20))
                        beta_b_lab = wx.StaticText(self, -1, str(round(beta_b, 2)), (20, 20))
                        beta_c_lab = wx.StaticText(self, -1, str(round(beta_c, 2)), (20, 20))
                        beta_d_lab = wx.StaticText(self, -1, str(round(beta_d, 2)), (20, 20))
                        beta_p_lab = wx.StaticText(self, -1, str(round(beta_p, 2)), (20, 20))

                        # Put all the metrics in a Sizer

                        sizer = wx.GridBagSizer(10, 10)

                        sizer.Add(mean_daily_return_label, (12, 0))
                        sizer.Add(expected_annual_return_label, (13, 0))
                        sizer.Add(daily_std_label, (14, 0))
                        sizer.Add(annual_std_label, (15, 0))
                        sizer.Add(sharpe_label, (16, 0))
                        sizer.Add(TE_label, (17, 0))
                        sizer.Add(Beta_label, (18, 0))

                        sizer.Add(stock_a_header, (11, 2))
                        sizer.Add(stock_b_header, (11, 4))
                        sizer.Add(stock_c_header, (11, 6))
                        sizer.Add(stock_d_header, (11, 8))
                        sizer.Add(portfolio_header, (11, 11))
                        sizer.Add(benchmark_header, (11, 13))

                        sizer.Add(stock_a_mean_daily_return, (12, 2))
                        sizer.Add(stock_b_mean_daily_return, (12, 4))
                        sizer.Add(stock_c_mean_daily_return, (12, 6))
                        sizer.Add(stock_d_mean_daily_return, (12, 8))
                        sizer.Add(portfolio_mean_daily_return_scr, (12, 11))
                        sizer.Add(benchmark_mean_daily_return, (12, 13))

                        sizer.Add(stock_a_annual_return, (13, 2))
                        sizer.Add(stock_b_annual_return, (13, 4))
                        sizer.Add(stock_c_annual_return, (13, 6))
                        sizer.Add(stock_d_annual_return, (13, 8))
                        sizer.Add(portfolio_annual_return, (13, 11))
                        sizer.Add(benchmark_annual_return, (13, 13))

                        sizer.Add(stock_a_daily_std, (14, 2))
                        sizer.Add(stock_b_daily_std, (14, 4))
                        sizer.Add(stock_c_daily_std, (14, 6))
                        sizer.Add(stock_d_daily_std, (14, 8))
                        sizer.Add(portfolio_daily_std_scr, (14, 11))
                        sizer.Add(benchmark_daily_std, (14, 13))

                        sizer.Add(stock_a_annual_std, (15, 2))
                        sizer.Add(stock_b_annual_std, (15, 4))
                        sizer.Add(stock_c_annual_std, (15, 6))
                        sizer.Add(stock_d_annual_std, (15, 8))
                        sizer.Add(portfolio_annual_std, (15, 11))
                        sizer.Add(benchmark_annual_std, (15, 13))

                        sizer.Add(sharpe_a_scr, (16, 2))
                        sizer.Add(sharpe_b_scr, (16, 4))
                        sizer.Add(sharpe_c_scr, (16, 6))
                        sizer.Add(sharpe_d_scr, (16, 8))
                        sizer.Add(sharpe_portfolio_scr, (16, 11))
                        sizer.Add(sharpe_benchmark_scr, (16, 13))

                        sizer.Add(TE_stock_a, (17, 2))
                        sizer.Add(TE_stock_b, (17, 4))
                        sizer.Add(TE_stock_c, (17, 6))
                        sizer.Add(TE_stock_d, (17, 8))
                        sizer.Add(TE_portfolio, (17, 11))

                        sizer.Add(beta_a_lab, (18, 2))
                        sizer.Add(beta_b_lab, (18, 4))
                        sizer.Add(beta_c_lab, (18, 6))
                        sizer.Add(beta_d_lab, (18, 8))
                        sizer.Add(beta_p_lab, (18, 11))

                        self.border = wx.BoxSizer()
                        self.border.Add(sizer, 1, wx.ALL | wx.EXPAND, 5)

                        self.SetSizerAndFit(self.border)

                        # Make the headline data available to the other tabs by means of PubSub

                        pub.sendMessage("panelListener", arg1 = data, arg2 = weights, arg3 = stocks, arg4 = portfolio)

                        # Export price-date from Yahoo to CSV if box is ticked

                        if self.export.GetValue() == True:

                            data.to_csv("data"+stock_a_ticker+"to"+stock_d_ticker+".csv", sep=';', encoding='utf-8')

                        else:
                            pass

                    except Exception as e:

                        self.warning.SetLabel(str(e))

        except ValueError:

            self.warning.SetLabel("Date not in the right format")

# Second tab

class PageTwo(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        pub.subscribe(self.myListener, "panelListener")
        self.SetBackgroundColour(self.GetParent().GetBackgroundColour())

    def myListener(self, arg1, arg2, arg3, arg4):

        # import variables

        data_2 = arg1
        stocks_2 = arg3
        portfolio_2 = arg4.copy()  # <-- make a copy so we don't mutate the shared object

        # keep the rename, but now it's only on our copy
        portfolio_2.rename(columns={'returns': 'Portfolio'}, inplace=True)

        returns = (data_2.pct_change()
           .replace([np.inf, -np.inf], np.nan)
           .dropna())
        portfolio_2["Portfolio"] = portfolio_2["Portfolio"].replace([np.inf, -np.inf], np.nan)

        # Create histogram of daily returns
        figure_1 = Figure(figsize=(7, 2.5))
        figure_1.tight_layout()
        canvas_1 = FigureCanvas(self, -1, figure_1)
        ax = figure_1.add_subplot(111)

        ax.hist(returns[stocks_2[0]], bins=50, density=True, histtype='stepfilled', alpha=0.5, label=stocks_2[0])
        ax.hist(returns[stocks_2[1]], bins=50, density=True, histtype='stepfilled', alpha=0.5, label=stocks_2[1])
        ax.hist(returns[stocks_2[2]], bins=50, density=True, histtype='stepfilled', alpha=0.5, label=stocks_2[2])
        ax.hist(returns[stocks_2[3]], bins=50, density=True, histtype='stepfilled', alpha=0.5, label=stocks_2[3])
        ax.hist(portfolio_2["Portfolio"].dropna(), bins=50, density=True, histtype='stepfilled', alpha=0.5, label="Portfolio")

        ax.set_title(u"Historic return distribution", weight='bold')
        ax.legend(loc='upper left')

        # Create indexed performance chart

        figure_2 = Figure(figsize=(7, 2.5))
        canvas_2 = FigureCanvas(self, -1, figure_2)
        ax2 = figure_2.add_subplot(111)

        years = mdates.YearLocator()
        yearsFmt = mdates.DateFormatter("'%y")

        ret_index = (1 + returns).cumprod()
        portfolio_cum = (1 + portfolio_2["Portfolio"].dropna()).cumprod()

        for t in stocks_2:
            ax2.plot(ret_index.index, ret_index[t], label=t)

        ax2.plot(portfolio_cum.index, portfolio_cum, label="Portfolio", linewidth=2)

        ax2.xaxis.set_major_locator(years)
        ax2.xaxis.set_major_formatter(yearsFmt)
        ax2.set_title(u"Indexed Performance (base = 1)", weight='bold')
        ax2.legend(loc='upper left')

        # improve spacing
        figure_2.autofmt_xdate()
        figure_2.tight_layout()

        sizer = wx.GridBagSizer(7, 3)
        sizer.Add(canvas_1, (1, 0))
        sizer.Add(canvas_2, (2, 0))

        self.border = wx.BoxSizer()
        self.border.Add(sizer, 1, wx.ALL | wx.EXPAND, 5)

        self.SetSizerAndFit(self.border)

# Third tab
class PageThree(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        pub.subscribe(self.myListener, "panelListener")
        self.SetBackgroundColour(self.GetParent().GetBackgroundColour())

    def myListener(self, arg1, arg2, arg3, arg4):
        try:
            # ---------- hard reset: clear previous controls/sizer ----------
            try:
                # Destroy all child windows so we start clean
                for child in self.GetChildren():
                    try:
                        child.Destroy()
                    except:
                        pass
                # Detach any existing sizer
                self.SetSizer(None)
            except:
                pass

            fontbold = wx.Font(18, wx.DEFAULT, wx.NORMAL, wx.BOLD)

            # ---------- inputs from PageOne ----------
            data_3      = arg1   # DataFrame of Adj close (Stooq), columns=tickers
            stocks_3    = arg3   # list of 4 tickers
            weights_3   = arg2   # kept for completeness
            portfolio_3 = arg4   # DataFrame with 'returns' or 'Portfolio'

            # choose portfolio returns column
            port_col = 'returns' if 'returns' in portfolio_3.columns else (
                'Portfolio' if 'Portfolio' in portfolio_3.columns else None
            )
            if port_col is None:
                msg = wx.StaticText(self, -1, "Portfolio returns column missing.")
                wrap = wx.BoxSizer(wx.VERTICAL); wrap.Add(msg, 0, wx.ALL, 8)
                self.SetSizerAndFit(wrap)
                return

            # ---------- clean series ----------
            returns = (
                data_3.pct_change()
                      .replace([np.inf, -np.inf], np.nan)
                      .dropna()
            )
            port_ret = (
                portfolio_3[port_col]
                .replace([np.inf, -np.inf], np.nan)
                .dropna()
            )

            if returns.empty or port_ret.empty:
                msg = wx.StaticText(self, -1, "Not enough return data for VaR; try different dates/tickers.")
                wrap = wx.BoxSizer(wx.VERTICAL); wrap.Add(msg, 0, wx.ALL, 8)
                self.SetSizerAndFit(wrap)
                return

            # ---------- stats ----------
            mean_daily_returns     = returns.mean()
            std                    = returns.std()
            portfolio_return_daily = port_ret.mean()
            portfolio_std          = port_ret.std()

            # ---------- optional vartests ----------
            try:
                import vartests as vt
            except ImportError:
                vt = None

            # ---------- VaR/ES config ----------
            import scipy.stats
            conf_95, conf_99 = 0.95, 0.99
            alpha_95, alpha_99 = 1.0 - conf_95, 1.0 - conf_99   # 0.05 and 0.01 (left tail)

            def _ppf(alpha, mu, sd):
                if sd is None or np.isnan(sd) or sd == 0:
                    return np.nan
                return scipy.stats.norm.ppf(alpha, mu, sd)

            def _hist_es(series, alpha):
                if series is None or len(series) == 0:
                    return np.nan
                q = series.quantile(alpha)
                tail = series[series <= q]
                return np.nan if tail.empty else tail.mean()

            def _param_es(mu, sd, alpha):
                if sd is None or np.isnan(sd) or sd == 0:
                    return np.nan
                z = scipy.stats.norm.ppf(alpha)
                phi = scipy.stats.norm.pdf(z)
                return mu - sd * (phi / alpha)

            # =====================================================================
            #                       HISTORICAL  (VaR & ES)
            # =====================================================================
            title_historical = wx.StaticText(self, wx.ID_ANY, 'VaR / ES - Historical Simulation')
            title_historical.SetFont(fontbold)

            # Labels
            stock_a_hist_var95_lab = wx.StaticText(self, -1, f"{stocks_3[0]} - VaR (95%)")
            stock_b_hist_var95_lab = wx.StaticText(self, -1, f"{stocks_3[1]} - VaR (95%)")
            stock_c_hist_var95_lab = wx.StaticText(self, -1, f"{stocks_3[2]} - VaR (95%)")
            stock_d_hist_var95_lab = wx.StaticText(self, -1, f"{stocks_3[3]} - VaR (95%)")
            portfolio_hist_var95_lab = wx.StaticText(self, -1, "Portfolio - VaR (95%)")

            stock_a_hist_var99_lab = wx.StaticText(self, -1, f"{stocks_3[0]} - VaR (99%)")
            stock_b_hist_var99_lab = wx.StaticText(self, -1, f"{stocks_3[1]} - VaR (99%)")
            stock_c_hist_var99_lab = wx.StaticText(self, -1, f"{stocks_3[2]} - VaR (99%)")
            stock_d_hist_var99_lab = wx.StaticText(self, -1, f"{stocks_3[3]} - VaR (99%)")
            portfolio_hist_var99_lab = wx.StaticText(self, -1, "Portfolio - VaR (99%)")

            stock_a_hist_es95_lab = wx.StaticText(self, -1, f"{stocks_3[0]} - ES (95%)")
            stock_b_hist_es95_lab = wx.StaticText(self, -1, f"{stocks_3[1]} - ES (95%)")
            stock_c_hist_es95_lab = wx.StaticText(self, -1, f"{stocks_3[2]} - ES (95%)")
            stock_d_hist_es95_lab = wx.StaticText(self, -1, f"{stocks_3[3]} - ES (95%)")
            portfolio_hist_es95_lab = wx.StaticText(self, -1, "Portfolio - ES (95%)")

            # stock_a_hist_es99_lab = wx.StaticText(self, -1, f"{stocks_3[0]} - ES (99%)")
            # stock_b_hist_es99_lab = wx.StaticText(self, -1, f"{stocks_3[1]} - ES (99%)")
            # stock_c_hist_es99_lab = wx.StaticText(self, -1, f"{stocks_3[2]} - ES (99%)")
            # stock_d_hist_es99_lab = wx.StaticText(self, -1, f"{stocks_3[3]} - ES (99%)")
            # portfolio_hist_es99_lab = wx.StaticText(self, -1, "Portfolio - ES (99%)")

            # Values (%)
            stock_a_hist_var95 = wx.StaticText(self, -1, str(round(returns[stocks_3[0]].quantile(alpha_95) * 100, 2)))
            stock_b_hist_var95 = wx.StaticText(self, -1, str(round(returns[stocks_3[1]].quantile(alpha_95) * 100, 2)))
            stock_c_hist_var95 = wx.StaticText(self, -1, str(round(returns[stocks_3[2]].quantile(alpha_95) * 100, 2)))
            stock_d_hist_var95 = wx.StaticText(self, -1, str(round(returns[stocks_3[3]].quantile(alpha_95) * 100, 2)))
            portfolio_hist_var95 = wx.StaticText(self, -1, str(round(port_ret.quantile(alpha_95) * 100, 2)))

            stock_a_hist_var99 = wx.StaticText(self, -1, str(round(returns[stocks_3[0]].quantile(alpha_99) * 100, 2)))
            stock_b_hist_var99 = wx.StaticText(self, -1, str(round(returns[stocks_3[1]].quantile(alpha_99) * 100, 2)))
            stock_c_hist_var99 = wx.StaticText(self, -1, str(round(returns[stocks_3[2]].quantile(alpha_99) * 100, 2)))
            stock_d_hist_var99 = wx.StaticText(self, -1, str(round(returns[stocks_3[3]].quantile(alpha_99) * 100, 2)))
            portfolio_hist_var99 = wx.StaticText(self, -1, str(round(port_ret.quantile(alpha_99) * 100, 2)))

            stock_a_hist_es95 = wx.StaticText(self, -1, str(round(_hist_es(returns[stocks_3[0]], alpha_95) * 100, 2)))
            stock_b_hist_es95 = wx.StaticText(self, -1, str(round(_hist_es(returns[stocks_3[1]], alpha_95) * 100, 2)))
            stock_c_hist_es95 = wx.StaticText(self, -1, str(round(_hist_es(returns[stocks_3[2]], alpha_95) * 100, 2)))
            stock_d_hist_es95 = wx.StaticText(self, -1, str(round(_hist_es(returns[stocks_3[3]], alpha_95) * 100, 2)))
            portfolio_hist_es95 = wx.StaticText(self, -1, str(round(_hist_es(port_ret,            alpha_95) * 100, 2)))

            # stock_a_hist_es99 = wx.StaticText(self, -1, str(round(_hist_es(returns[stocks_3[0]], alpha_99) * 100, 2)))
            # stock_b_hist_es99 = wx.StaticText(self, -1, str(round(_hist_es(returns[stocks_3[1]], alpha_99) * 100, 2)))
            # stock_c_hist_es99 = wx.StaticText(self, -1, str(round(_hist_es(returns[stocks_3[2]], alpha_99) * 100, 2)))
            # stock_d_hist_es99 = wx.StaticText(self, -1, str(round(_hist_es(returns[stocks_3[3]], alpha_99) * 100, 2)))
            # portfolio_hist_es99 = wx.StaticText(self, -1, str(round(_hist_es(port_ret,            alpha_99) * 100, 2)))

            # =====================================================================
            #                 VARIANCE–COVARIANCE (Normal)  (VaR & ES)
            # =====================================================================
            title_varcov = wx.StaticText(self, wx.ID_ANY, 'VaR / ES - Variance Covariance (Normal)')
            title_varcov.SetFont(fontbold)

            stock_a_cov_var95_lab = wx.StaticText(self, -1, f"{stocks_3[0]} - VaR (95%)")
            stock_b_cov_var95_lab = wx.StaticText(self, -1, f"{stocks_3[1]} - VaR (95%)")
            stock_c_cov_var95_lab = wx.StaticText(self, -1, f"{stocks_3[2]} - VaR (95%)")
            stock_d_cov_var95_lab = wx.StaticText(self, -1, f"{stocks_3[3]} - VaR (95%)")
            portfolio_cov_var95_lab = wx.StaticText(self, -1, "Portfolio - VaR (95%)")

            stock_a_cov_var99_lab = wx.StaticText(self, -1, f"{stocks_3[0]} - VaR (99%)")
            stock_b_cov_var99_lab = wx.StaticText(self, -1, f"{stocks_3[1]} - VaR (99%)")
            stock_c_cov_var99_lab = wx.StaticText(self, -1, f"{stocks_3[2]} - VaR (99%)")
            stock_d_cov_var99_lab = wx.StaticText(self, -1, f"{stocks_3[3]} - VaR (99%)")
            portfolio_cov_var99_lab = wx.StaticText(self, -1, "Portfolio - VaR (99%)")

            stock_a_cov_es95_lab = wx.StaticText(self, -1, f"{stocks_3[0]} - ES (95%)")
            stock_b_cov_es95_lab = wx.StaticText(self, -1, f"{stocks_3[1]} - ES (95%)")
            stock_c_cov_es95_lab = wx.StaticText(self, -1, f"{stocks_3[2]} - ES (95%)")
            stock_d_cov_es95_lab = wx.StaticText(self, -1, f"{stocks_3[3]} - ES (95%)")
            portfolio_cov_es95_lab = wx.StaticText(self, -1, "Portfolio - ES (95%)")

            # stock_a_cov_es99_lab = wx.StaticText(self, -1, f"{stocks_3[0]} - ES (99%)")
            # stock_b_cov_es99_lab = wx.StaticText(self, -1, f"{stocks_3[1]} - ES (99%)")
            # stock_c_cov_es99_lab = wx.StaticText(self, -1, f"{stocks_3[2]} - ES (99%)")
            # stock_d_cov_es99_lab = wx.StaticText(self, -1, f"{stocks_3[3]} - ES (99%)")
            # portfolio_cov_es99_lab = wx.StaticText(self, -1, "Portfolio - ES (99%)")

            stock_a_cov_var95 = wx.StaticText(self, -1, str(round(_ppf(alpha_95, mean_daily_returns[stocks_3[0]], std[stocks_3[0]]) * 100, 2)))
            stock_b_cov_var95 = wx.StaticText(self, -1, str(round(_ppf(alpha_95, mean_daily_returns[stocks_3[1]], std[stocks_3[1]]) * 100, 2)))
            stock_c_cov_var95 = wx.StaticText(self, -1, str(round(_ppf(alpha_95, mean_daily_returns[stocks_3[2]], std[stocks_3[2]]) * 100, 2)))
            stock_d_cov_var95 = wx.StaticText(self, -1, str(round(_ppf(alpha_95, mean_daily_returns[stocks_3[3]], std[stocks_3[3]]) * 100, 2)))
            portfolio_cov_var95 = wx.StaticText(self, -1, str(round(_ppf(alpha_95, portfolio_return_daily,        portfolio_std) * 100, 2)))

            stock_a_cov_var99 = wx.StaticText(self, -1, str(round(_ppf(alpha_99, mean_daily_returns[stocks_3[0]], std[stocks_3[0]]) * 100, 2)))
            stock_b_cov_var99 = wx.StaticText(self, -1, str(round(_ppf(alpha_99, mean_daily_returns[stocks_3[1]], std[stocks_3[1]]) * 100, 2)))
            stock_c_cov_var99 = wx.StaticText(self, -1, str(round(_ppf(alpha_99, mean_daily_returns[stocks_3[2]], std[stocks_3[2]]) * 100, 2)))
            stock_d_cov_var99 = wx.StaticText(self, -1, str(round(_ppf(alpha_99, mean_daily_returns[stocks_3[3]], std[stocks_3[3]]) * 100, 2)))
            portfolio_cov_var99 = wx.StaticText(self, -1, str(round(_ppf(alpha_99, portfolio_return_daily,        portfolio_std) * 100, 2)))

            stock_a_cov_es95 = wx.StaticText(self, -1, str(round(_param_es(mean_daily_returns[stocks_3[0]], std[stocks_3[0]], alpha_95) * 100, 2)))
            stock_b_cov_es95 = wx.StaticText(self, -1, str(round(_param_es(mean_daily_returns[stocks_3[1]], std[stocks_3[1]], alpha_95) * 100, 2)))
            stock_c_cov_es95 = wx.StaticText(self, -1, str(round(_param_es(mean_daily_returns[stocks_3[2]], std[stocks_3[2]], alpha_95) * 100, 2)))
            stock_d_cov_es95 = wx.StaticText(self, -1, str(round(_param_es(mean_daily_returns[stocks_3[3]], std[stocks_3[3]], alpha_95) * 100, 2)))
            portfolio_cov_es95 = wx.StaticText(self, -1, str(round(_param_es(portfolio_return_daily,        portfolio_std,        alpha_95) * 100, 2)))

            # stock_a_cov_es99 = wx.StaticText(self, -1, str(round(_param_es(mean_daily_returns[stocks_3[0]], std[stocks_3[0]], alpha_99) * 100, 2)))
            # stock_b_cov_es99 = wx.StaticText(self, -1, str(round(_param_es(mean_daily_returns[stocks_3[1]], std[stocks_3[1]], alpha_99) * 100, 2)))
            # stock_c_cov_es99 = wx.StaticText(self, -1, str(round(_param_es(mean_daily_returns[stocks_3[2]], std[stocks_3[2]], alpha_99) * 100, 2)))
            # stock_d_cov_es99 = wx.StaticText(self, -1, str(round(_param_es(mean_daily_returns[stocks_3[3]], std[stocks_3[3]], alpha_99) * 100, 2)))
            # portfolio_cov_es99 = wx.StaticText(self, -1, str(round(_param_es(portfolio_return_daily,        portfolio_std,        alpha_99) * 100, 2)))

            # =====================================================================
            #                    MONTE CARLO (GBM) (VaR & ES)
            # =====================================================================
            title_MC = wx.StaticText(self, wx.ID_ANY, 'VaR / ES - Monte Carlo (Geometric Brownian Motion)')
            title_MC.SetFont(fontbold)

            MC_var95_vals, MC_var99_vals, MC_es95_vals, MC_es99_vals = [], [], [], []
            for item in range(len(stocks_3)):
                S   = data_3[stocks_3[item]].iloc[-1]
                T   = 252
                mu  = returns[stocks_3[item]].mean() * 252
                vol = returns[stocks_3[item]].std()  * np.sqrt(252)

                sims = 1000
                ret_list = []
                for _ in range(sims):
                    daily = np.random.normal(mu / T, vol / math.sqrt(T), T) + 1.0
                    final_price = S * daily.prod()
                    ret_list.append((final_price - S) / S)

                ret_arr = np.array(ret_list)
                v95 = np.percentile(ret_arr, 100 * alpha_95)
                v99 = np.percentile(ret_arr, 100 * alpha_99)
                es95 = ret_arr[ret_arr <= v95].mean() if np.any(ret_arr <= v95) else np.nan
                es99 = ret_arr[ret_arr <= v99].mean() if np.any(ret_arr <= v99) else np.nan

                MC_var95_vals.append(v95); MC_var99_vals.append(v99)
                MC_es95_vals.append(es95); MC_es99_vals.append(es99)

            stock_a_MC_var95_lab = wx.StaticText(self, -1, f"{stocks_3[0]} - VaR (95%)")
            stock_b_MC_var95_lab = wx.StaticText(self, -1, f"{stocks_3[1]} - VaR (95%)")
            stock_c_MC_var95_lab = wx.StaticText(self, -1, f"{stocks_3[2]} - VaR (95%)")
            stock_d_MC_var95_lab = wx.StaticText(self, -1, f"{stocks_3[3]} - VaR (95%)")

            stock_a_MC_var99_lab = wx.StaticText(self, -1, f"{stocks_3[0]} - VaR (99%)")
            stock_b_MC_var99_lab = wx.StaticText(self, -1, f"{stocks_3[1]} - VaR (99%)")
            stock_c_MC_var99_lab = wx.StaticText(self, -1, f"{stocks_3[2]} - VaR (99%)")
            stock_d_MC_var99_lab = wx.StaticText(self, -1, f"{stocks_3[3]} - VaR (99%)")

            stock_a_MC_es95_lab = wx.StaticText(self, -1, f"{stocks_3[0]} - ES (95%)")
            stock_b_MC_es95_lab = wx.StaticText(self, -1, f"{stocks_3[1]} - ES (95%)")
            stock_c_MC_es95_lab = wx.StaticText(self, -1, f"{stocks_3[2]} - ES (95%)")
            stock_d_MC_es95_lab = wx.StaticText(self, -1, f"{stocks_3[3]} - ES (95%)")

            # stock_a_MC_es99_lab = wx.StaticText(self, -1, f"{stocks_3[0]} - ES (99%)")
            # stock_b_MC_es99_lab = wx.StaticText(self, -1, f"{stocks_3[1]} - ES (99%)")
            # stock_c_MC_es99_lab = wx.StaticText(self, -1, f"{stocks_3[2]} - ES (99%)")
            # stock_d_MC_es99_lab = wx.StaticText(self, -1, f"{stocks_3[3]} - ES (99%)")

            stock_a_MC_var95 = wx.StaticText(self, -1, str(round(MC_var95_vals[0] * 100, 2)))
            stock_b_MC_var95 = wx.StaticText(self, -1, str(round(MC_var95_vals[1] * 100, 2)))
            stock_c_MC_var95 = wx.StaticText(self, -1, str(round(MC_var95_vals[2] * 100, 2)))
            stock_d_MC_var95 = wx.StaticText(self, -1, str(round(MC_var95_vals[3] * 100, 2)))

            stock_a_MC_var99 = wx.StaticText(self, -1, str(round(MC_var99_vals[0] * 100, 2)))
            stock_b_MC_var99 = wx.StaticText(self, -1, str(round(MC_var99_vals[1] * 100, 2)))
            stock_c_MC_var99 = wx.StaticText(self, -1, str(round(MC_var99_vals[2] * 100, 2)))
            stock_d_MC_var99 = wx.StaticText(self, -1, str(round(MC_var99_vals[3] * 100, 2)))

            stock_a_MC_es95 = wx.StaticText(self, -1, str(round(MC_es95_vals[0] * 100, 2)))
            stock_b_MC_es95 = wx.StaticText(self, -1, str(round(MC_es95_vals[1] * 100, 2)))
            stock_c_MC_es95 = wx.StaticText(self, -1, str(round(MC_es95_vals[2] * 100, 2)))
            stock_d_MC_es95 = wx.StaticText(self, -1, str(round(MC_es95_vals[3] * 100, 2)))

            # stock_a_MC_es99 = wx.StaticText(self, -1, str(round(MC_es99_vals[0] * 100, 2)))
            # stock_b_MC_es99 = wx.StaticText(self, -1, str(round(MC_es99_vals[1] * 100, 2)))
            # stock_c_MC_es99 = wx.StaticText(self, -1, str(round(MC_es99_vals[2] * 100, 2)))
            # stock_d_MC_es99 = wx.StaticText(self, -1, str(round(MC_es99_vals[3] * 100, 2)))

            # =====================================================================
            #                      VaR BACKTESTS (Portfolio)
            # =====================================================================
            alpha_bt = 0.05              # rolling HS VaR at 95% confidence
            window   = 250               # ~1 year
            roll_var = port_ret.rolling(window).quantile(alpha_bt).shift(1)  # past-only
            bt_df = (port_ret.to_frame("ret").join(roll_var.to_frame("var"), how="inner").dropna())
            violations = (bt_df["ret"] < bt_df["var"]).astype(int).tolist()

            title_bt = wx.StaticText(self, wx.ID_ANY, "VaR Backtests (Portfolio, 95% HS rolling)")
            title_bt.SetFont(fontbold)

            kup_lab = wx.StaticText(self, -1, "Kupiec LR (Unconditional Coverage):")
            dur_lab = wx.StaticText(self, -1, "Duration (Time-between-violations):")

            def _get(res, keys):
                if not isinstance(res, dict):
                    return None
                lower = {str(k).lower().replace(" ", "").replace("-", ""): k for k in res}
                for k in keys:
                    kk = k.lower().replace(" ", "").replace("-", "")
                    if kk in lower:
                        return res[lower[kk]]
                return None

            def _num(x):
                try:
                    import numpy as _np
                    if isinstance(x, _np.ndarray):
                        x = x.ravel()[0]
                except Exception:
                    pass
                if isinstance(x, (list, tuple)) and x:
                    x = x[0]
                try:
                    return float(x)
                except Exception:
                    return None

            def _chi2_pvalue(stat, df=1):
                try:
                    import scipy.stats as _st
                    return 1.0 - _st.chi2.cdf(stat, df)
                except Exception:
                    return None

            kup_text = "Backtest unavailable (install vartests and/or increase sample size)."
            dur_text = "Backtest unavailable (install vartests and/or increase sample size)."

            if vt is not None and len(violations) >= 20:
                try:
                    kup_res = vt.kupiec_test(violations, var_conf_level=1 - alpha_bt, conf_level=0.95)
                    dur_res = vt.duration_test(violations, conf_level=0.95)

                    kup_stat = _num(_get(kup_res, ["lr_uc", "LR", "stat", "log-likelihood ratio test statistic"]))
                    kup_p    = _num(_get(kup_res, ["p_value", "p", "pval"]))
                    if kup_p is None and kup_stat is not None:
                        kup_p = _chi2_pvalue(kup_stat, df=1)
                    kup_dec  = _get(kup_res, ["reject", "decision", "result"])

                    kup_text = (f"LR={kup_stat:.3f}, p={kup_p:.3f}, reject={bool(kup_dec)}"
                                if (kup_stat is not None and kup_p is not None and kup_dec is not None)
                                else str(kup_res))

                    dur_stat = _num(_get(dur_res, ["log-likelihood ratio test statistic", "stat", "LR"]))
                    dur_p    = _num(_get(dur_res, ["p_value", "p", "pval"]))
                    if dur_p is None and dur_stat is not None:
                        dur_p = _chi2_pvalue(dur_stat, df=1)
                    dur_dec  = _get(dur_res, ["reject", "decision", "result"])

                    dur_text = (f"LR={dur_stat:.3f}, p={dur_p:.3f}, reject={bool(dur_dec)}"
                                if (dur_stat is not None and dur_p is not None and dur_dec is not None)
                                else str(dur_res))
                except Exception as _e:
                    kup_text = f"Backtest error: {type(_e).__name__}: {_e}"
                    dur_text = "Duration test not computed due to error above."

            kup_val = wx.StaticText(self, -1, kup_text, style=wx.ST_NO_AUTORESIZE)
            dur_val = wx.StaticText(self, -1, dur_text, style=wx.ST_NO_AUTORESIZE)

            wrap_w = 460
            for w in (kup_val, dur_val):
                w.SetMinSize((wrap_w, -1))
                w.Wrap(wrap_w)

            # =====================================================================
            #                              LAYOUT
            # =====================================================================
            root  = wx.BoxSizer(wx.HORIZONTAL)
            left  = wx.GridBagSizer(8, 10)
            right = wx.GridBagSizer(8, 10)

            # (Optional) allow both directions to be flexible; do NOT call AddGrowableCol
            left.SetFlexibleDirection(wx.BOTH)
            right.SetFlexibleDirection(wx.BOTH)

            # Small helper to safely add rows without manual row math
            def add_pair(gbs, r, label, value, label_flag=0, value_flag=wx.EXPAND):
                gbs.Add(label, (r, 0), flag=label_flag)
                gbs.Add(value, (r, 1), flag=value_flag)
                return r + 1  # next row

            # ---------------- LEFT COLUMN ----------------
            r = 0
            left.Add(title_historical, (r, 0), span=(1, 2)); r += 1

            # VaR 95 (Historical)
            r = add_pair(left, r, stock_a_hist_var95_lab, stock_a_hist_var95)
            r = add_pair(left, r, stock_b_hist_var95_lab, stock_b_hist_var95)
            r = add_pair(left, r, stock_c_hist_var95_lab, stock_c_hist_var95)
            r = add_pair(left, r, stock_d_hist_var95_lab, stock_d_hist_var95)
            r = add_pair(left, r, portfolio_hist_var95_lab, portfolio_hist_var95)

            #r += 1  # spacer

            # VaR 99 (Historical)
            r = add_pair(left, r, stock_a_hist_var99_lab, stock_a_hist_var99)
            r = add_pair(left, r, stock_b_hist_var99_lab, stock_b_hist_var99)
            r = add_pair(left, r, stock_c_hist_var99_lab, stock_c_hist_var99)
            r = add_pair(left, r, stock_d_hist_var99_lab, stock_d_hist_var99)
            r = add_pair(left, r, portfolio_hist_var99_lab, portfolio_hist_var99)

            #r += 1  # spacer

            # ES 95 (Historical)
            r = add_pair(left, r, stock_a_hist_es95_lab, stock_a_hist_es95)
            r = add_pair(left, r, stock_b_hist_es95_lab, stock_b_hist_es95)
            r = add_pair(left, r, stock_c_hist_es95_lab, stock_c_hist_es95)
            r = add_pair(left, r, stock_d_hist_es95_lab, stock_d_hist_es95)
            r = add_pair(left, r, portfolio_hist_es95_lab, portfolio_hist_es95)

            r += 1  # spacer

            # # ES 99 (Historical)
            # r = add_pair(left, r, stock_a_hist_es99_lab, stock_a_hist_es99)
            # r = add_pair(left, r, stock_b_hist_es99_lab, stock_b_hist_es99)
            # r = add_pair(left, r, stock_c_hist_es99_lab, stock_c_hist_es99)
            # r = add_pair(left, r, stock_d_hist_es99_lab, stock_d_hist_es99)
            # r = add_pair(left, r, portfolio_hist_es99_lab, portfolio_hist_es99)

            #r += 1
            left.Add(title_varcov, (r, 0), span=(1, 2)); r += 1

            # VaR 95 (Parametric)
            r = add_pair(left, r, stock_a_cov_var95_lab, stock_a_cov_var95)
            r = add_pair(left, r, stock_b_cov_var95_lab, stock_b_cov_var95)
            r = add_pair(left, r, stock_c_cov_var95_lab, stock_c_cov_var95)
            r = add_pair(left, r, stock_d_cov_var95_lab, stock_d_cov_var95)
            r = add_pair(left, r, portfolio_cov_var95_lab, portfolio_cov_var95)

            #r += 1  # spacer

            # VaR 99 (Parametric)
            r = add_pair(left, r, stock_a_cov_var99_lab, stock_a_cov_var99)
            r = add_pair(left, r, stock_b_cov_var99_lab, stock_b_cov_var99)
            r = add_pair(left, r, stock_c_cov_var99_lab, stock_c_cov_var99)
            r = add_pair(left, r, stock_d_cov_var99_lab, stock_d_cov_var99)
            r = add_pair(left, r, portfolio_cov_var99_lab, portfolio_cov_var99)

            #r += 1  # spacer

            # ES 95 (Parametric)
            r = add_pair(left, r, stock_a_cov_es95_lab, stock_a_cov_es95)
            r = add_pair(left, r, stock_b_cov_es95_lab, stock_b_cov_es95)
            r = add_pair(left, r, stock_c_cov_es95_lab, stock_c_cov_es95)
            r = add_pair(left, r, stock_d_cov_es95_lab, stock_d_cov_es95)
            r = add_pair(left, r, portfolio_cov_es95_lab, portfolio_cov_es95)

            #r += 1  # spacer

            # # ES 99 (Parametric)
            # r = add_pair(left, r, stock_a_cov_es99_lab, stock_a_cov_es99)
            # r = add_pair(left, r, stock_b_cov_es99_lab, stock_b_cov_es99)
            # r = add_pair(left, r, stock_c_cov_es99_lab, stock_c_cov_es99)
            # r = add_pair(left, r, stock_d_cov_es99_lab, stock_d_cov_es99)
            # r = add_pair(left, r, portfolio_cov_es99_lab, portfolio_cov_es99)

            # ---------------- RIGHT COLUMN ----------------
            rr = 0
            right.Add(title_MC, (rr, 0), span=(1, 2)); rr += 1

            # MC VaR 95
            rr = add_pair(right, rr, stock_a_MC_var95_lab, stock_a_MC_var95)
            rr = add_pair(right, rr, stock_b_MC_var95_lab, stock_b_MC_var95)
            rr = add_pair(right, rr, stock_c_MC_var95_lab, stock_c_MC_var95)
            rr = add_pair(right, rr, stock_d_MC_var95_lab, stock_d_MC_var95)

            rr += 1  # spacer

            # MC VaR 99
            rr = add_pair(right, rr, stock_a_MC_var99_lab, stock_a_MC_var99)
            rr = add_pair(right, rr, stock_b_MC_var99_lab, stock_b_MC_var99)
            rr = add_pair(right, rr, stock_c_MC_var99_lab, stock_c_MC_var99)
            rr = add_pair(right, rr, stock_d_MC_var99_lab, stock_d_MC_var99)

            rr += 1  # spacer

            # MC ES 95
            rr = add_pair(right, rr, stock_a_MC_es95_lab, stock_a_MC_es95)
            rr = add_pair(right, rr, stock_b_MC_es95_lab, stock_b_MC_es95)
            rr = add_pair(right, rr, stock_c_MC_es95_lab, stock_c_MC_es95)
            rr = add_pair(right, rr, stock_d_MC_es95_lab, stock_d_MC_es95)

            rr += 1  # spacer

            # # MC ES 99
            # rr = add_pair(right, rr, stock_a_MC_es99_lab, stock_a_MC_es99)
            # rr = add_pair(right, rr, stock_b_MC_es99_lab, stock_b_MC_es99)
            # rr = add_pair(right, rr, stock_c_MC_es99_lab, stock_c_MC_es99)
            # rr = add_pair(right, rr, stock_d_MC_es99_lab, stock_d_MC_es99)

            # rr += 1
            right.Add(title_bt, (rr, 0), span=(1, 2)); rr += 1

            # Keep backtests wrapped inside the tab
            wrap_w = 460
            kup_val.SetMinSize((wrap_w, -1)); kup_val.Wrap(wrap_w)
            dur_val.SetMinSize((wrap_w, -1)); dur_val.Wrap(wrap_w)

            rr = add_pair(right, rr, kup_lab, kup_val, label_flag=wx.ALIGN_TOP)
            rr = add_pair(right, rr, dur_lab, dur_val, label_flag=wx.ALIGN_TOP)
            

            # Pack: give right a bit more weight so backtests have room
            root.Add(left,  1, wx.ALL | wx.EXPAND, 8)
            root.Add(right, 2, wx.ALL | wx.EXPAND, 8)

            self.border = wx.BoxSizer()
            self.border.Add(root, 1, wx.ALL | wx.EXPAND, 5)
            self.SetSizerAndFit(self.border)


        except Exception as e:
            import traceback
            # hard reset on error
            try:
                for child in self.GetChildren():
                    try: child.Destroy()
                    except: pass
                self.SetSizer(None)
            except:
                pass
            err = wx.StaticText(self, -1, f"VAR tab error: {e}")
            s = wx.BoxSizer(wx.VERTICAL); s.Add(err, 0, wx.ALL, 8)
            self.SetSizerAndFit(s)
            print("PageThree exception:\n", traceback.format_exc())

# Fourth tab

class PageFour(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        pub.subscribe(self.myListener, "panelListener")
        self.SetBackgroundColour(self.GetParent().GetBackgroundColour())
        
    def myListener(self, arg1, arg2, arg3, arg4):
        try:
            # ------------------------------
            # Inputs
            # ------------------------------
            data_4 = arg1
            portfolio_df = arg4

            # ------------------------------
            # Clean returns
            # ------------------------------
            returns = (
                data_4.pct_change()
                      .replace([np.inf, -np.inf], np.nan)
                      .dropna()
            )

            if returns.empty:
                msg = wx.StaticText(self, -1, "Not enough synchronized data to build a correlation matrix.")
                sizer = wx.BoxSizer(wx.VERTICAL)
                sizer.Add(msg, 0, wx.ALL, 15)
                self.SetSizerAndFit(sizer)
                return

            # ------------------------------
            # Correlation Matrix (with values)
            # ------------------------------
            fig = Figure(figsize=(6, 4))
            canvas = FigureCanvas(self, -1, fig)
            ax = fig.add_subplot(111)

            corr = returns.corr()
            im = ax.imshow(corr.values, cmap="RdPu", vmin=-1, vmax=1)

            n = len(corr.columns)
            ax.set_xticks(range(n))
            ax.set_yticks(range(n))
            ax.set_xticklabels(corr.columns, rotation=45, ha="right")
            ax.set_yticklabels(corr.columns)

            # Add correlation values inside cells
            for i in range(n):
                for j in range(n):
                    ax.text(
                        j, i,
                        f"{corr.values[i, j]:.2f}",
                        ha="center",
                        va="center",
                        color="white"
                    )

            ax.set_title("Asset Return Correlation Matrix")
            fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
            fig.tight_layout()

            # ------------------------------
            # Standardised ES (Portfolio, 95%)
            # ------------------------------
            port_col = (
                "returns" if "returns" in portfolio_df.columns
                else "Portfolio" if "Portfolio" in portfolio_df.columns
                else None
            )

            if port_col is not None:
                port_ret = (
                    portfolio_df[port_col]
                    .replace([np.inf, -np.inf], np.nan)
                    .dropna()
                )

                if not port_ret.empty:
                    alpha = 0.05
                    var_95 = port_ret.quantile(alpha)
                    es_95 = port_ret[port_ret <= var_95].mean()
                    sigma = port_ret.std()

                    std_es = es_95 / sigma if sigma != 0 else np.nan

                    es_text = (
                        f"Portfolio ES (95%) = {es_95 * 100:.2f}%\n"
                        f"Daily Volatility = {sigma * 100:.2f}%\n"
                        f"Standardised ES (ES / σ) = {std_es:.2f}"
                    )
                else:
                    es_text = "Standardised ES unavailable (insufficient portfolio data)."
            else:
                es_text = "Standardised ES unavailable (portfolio returns missing)."

            es_label = wx.StaticText(self, -1, es_text)
            es_label.Wrap(450)

            # ------------------------------
            # Layout
            # ------------------------------
            root = wx.BoxSizer(wx.VERTICAL)
            root.Add(canvas, 1, wx.ALL | wx.EXPAND, 10)
            root.Add(es_label, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 15)

            self.SetSizerAndFit(root)

        except Exception as e:
            err = wx.StaticText(self, -1, f"Correlation tab error: {e}")
            sizer = wx.BoxSizer(wx.VERTICAL)
            sizer.Add(err, 0, wx.ALL, 15)
            self.SetSizerAndFit(sizer)
            
# ----- Fifth tab: PnL -----
class PagePnL(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        pub.subscribe(self.myListener, "panelListener")
        self.SetBackgroundColour(self.GetParent().GetBackgroundColour())

    def myListener(self, arg1, arg2, arg3, arg4):
        # clean any prior content
        for child in self.GetChildren():
            try:
                child.Destroy()
            except:
                pass

        # pick the portfolio returns column
        portfolio_df = arg4
        if "returns" in portfolio_df.columns:
            port_ret = portfolio_df["returns"].replace([np.inf, -np.inf], np.nan).dropna()
        elif "Portfolio" in portfolio_df.columns:
            port_ret = portfolio_df["Portfolio"].replace([np.inf, -np.inf], np.nan).dropna()
        else:
            msg = wx.StaticText(self, -1, "PnL: portfolio returns column not found.")
            s = wx.BoxSizer(wx.VERTICAL); s.Add(msg, 0, wx.ALL, 8)
            self.SetSizerAndFit(s); return

        if port_ret.empty:
            msg = wx.StaticText(self, -1, "PnL: not enough data to plot.")
            s = wx.BoxSizer(wx.VERTICAL); s.Add(msg, 0, wx.ALL, 8)
            self.SetSizerAndFit(s); return

        # ---------- basic stats (daily) ----------
        mu      = port_ret.mean()
        sig     = port_ret.std()
        ann_mu  = mu * 252.0
        ann_sig = sig * (252.0 ** 0.5)

        # ---------- tail risk: VaR & ES (left-tail) ----------
        var95 = port_ret.quantile(0.05)
        var99 = port_ret.quantile(0.01)
        es95  = port_ret[port_ret <= var95].mean() if not port_ret[port_ret <= var95].empty else np.nan
        es99  = port_ret[port_ret <= var99].mean() if not port_ret[port_ret <= var99].empty else np.nan

        # ---------- figure ----------
        fig = Figure(figsize=(7.8, 3.5))
        canvas = FigureCanvas(self, -1, fig)
        ax1 = fig.add_subplot(1, 2, 1)
        ax2 = fig.add_subplot(1, 2, 2)

        # RdPu color palette
        hist_color = plt.cm.RdPu(0.45)
        mean_color = plt.cm.RdPu(0.75)
        var95_color = plt.cm.RdPu(0.90)
        var99_color = plt.cm.RdPu(0.60)
        line_color = plt.cm.RdPu(0.80)

        # ---------- histogram of daily returns ----------
        ax1.hist(
            (port_ret * 100.0).values,
            bins=50,
            histtype="stepfilled",
            alpha=0.65,
            color=hist_color,
            edgecolor=plt.cm.RdPu(0.85)
        )
        ax1.set_title("Portfolio Daily PnL (%)")
        ax1.set_xlabel("Daily return (%)")
        ax1.set_ylabel("Frequency")

        ymax = ax1.get_ylim()[1]

        # mean line
        ax1.axvline(mu * 100.0, linestyle="--", linewidth=1.8, color=mean_color)
        ax1.text(mu * 100.0, ymax * 0.92, f"Mean = {mu*100:.2f}%", rotation=90, va="top")

        # VaR 95
        ax1.axvline(var95 * 100.0, linestyle=":", linewidth=2.0, color=var95_color)
        ax1.text(var95 * 100.0, ymax * 0.84, f"VaR 95% = {var95*100:.2f}%", rotation=90, va="top")

        # VaR 99
        ax1.axvline(var99 * 100.0, linestyle="-.", linewidth=1.8, color=var99_color)
        ax1.text(var99 * 100.0, ymax * 0.76, f"VaR 99% = {var99*100:.2f}%", rotation=90, va="top")

        # ---------- cumulative PnL ----------
        cum = (1.0 + port_ret).cumprod()
        ax2.plot(cum.index, cum.values, linewidth=2.2, color=line_color)
        ax2.set_title("Portfolio Cumulative PnL (Indexed)")
        ax2.set_xlabel("Date")
        ax2.set_ylabel("Index level")

        fig.tight_layout()

        # ---------- stats text ----------
        stats = (
            f"Daily mean = {mu*100:.2f}% | Daily std = {sig*100:.2f}%\n"
            f"Annualized mean ≈ {ann_mu*100:.2f}% | Annualized std ≈ {ann_sig*100:.2f}%\n"
            f"Historical VaR (95%) = {var95*100:.2f}% | ES (95%) = {es95*100:.2f}%\n"
        )
        stats_lbl = wx.StaticText(self, -1, stats, style=wx.ST_NO_AUTORESIZE)
        stats_lbl.SetMinSize((720, -1))
        stats_lbl.Wrap(720)

        # ---------- layout ----------
        col = wx.BoxSizer(wx.VERTICAL)
        col.Add(canvas,    1, wx.ALL | wx.EXPAND, 8)
        col.Add(stats_lbl, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        self.SetSizerAndFit(col)



# MainFrame
class MainFrame(wx.Frame):
    def __init__(self, bg_color):
        super().__init__(None, title="VaR Portfolio Tool")

        self.bg_color = bg_color
        self.SetBackgroundColour(self.bg_color)

        # Root panel
        p = wx.Panel(self)
        p.SetBackgroundColour(self.bg_color)

        # Notebook
        nb = wx.Notebook(p)
        nb.SetBackgroundColour(self.bg_color)

        # Pages
        page1 = PageOne(nb)
        page2 = PageTwo(nb)
        page3 = PageThree(nb)
        page4 = PageFour(nb)
        page5 = PagePnL(nb)

        nb.AddPage(page1, "Portfolio Data")
        nb.AddPage(page2, "Descriptive Data +")
        nb.AddPage(page3, "VAR")
        nb.AddPage(page4, "Correlation Matrix")
        nb.AddPage(page5, "PnL")

        # Layout
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(nb, 1, wx.EXPAND)
        p.SetSizer(sizer)

        self.Centre()


if __name__ == "__main__":
    app = wx.App(False)

    UI_BG_HEX = "#00175f"
    UI_BG_COLOR = wx.Colour(UI_BG_HEX)
    frame = MainFrame(UI_BG_COLOR)
    frame.SetSize(1200, 750)
    frame.Center()
    frame.Show()
    app.MainLoop()